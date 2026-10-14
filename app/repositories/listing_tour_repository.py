
"""
PostgreSQL repository for ListingTour AI summaries.

Stores one summary per listing and page. A summary is considered fresh
for seven days. Old summaries remain stored if regeneration fails.
"""

import json
from typing import Any

from app.database import get_connection


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS listing_tour_summaries (
    listing_key TEXT NOT NULL,
    page_number SMALLINT NOT NULL CHECK (page_number BETWEEN 1 AND 6),
    summary JSONB NOT NULL,
    model_name TEXT,
    prompt_version TEXT,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (listing_key, page_number)
);
"""


def ensure_summary_table() -> None:
    """Create the summary cache table if it does not exist."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()


def get_fresh_summary(
    listing_key: str,
    page_number: int,
) -> Any | None:
    """Return a cached summary if it was generated within the last 7 days."""
    ensure_summary_table()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT summary
                FROM listing_tour_summaries
                WHERE listing_key = %s
                  AND page_number = %s
                  AND generated_at >= NOW() - INTERVAL '7 days'
                """,
                (str(listing_key), page_number),
            )
            row = cursor.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def save_summary(
    listing_key: str,
    page_number: int,
    summary: Any,
    model_name: str | None = None,
    prompt_version: str | None = None,
) -> None:
    """Save a generated summary or update the existing cached summary."""
    ensure_summary_table()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO listing_tour_summaries (
                    listing_key,
                    page_number,
                    summary,
                    model_name,
                    prompt_version,
                    generated_at,
                    updated_at
                )
                VALUES (%s, %s, %s::jsonb, %s, %s, NOW(), NOW())
                ON CONFLICT (listing_key, page_number)
                DO UPDATE SET
                    summary = EXCLUDED.summary,
                    model_name = EXCLUDED.model_name,
                    prompt_version = EXCLUDED.prompt_version,
                    generated_at = NOW(),
                    updated_at = NOW()
                """,
                (
                    str(listing_key),
                    page_number,
                    json.dumps(summary, default=str),
                    model_name,
                    prompt_version,
                ),
            )
        conn.commit()
    finally:
        conn.close()
