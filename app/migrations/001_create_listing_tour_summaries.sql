
-- Create a table to cache AI-generated ListingTour summaries.
-- Each listing can have one summary per page.

CREATE TABLE IF NOT EXISTS listing_tour_summaries (
    listing_key TEXT NOT NULL,
    page_number SMALLINT NOT NULL
        CHECK (page_number BETWEEN 1 AND 6),

    summary JSONB NOT NULL,

    model_name TEXT,
    prompt_version TEXT,

    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (listing_key, page_number)
);

-- Index to support cache-expiration checks.
CREATE INDEX IF NOT EXISTS idx_listing_tour_summaries_generated_at
    ON listing_tour_summaries (generated_at);
