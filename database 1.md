# ZipData MLS / IDX — Database Schema Reference

PostgreSQL tables owned by the Django `zipdata` app for **MLSListings IDX** (RESO / OData).

| | |
|---|---|
| **DDL (CREATE TABLE)** | [`mls_idx_schema.sql`](mls_idx_schema.sql) |
| **Django models** | `backend/zipdata_proj/zipdata/models/property.py`, `idx_agent.py`, `idx_price_history.py` |
| **Ingest** | `backend/zipdata_proj/zipdata/services/idx_ingest.py` |
| **Feed** | MLSListings IDX Web API (`Property`, `Media`, `Member`, `Office`, `OpenHouse`, aux entities) |

This document is for the **Principal Agent / India team** so MLS data can be queried or mirrored correctly.

---

## How MLS data is stored (critical)

```
MLSListings OData
       │
       ▼
┌──────────────────────┐     full JSON (no field loss)
│  *Raw tables         │◄──── payload JSONB
│  idxlistingraw, etc. │
└──────────┬───────────┘
           │ upsert / normalize
           ▼
┌──────────────────────┐     denormalized columns for search/map
│  Normalized tables   │◄──── + source_payload JSONB (same full Property row)
│  idxlisting, media…  │
└──────────────────────┘
```

1. **Raw tables** (`zipdata_idx*raw`) store every OData field in `payload` JSONB.
2. **Normalized tables** expose the columns ZipData APIs filter/sort on.
3. For Property listings, the **entire** RESO row is also copied to `zipdata_idxlisting.source_payload` — there is no field loss on Property.

**Primary cross-entity key:** `listing_key_numeric` (= RESO `ListingKeyNumeric`).

**JSON key style:** PascalCase RESO names inside JSONB (`ListPrice`, `StandardStatus`, `YearBuilt`, …).

---

## Table inventory

| Django model | PostgreSQL table | Role |
|---|---|---|
| `IdxSyncCursor` | `zipdata_idxsynccursor` | Incremental ingest high-water marks |
| `IdxListingRaw` | `zipdata_idxlistingraw` | Raw Property OData |
| `IdxListing` | `zipdata_idxlisting` | Normalized listing + `source_payload` |
| `IdxAddressGeocode` | `zipdata_idxaddressgeocode` | Nominatim address → lat/lng cache |
| `IdxMediaRaw` | `zipdata_idxmediaraw` | Raw Media OData |
| `IdxMedia` | `zipdata_idxmedia` | Hosted media URLs for APIs |
| `IdxMemberRaw` | `zipdata_idxmemberraw` | Raw Member OData |
| `IdxOfficeRaw` | `zipdata_idxofficeraw` | Raw Office OData |
| `IdxOpenHouseRaw` | `zipdata_idxopenhouseraw` | Raw OpenHouse OData |
| `IdxFeedEntityRaw` | `zipdata_idxfeedentityraw` | Aux entity sets (e.g. PropertyUnit) |
| `IdxOffice` | `zipdata_idxoffice` | Normalized office (agent map) |
| `IdxMember` | `zipdata_idxmember` | Normalized member (agent map) |
| `IdxPropertyIdentity` | `zipdata_idxpropertyidentity` | Canonical property id (relists) |
| `IdxListingIdentityLink` | `zipdata_idxlistingidentitylink` | Listing → property identity |
| `IdxListingPriceEvent` | `zipdata_idxlistingpriceevent` | Append-only price/status events |

---

## 1. `zipdata_idxlisting` (normalized Property — primary for agents)

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | `BIGSERIAL` | No | PK |
| `listing_key_numeric` | `VARCHAR(128)` | No | Unique RESO key |
| `listing_id` | `VARCHAR(128)` | Yes | Public MLS listing id |
| `source_system` | `VARCHAR(64)` | Yes | Feed source system |
| `standard_status` | `VARCHAR(64)` | Yes | Active / Pending / Closed / … |
| `modification_timestamp` | `TIMESTAMPTZ` | Yes | RESO ModificationTimestamp |
| `internet_list` | `BOOLEAN` | No | IDX internet-listable flag (compliance) |
| `is_lease_listing` | `BOOLEAN` | No | Denormalized lease heuristic |
| `property_class` | `VARCHAR(32)` | No | Denormalized dwelling class (SFH, condo, …) |
| `filtered_address` | `VARCHAR(512)` | Yes | Display address (compliance-filtered) |
| `unparsed_address` | `VARCHAR(512)` | Yes | Unparsed address |
| `city` | `VARCHAR(128)` | Yes | |
| `state_or_province` | `VARCHAR(32)` | Yes | |
| `postal_code` | `VARCHAR(16)` | Yes | ZIP |
| `list_price` | `NUMERIC(14,2)` | Yes | |
| `bedrooms_total` | `NUMERIC(8,2)` | Yes | |
| `bathrooms_total_integer` | `NUMERIC(8,2)` | Yes | |
| `living_area` | `NUMERIC(14,2)` | Yes | Sq ft |
| `listing_office_name` | `VARCHAR(255)` | Yes | Attribution |
| `listing_member_name` | `VARCHAR(255)` | Yes | |
| `listing_member_email` | `VARCHAR(255)` | Yes | |
| `listing_member_phone` | `VARCHAR(64)` | Yes | |
| `listing_member_key_numeric` | `VARCHAR(128)` | Yes | → Member |
| `listing_office_key_numeric` | `VARCHAR(128)` | Yes | → Office |
| `attribution_required` | `BOOLEAN` | No | |
| `data_source_name` | `VARCHAR(255)` | No | Default `MLSListings` |
| `source_payload` | `JSONB` | Yes | **Full Property OData row** |
| `latitude` / `longitude` | `NUMERIC(11,7)` | Yes | Map coords |
| `created_at` / `updated_at` | `TIMESTAMPTZ` | No | |

### Example: read a rich RESO field

```sql
SELECT
  listing_key_numeric,
  list_price,
  standard_status,
  source_payload->>'YearBuilt'        AS year_built,
  source_payload->>'LotSizeAcres'     AS lot_acres,
  source_payload->>'PublicRemarks'    AS remarks,
  source_payload->>'PropertyType'     AS property_type
FROM zipdata_idxlisting
WHERE postal_code = '90210'
  AND internet_list = TRUE
  AND standard_status = 'Active';
```

---

## 2. `zipdata_idxlistingraw`

| Column | Type | Description |
|---|---|---|
| `listing_key_numeric` | `VARCHAR(128)` UNIQUE | |
| `listing_id` | `VARCHAR(128)` | |
| `modification_timestamp` | `TIMESTAMPTZ` | |
| `standard_status` | `VARCHAR(64)` | |
| `payload` | `JSONB` NOT NULL | Full OData Property row |
| `payload_crc` | `VARCHAR(64)` | Change detection |
| `ingested_at` | `TIMESTAMPTZ` | Last ingest write |

Mirror of Property for audit / re-normalize. Prefer `zipdata_idxlisting` for agent queries.

---

## 3. Media

### `zipdata_idxmediaraw`

Full Media OData in `payload` (includes vendor `MediaURL`). After ingest, `media_url` is rewritten to ZipData hosting.

### `zipdata_idxmedia`

| Column | Description |
|---|---|
| `listing_id` | FK → `zipdata_idxlisting.id` (CASCADE) |
| `media_key_numeric` | Unique media key |
| `media_url` | **Hosted** HTTPS (S3/CloudFront) or `/media/` — never MLS CDN in APIs |
| `media_category` / `order` / `permission` | RESO media metadata |
| `media_caption` / `image_of` / `media_type` | Optional RESO caption fields |
| `is_public_allowed` | Compliance visibility |

---

## 4. Member / Office / OpenHouse (raw)

| Table | Unique key | JSONB |
|---|---|---|
| `zipdata_idxmemberraw` | `member_key_numeric` | `payload` |
| `zipdata_idxofficeraw` | `office_key_numeric` | `payload` |
| `zipdata_idxopenhouseraw` | `open_house_key_numeric` (+ `listing_key_numeric`) | `payload` |

---

## 5. Auxiliary entities — `zipdata_idxfeedentityraw`

Rows from OData entity sets discovered in `/$metadata` (e.g. `PropertyUnit`) that are not Media/OpenHouse.

| Column | Description |
|---|---|
| `listing_key_numeric` | Parent listing |
| `entity_set` | Entity set name |
| `record_key` | Row identity within set |
| `payload` | Full OData row |

Unique on `(listing_key_numeric, entity_set, record_key)`.

---

## 6. Normalized agent map — `zipdata_idxoffice` / `zipdata_idxmember`

Public “Find an Agent” serving tables. Full office/member JSON may also live in `source_payload`. Eligibility flags: `is_public_map_eligible`, `is_active_in_feed`, member `is_solo_map_pin`.

Join listings → agents:

```sql
SELECT l.listing_key_numeric, l.list_price, m.member_full_name, m.dre_license
FROM zipdata_idxlisting l
LEFT JOIN zipdata_idxmember m
  ON m.member_key_numeric = l.listing_member_key_numeric
WHERE l.listing_key_numeric = '123456789';
```

---

## 7. Price history

```
zipdata_idxpropertyidentity
        ▲
        │ FK
zipdata_idxlistingidentitylink   (listing_key_numeric → identity)
        │
zipdata_idxlistingpriceevent     (append-only events)
```

`event_type`: `listed_for_sale` | `price_change` | `sold` | `listing_removed` | `relisted` | `pending`  
`visibility`: `public` | `vow` | `internal`

---

## 8. Sync — `zipdata_idxsynccursor`

One row per ingest `resource` with `last_modified_at` / `last_listing_key` high-water marks.

---

## Entity relationship (simplified)

```
idxsynccursor
idxlistingraw ──(key)──► idxlisting ◄── idxmedia
                              │
                              ├── listing_member_key_numeric → idxmember
                              ├── listing_office_key_numeric → idxoffice
                              ├── idxopenhouseraw (by listing_key)
                              ├── idxfeedentityraw (by listing_key)
                              └── idxlistingidentitylink → idxpropertyidentity
                                                              ▲
                                              idxlistingpriceevent
idxmemberraw / idxofficeraw / idxmediaraw / idxaddressgeocode
```

---

## Principal Agent guidance

1. **Prefer** `zipdata_idxlisting` + JSONB `source_payload` for listing facts.
2. **Filter** consumer-facing sets with `internet_list = TRUE` and allowed `standard_status`.
3. **Photos:** use `zipdata_idxmedia` where `is_public_allowed`; do not hotlink MLS CDN URLs.
4. **Do not invent columns** for RESO fields — read them from JSONB.
5. DDL in [`mls_idx_schema.sql`](mls_idx_schema.sql) is a mirror of Django; ZipData prod is migrated via Django, not this SQL.

---

Auth/compliance rules for anonymous vs authenticated callers live in `idx_listing_filters` / IDX views — DB rows may exist that must not be shown publicly.
