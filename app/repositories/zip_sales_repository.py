from app.database import get_connection


class ZipSalesRepository:

    def get_zip_sales(self, postal_code: str):
        query = """
            SELECT
                pe.property_identity_id,
                pe.listing_key_numeric,
                pe.event_type,
                pe.event_date,
                pe.price,
                pe.prior_price,
                pe.standard_status_at_event,
                pe.observed_at
            FROM public.zipdata_idxlistingpriceevent pe
            JOIN public.zipdata_idxpropertyidentity pi
                ON pi.id = pe.property_identity_id
            WHERE pi.postal_code = %s
              AND pe.event_type = 'sold'
              AND pe.price IS NOT NULL
              AND pe.price > 0
            ORDER BY
                pe.property_identity_id,
                pe.event_date ASC,
                pe.observed_at ASC;
        """

        conn = get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (postal_code,))
                rows = cursor.fetchall()

                return [
                    {
                        "property_identity_id": row[0],
                        "listing_key_numeric": row[1],
                        "event_type": row[2],
                        "event_date": row[3],
                        "price": float(row[4]),
                        "prior_price": float(row[5])
                        if row[5] is not None
                        else None,
                        "status": row[6],
                        "observed_at": row[7],
                    }
                    for row in rows
                ]

        finally:
            conn.close()