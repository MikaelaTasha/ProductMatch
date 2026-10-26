-- One pinned WDC snapshot per database. Original values remain unchanged.
CREATE TABLE IF NOT EXISTS listings (
    listing_id INTEGER PRIMARY KEY,
    title TEXT,
    brand TEXT,
    description TEXT,
    price TEXT,
    price_currency TEXT,
    cluster_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dataset_splits (
    split_name TEXT PRIMARY KEY CHECK (split_name IN
        ('train', 'validation', 'test_seen', 'test_half_unseen', 'test_unseen')),
    source_filename TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    source_url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS labeled_pairs (
    split_name TEXT NOT NULL REFERENCES dataset_splits(split_name),
    pair_id TEXT NOT NULL,
    left_id INTEGER NOT NULL REFERENCES listings(listing_id),
    right_id INTEGER NOT NULL REFERENCES listings(listing_id),
    label INTEGER NOT NULL CHECK (label IN (0, 1)),
    is_hard_negative INTEGER NOT NULL CHECK (is_hard_negative IN (0, 1)),
    PRIMARY KEY (split_name, pair_id),
    CHECK (pair_id = CAST(left_id AS TEXT) || '#' || CAST(right_id AS TEXT))
);

CREATE INDEX IF NOT EXISTS labeled_pairs_left_id ON labeled_pairs(left_id);
CREATE INDEX IF NOT EXISTS labeled_pairs_right_id ON labeled_pairs(right_id);
