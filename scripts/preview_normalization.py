"""Compare original and normalized training titles without changing SQLite."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3

from productmatch.browsing import connect_readonly
from productmatch.normalization import NORMALIZATION_VERSION, normalize_title
from scripts.import_data import DEFAULT_DB


def normalized_training_titles(db_path):
    with closing(connect_readonly(db_path)) as connection:
        rows = connection.execute('''
            SELECT listing_id, title FROM listings
            WHERE listing_id IN (
                SELECT left_id FROM labeled_pairs WHERE split_name='train'
                UNION
                SELECT right_id FROM labeled_pairs WHERE split_name='train'
            ) ORDER BY listing_id
        ''').fetchall()
    return [{'listing_id': row['listing_id'], 'original_title': row['title'],
             'normalized_title': normalize_title(row['title']),
             'normalization_version': NORMALIZATION_VERSION} for row in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--examples', type=int, choices=range(0, 21), default=5,
                        metavar='0..20')
    args = parser.parse_args()
    try:
        rows = normalized_training_titles(args.db)
    except (OSError, sqlite3.Error, TypeError) as error:
        parser.exit(1, f'Cannot preview titles: {error}\nRun python -m scripts.import_data to prepare the database.\n')
    if not rows:
        parser.exit(1, 'No training listings found. Run python -m scripts.import_data.\n')
    changed = sum(row['original_title'] != row['normalized_title'] for row in rows)
    for row in rows:
        if normalize_title(row['normalized_title']) != row['normalized_title']:
            parser.exit(1, f"Idempotence check failed for listing {row['listing_id']}\n")
    print(f'Normalization: {NORMALIZATION_VERSION}')
    print(f'Training listings: {len(rows):,}; titles changed: {changed:,}')
    print('Applying normalization twice gives the same result for every training title.')
    for row in rows[:args.examples]:
        print(f"\nListing {row['listing_id']}")
        print(f"Original:   {row['original_title']!r}")
        print(f"Normalized: {row['normalized_title']!r}")
    print('\nOriginal database values are unchanged. No matching decisions were made.')


if __name__ == '__main__':
    main()
