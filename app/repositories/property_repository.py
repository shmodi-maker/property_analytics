from app.database import get_connection

class PropertyRepository:
    
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