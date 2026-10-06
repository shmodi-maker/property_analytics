# app/calculations/comparable_calculator.py

from typing import Optional

from app.config import COMPARABLE_WEIGHTS


class ComparableCalculator:

    @staticmethod
    def calculate_price_per_sqft(
        price: Optional[float],
        living_area: Optional[float],
    ) -> Optional[float]:

        if price is None or living_area is None or living_area <= 0:
            return None

        return float(price) / float(living_area)

    @staticmethod
    def similarity_score(
        subject: dict,
        comp: dict,
        radius_miles: float,
    ) -> float:

        scores = {}
        weights = {}

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        distance = comp.get("distance_miles")

        if distance is not None and radius_miles > 0:
            distance_score = max(
                0.0,
                1.0 - (float(distance) / float(radius_miles)),
            )

            scores["distance"] = distance_score
            weights["distance"] = COMPARABLE_WEIGHTS["distance"]


        subject_area = subject.get("living_area")
        comp_area = comp.get("living_area")

        if (
            subject_area is not None
            and comp_area is not None
            and float(subject_area) > 0
            and float(comp_area) > 0
        ):
            area_difference = abs(
                float(subject_area) - float(comp_area)
            )

            area_score = max(
                0.0,
                1.0 - (
                    area_difference
                    / max(float(subject_area), float(comp_area))
                ),
            )

            scores["living_area"] = area_score
            weights["living_area"] = COMPARABLE_WEIGHTS["living_area"]

        subject_beds = subject.get("bedrooms")
        comp_beds = comp.get("bedrooms")

        if (
            subject_beds is not None
            and comp_beds is not None
        ):
            bedroom_score = max(
                0.0,
                1.0 - (
                    abs(
                        float(subject_beds)
                        - float(comp_beds)
                    )
                    / max(float(subject_beds), 1.0)
                ),
            )

            scores["bedrooms"] = bedroom_score
            weights["bedrooms"] = COMPARABLE_WEIGHTS["bedrooms"]

        # ----------------------------------------------------
        # Bathrooms
        # ----------------------------------------------------

        subject_baths = subject.get("bathrooms")
        comp_baths = comp.get("bathrooms")

        if (
            subject_baths is not None
            and comp_baths is not None
        ):
            bathroom_score = max(
                0.0,
                1.0 - (
                    abs(
                        float(subject_baths)
                        - float(comp_baths)
                    )
                    / max(float(subject_baths), 1.0)
                ),
            )

            scores["bathrooms"] = bathroom_score
            weights["bathrooms"] = COMPARABLE_WEIGHTS["bathrooms"]

        subject_class = subject.get("property_class")
        comp_class = comp.get("property_class")

        if (
            subject_class is not None
            and comp_class is not None
        ):
            property_class_score = (
                1.0
                if subject_class == comp_class
                else 0.0
            )

            scores["property_class"] = property_class_score
            weights["property_class"] = COMPARABLE_WEIGHTS[
                "property_class"
            ]

        # ----------------------------------------------------
        # Weighted score
        #
        # Only use criteria where data exists.
        # This prevents NULL values from causing errors and
        # prevents missing data from automatically becoming 0.
        # ----------------------------------------------------

        if not weights:
            return 0.0

        total_weight = sum(weights.values())

        if total_weight <= 0:
            return 0.0

        weighted_score = sum(
            scores[key] * weights[key]
            for key in scores
        )

        return round(
            (weighted_score / total_weight) * 100,
            2,
        )

    @classmethod
    def prepare_comparable(
        cls,
        subject: dict,
        comp: dict,
        radius_miles: float,
    ) -> dict:

        comp = comp.copy()

        comp["price_per_sqft"] = (
            cls.calculate_price_per_sqft(
                comp.get("list_price"),
                comp.get("living_area"),
            )
        )

        comp["comparability_score"] = (
            cls.similarity_score(
                subject=subject,
                comp=comp,
                radius_miles=radius_miles,
            )
        )

        return comp

    @staticmethod
    def calculate_valuation(
        subject: dict,
        comparables: list[dict],
    ) -> dict:

        valid_comps = [
            comp
            for comp in comparables
            if comp.get("price_per_sqft") is not None
            and comp.get("comparability_score") is not None
        ]

        if not valid_comps:
            return {
                "estimated_low": None,
                "estimated_mid": None,
                "estimated_high": None,
                "weighted_price_per_sqft": None,
            }

        total_weight = sum(
            max(
                float(comp["comparability_score"]),
                1.0,
            )
            for comp in valid_comps
        )

        weighted_ppsf = sum(
            float(comp["price_per_sqft"])
            * max(
                float(comp["comparability_score"]),
                1.0,
            )
            for comp in valid_comps
        ) / total_weight

        subject_area = subject.get("living_area")

        if subject_area is None or float(subject_area) <= 0:
            return {
                "estimated_low": None,
                "estimated_mid": None,
                "estimated_high": None,
                "weighted_price_per_sqft": round(
                    weighted_ppsf,
                    2,
                ),
            }

        # ----------------------------------------------------
        # Price-per-square-foot distribution
        # ----------------------------------------------------

        ppsf_values = sorted(
            float(comp["price_per_sqft"])
            for comp in valid_comps
        )

        low_index = max(
            0,
            int(len(ppsf_values) * 0.25),
        )

        high_index = min(
            len(ppsf_values) - 1,
            int(len(ppsf_values) * 0.75),
        )

        low_ppsf = ppsf_values[low_index]
        high_ppsf = ppsf_values[high_index]

        estimated_low = float(subject_area) * low_ppsf
        estimated_mid = float(subject_area) * weighted_ppsf
        estimated_high = float(subject_area) * high_ppsf

        return {
            "estimated_low": round(
                estimated_low,
                2,
            ),
            "estimated_mid": round(
                estimated_mid,
                2,
            ),
            "estimated_high": round(
                estimated_high,
                2,
            ),
            "weighted_price_per_sqft": round(
                weighted_ppsf,
                2,
            ),
        }

    @staticmethod
    def compare_asking_price(
        asking_price: Optional[float],
        valuation: dict,
    ) -> dict:

        if asking_price is None:
            return {
                "asking_price": None,
                "position": None,
                "difference_from_mid": None,
                "difference_percent": None,
            }

        low = valuation.get("estimated_low")
        high = valuation.get("estimated_high")
        mid = valuation.get("estimated_mid")

        # ----------------------------------------------------
        # No valid valuation
        # ----------------------------------------------------

        if low is None or high is None or mid is None:
            return {
                "asking_price": float(asking_price),
                "position": None,
                "difference_from_mid": None,
                "difference_percent": None,
            }

        # ----------------------------------------------------
        # Position
        # ----------------------------------------------------

        if asking_price < low:
            position = "below_range"

        elif asking_price > high:
            position = "above_range"

        else:
            position = "within_range"

        # ----------------------------------------------------
        # Difference from midpoint
        # ----------------------------------------------------

        difference = float(asking_price) - float(mid)

        percentage = (
            (difference / float(mid)) * 100
            if mid != 0
            else None
        )

        return {
            "asking_price": float(asking_price),
            "position": position,
            "difference_from_mid": round(
                difference,
                2,
            ),
            "difference_percent": (
                round(percentage, 2)
                if percentage is not None
                else None
            ),
        }