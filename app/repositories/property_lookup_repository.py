from app.database import get_connection


class PropertyLookupRepository:

    def search_by_address(
        self,
        address: str,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
    ):
        query = """
            SELECT
                li.listing_key_numeric,
                li.unparsed_address,
                li.filtered_address,
                li.city,
                li.state_or_province,
                li.postal_code,
                
                link.property_identity_id,

                pi.normalized_address,
                pi.identity_source,
                pi.confidence,

                li.modification_timestamp,
                li.latitude,
                li.longitude,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM public.zipdata_idxlistingpriceevent active_event
                        WHERE active_event.property_identity_id =
                              link.property_identity_id
                          AND active_event.standard_status_at_event = 'Active'
                          AND active_event.price IS NOT NULL
                          AND active_event.price > 0
                    )
                    THEN TRUE
                    ELSE FALSE
                END AS has_active_listing,

                (
                    SELECT MAX(event_date)
                    FROM public.zipdata_idxlistingpriceevent latest_event
                    WHERE latest_event.property_identity_id =
                          link.property_identity_id
                ) AS latest_event_date

            FROM public.zipdata_idxlisting li

            LEFT JOIN public.zipdata_idxlistingidentitylink link
                ON link.listing_key_numeric = li.listing_key_numeric

            LEFT JOIN public.zipdata_idxpropertyidentity pi
                ON pi.id = link.property_identity_id

            WHERE (
                li.unparsed_address ILIKE %s
                OR li.filtered_address ILIKE %s
            )
        """

        params = [
            f"%{address}%",
            f"%{address}%",
        ]

        if city:
            query += """
                AND li.city ILIKE %s
            """
            params.append(city)

        if state:
            query += """
                AND li.state_or_province ILIKE %s
            """
            params.append(state)

        if postal_code:
            query += """
                AND li.postal_code = %s
            """
            params.append(postal_code)

        query += """
            ORDER BY
                has_active_listing DESC,
                latest_event_date DESC NULLS LAST,
                li.modification_timestamp DESC;
        """

        conn = get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [
                    {
                        "listing_key_numeric": row[0],
                        "unparsed_address": row[1],
                        "filtered_address": row[2],
                        "city": row[3],
                        "state_or_province": row[4],
                        "postal_code": row[5],
                        "property_identity_id": row[6],
                        "normalized_address": row[7],
                        "identity_source": row[8],
                        "confidence": row[9],
                        "modification_timestamp": row[10],
                        "latitude": float(row[11]) if row[11] is not None else None,
                        "longitude": float(row[12]) if row[12] is not None else None,
                        "has_active_listing": row[13],
                        "latest_event_date": row[14],
                    }
                    for row in rows
                ]
        finally:
            conn.close()