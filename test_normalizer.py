"""
Temporary script for inspecting the actual Facts API field keys.

This helps us identify the exact field names that should be
used by normalize_facts().
"""

import requests

from app.services.listing_tour.normalizer import normalize_facts


LISTING_KEY = "17985574"

BASE_URL = "https://app.zipai.co"

FACTS_URL = (
    f"{BASE_URL}/api/idx/v1/listings/"
    f"{LISTING_KEY}/facts/"
)


print("Fetching Facts API...")

response = requests.get(
    FACTS_URL,
    timeout=30,
)

response.raise_for_status()

raw_facts = response.json()

print("Facts API response received.")


# Run current normalizer.
normalized = normalize_facts(raw_facts)


# ---------------------------------------------------------
# Print exact API keys.
# ---------------------------------------------------------

print("\n========================================")
print("ALL FACTS API FIELDS")
print("========================================")

for section in raw_facts.get("sections", []):

    print(f"\n### SECTION: {section.get('id')}")

    for field in section.get("fields", []):

        print(
            f"{field.get('key')} = "
            f"{field.get('value')}"
        )