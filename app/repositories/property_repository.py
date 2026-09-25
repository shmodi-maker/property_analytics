from app.database import get_connection


class PropertyRepository:

    def get_active_listing(self, property_identity_id: int):
        query = """
            SELECT
                pe.property_identity_id,
                pe.listing_key_numeric,
                pe.event_date,
                pe.price,
                pe.standard_status_at_event
            FROM public.zipdata_idxlistingpriceevent pe
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
                    "price": float(row[3]),
                    "status": row[4],
                }

        finally:
            conn.close()

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