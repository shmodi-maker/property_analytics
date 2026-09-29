# app/calculations/comparable_calculator.py

from typing import Optional

from app.config import COMPARABLE_WEIGHTS


class ComparableCalculator:

    @staticmethod
    def calculate_price_per_sqft(
        price: Optional[float],
        living_area: Optional[float],
    ) -> Optional[float]:

        if not price or not living_area or living_area <= 0:
            return None

        return float(price) / float(living_area)

    @staticmethod
    def similarity_score(
        subject: dict,
        comp: dict,
        radius_miles: float,
    ) -> float:

        scores = {}

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        distance = comp.get("distance_miles")

        if distance is not None and radius_miles > 0:
            distance_score = max(
                0.0,
                1.0 - (distance / radius_miles)
            )
        else:
            distance_score = 0.0

        scores["distance"] = distance_score

        # ----------------------------------------------------
        # Living area
        # ----------------------------------------------------

        subject_area = subject.get("living_area")
        comp_area = comp.get("living_area")

        if subject_area and comp_area:
            area_difference = abs(
                subject_area - comp_area
            )

            area_score = max(
                0.0,
                1.0 - (
                    area_difference
                    / max(subject_area, comp_area)
                )
            )
        else:
            area_score = 0.0

        scores["living_area"] = area_score

        # ----------------------------------------------------
        # Bedrooms
        # ----------------------------------------------------

        subject_beds = subject.get("bedrooms")
        comp_beds = comp.get("bedrooms")

        if subject_beds is not None and comp_beds is not None:
            bedroom_score = max(
                0.0,
                1.0 - (
                    abs(subject_beds - comp_beds)
                    / max(float(subject_beds), 1.0)
                )
            )
        else:
            bedroom_score = 0.0

        scores["bedrooms"] = bedroom_score

        # ----------------------------------------------------
        # Bathrooms
        # ----------------------------------------------------

        subject_baths = subject.get("bathrooms")
        comp_baths = comp.get("bathrooms")

        if subject_baths is not None and comp_baths is not None:
            bathroom_score = max(
                0.0,
                1.0 - (
                    abs(subject_baths - comp_baths)
                    / max(float(subject_baths), 1.0)
                )
            )
        else:
            bathroom_score = 0.0

        scores["bathrooms"] = bathroom_score

        # ----------------------------------------------------
        # Property class
        # ----------------------------------------------------

        if (
            subject.get("property_class")
            and comp.get("property_class")
        ):
            property_class_score = (
                1.0
                if subject["property_class"]
                == comp["property_class"]
                else 0.0
            )
        else:
            property_class_score = 0.0

        scores["property_class"] = property_class_score

        # ----------------------------------------------------
        # Weighted score
        # ----------------------------------------------------

        total_score = sum(
            scores[key] * COMPARABLE_WEIGHTS[key]
            for key in COMPARABLE_WEIGHTS
        )

        return round(total_score * 100, 2)

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
                subject,
                comp,
                radius_miles,
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
        ]

        if not valid_comps:
            return {
                "estimated_low": None,
                "estimated_mid": None,
                "estimated_high": None,
                "weighted_price_per_sqft": None,
            }

        total_weight = sum(
            max(comp["comparability_score"], 1.0)
            for comp in valid_comps
        )

        weighted_ppsf = sum(
            comp["price_per_sqft"]
            * max(comp["comparability_score"], 1.0)
            for comp in valid_comps
        ) / total_weight

        subject_area = subject.get("living_area")

        if not subject_area:
            return {
                "estimated_low": None,
                "estimated_mid": None,
                "estimated_high": None,
                "weighted_price_per_sqft": round(
                    weighted_ppsf,
                    2,
                ),
            }

        # Use the distribution of comparable $/sqft
        # to create the initial valuation range.

        ppsf_values = sorted(
            comp["price_per_sqft"]
            for comp in valid_comps
        )

        low_ppsf = ppsf_values[
            max(0, int(len(ppsf_values) * 0.25))
        ]

        high_ppsf = ppsf_values[
            min(
                len(ppsf_values) - 1,
                int(len(ppsf_values) * 0.75),
            )
        ]

        estimated_low = subject_area * low_ppsf
        estimated_mid = subject_area * weighted_ppsf
        estimated_high = subject_area * high_ppsf

        return {
            "estimated_low": round(estimated_low, 2),
            "estimated_mid": round(estimated_mid, 2),
            "estimated_high": round(estimated_high, 2),
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

        if not asking_price:
            return {
                "asking_price": None,
                "position": None,
                "difference_from_mid": None,
                "difference_percent": None,
            }

        low = valuation.get("estimated_low")
        high = valuation.get("estimated_high")
        mid = valuation.get("estimated_mid")

        if low is None or high is None or mid is None:
            position = None
        elif asking_price < low:
            position = "below_range"
        elif asking_price > high:
            position = "above_range"
        else:
            position = "within_range"

        difference = asking_price - mid

        percentage = (
            (difference / mid) * 100
            if mid
            else None
        )

        return {
            "asking_price": asking_price,
            "position": position,
            "difference_from_mid": round(
                difference,
                2,
            ),
            "difference_percent": round(
                percentage,
                2,
            ) if percentage is not None else None,
        }