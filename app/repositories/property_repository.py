from app.database import get_connection


class PropertyRepository:

    # ==========================================================
    # COMPARABLE PROPERTIES
    # ==========================================================

    def get_nearby_active_properties(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float,
        property_class: str | None = None,
        exclude_listing_id: str | None = None,
    ):
        query = """
            WITH nearby_listings AS (
                SELECT
                    listing_id,
                    filtered_address,
                    city,
                    state_or_province,
                    postal_code,
                    list_price,
                    bedrooms_total,
                    bathrooms_total_integer,
                    living_area,
                    property_class,
                    latitude,
                    longitude,

                    (
                        3959 * 2 * ASIN(
                            SQRT(
                                POWER(
                                    SIN(
                                        RADIANS(
                                            latitude - %s
                                        ) / 2
                                    ),
                                    2
                                )
                                +
                                COS(RADIANS(%s))
                                * COS(RADIANS(latitude))
                                * POWER(
                                    SIN(
                                        RADIANS(
                                            longitude - %s
                                        ) / 2
                                    ),
                                    2
                                )
                            )
                        )
                    ) AS distance_miles

                FROM public.zipdata_idxlisting

                WHERE standard_status = 'Active'

                AND latitude IS NOT NULL
                AND longitude IS NOT NULL

                AND list_price IS NOT NULL

                AND living_area IS NOT NULL
                AND living_area > 0

                AND bedrooms_total IS NOT NULL
                AND bathrooms_total_integer IS NOT NULL

                AND (
                    %s IS NULL
                    OR property_class = %s
                )

                AND (
                    %s IS NULL
                    OR listing_id <> %s
                )
            )

            SELECT *
            FROM nearby_listings

            WHERE distance_miles <= %s

            ORDER BY distance_miles ASC;
        """

        params = (
            latitude,
            latitude,
            longitude,
            property_class,
            property_class,
            exclude_listing_id,
            exclude_listing_id,
            radius_miles,
        )

        conn = get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [
                    {
                        "listing_id": row[0],
                        "address": row[1],
                        "city": row[2],
                        "state": row[3],
                        "postal_code": row[4],
                        "list_price": (
                            float(row[5])
                            if row[5] is not None
                            else None
                        ),
                        "bedrooms": (
                            float(row[6])
                            if row[6] is not None
                            else None
                        ),
                        "bathrooms": (
                            float(row[7])
                            if row[7] is not None
                            else None
                        ),
                        "living_area": (
                            float(row[8])
                            if row[8] is not None
                            else None
                        ),
                        "property_class": row[9],
                        "latitude": float(row[10]),
                        "longitude": float(row[11]),
                        "distance_miles": float(row[12]),
                    }
                    for row in rows
                ]

        finally:
            conn.close()

    # ----------------------------------------------------------
    # Get property by MLS listing ID
    # ----------------------------------------------------------

    def get_property_by_id(self, property_id: str):

        query = """
            SELECT
                listing_id,
                filtered_address,
                city,
                state_or_province,
                postal_code,
                list_price,
                bedrooms_total,
                bathrooms_total_integer,
                living_area,
                property_class,
                latitude,
                longitude
            FROM public.zipdata_idxlisting
            WHERE listing_id = %s
            LIMIT 1;
        """

        conn = get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (property_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return {
                    "listing_id": row[0],
                    "address": row[1],
                    "city": row[2],
                    "state": row[3],
                    "postal_code": row[4],
                    "list_price": (
                        float(row[5])
                        if row[5] is not None
                        else None
                    ),
                    "bedrooms": (
                        float(row[6])
                        if row[6] is not None
                        else None
                    ),
                    "bathrooms": (
                        float(row[7])
                        if row[7] is not None
                        else None
                    ),
                    "living_area": (
                        float(row[8])
                        if row[8] is not None
                        else None
                    ),
                    "property_class": row[9],
                    "latitude": (
                        float(row[10])
                        if row[10] is not None
                        else None
                    ),
                    "longitude": (
                        float(row[11])
                        if row[11] is not None
                        else None
                    ),
                }

        finally:
            conn.close()

    # ==========================================================
    # PRICE PROJECTION
    # ==========================================================

    # ----------------------------------------------------------
    # Get current active listing
    # ----------------------------------------------------------

    def get_active_listing(self, property_identity_id: int):

        query = """
            SELECT
                pe.property_identity_id,
                pe.listing_key_numeric,
                pe.event_date,
                pe.price,
                pe.standard_status_at_event,
                li.is_lease_listing,
                li.list_price
            FROM public.zipdata_idxlistingpriceevent pe
            LEFT JOIN public.zipdata_idxlisting li
                ON li.listing_key_numeric = pe.listing_key_numeric
            WHERE pe.property_identity_id = %s
              AND pe.standard_status_at_event = 'Active'
              AND pe.price IS NOT NULL
            ORDER BY
                pe.event_date DESC,
                pe.observed_at DESC
            LIMIT 1;
        """

        conn = get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (property_identity_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return {
                    "property_identity_id": row[0],
                    "listing_key_numeric": row[1],
                    "event_date": row[2],
                    "price": (
                        float(row[3])
                        if row[3] is not None
                        else None
                    ),
                    "status": row[4],
                    "is_lease_listing": bool(row[5]),
                    "list_price": (
                        float(row[6])
                        if row[6] is not None
                        else None
                    ),
                }

        finally:
            conn.close()

    # ----------------------------------------------------------
    # Get property identity by ID
    # ----------------------------------------------------------

    def get_property_identity(self, property_identity_id: int):

        query = """
            SELECT
                id,
                identity_key,
                normalized_address,
                postal_code,
                city,
                state_or_province
            FROM public.zipdata_idxpropertyidentity
            WHERE id = %s
            LIMIT 1;
        """

        conn = get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (property_identity_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return {
                    "id": row[0],
                    "identity_key": row[1],
                    "normalized_address": row[2],
                    "postal_code": row[3],
                    "city": row[4],
                    "state_or_province": row[5],
                }

        finally:
            conn.close()

    # ----------------------------------------------------------
    # Get property identity using listing key
    # ----------------------------------------------------------

    def get_property_identity_by_listing_key(
        self,
        listing_key: str,
    ):
        query = """
            SELECT
                pe.property_identity_id,
                pe.listing_key_numeric,
                pe.event_date,
                pe.observed_at
            FROM public.zipdata_idxlistingpriceevent pe
            WHERE pe.listing_key_numeric = %s
            ORDER BY
                pe.event_date DESC,
                pe.observed_at DESC
            LIMIT 1;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (listing_key,))
                row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "listing_key_numeric": row[1],
            "event_date": row[2],
            "observed_at": row[3],
        }