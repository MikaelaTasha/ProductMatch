"""Summarize training-pair features and SQL data quality without fitting a model."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from productmatch.browsing import connect_readonly
from productmatch.features import FEATURE_VERSION, FEATURE_NAMES, FIELDS, STATES, compare_titles
from productmatch.attributes import EXTRACTION_VERSION
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT


def training_report(path):
    with closing(connect_readonly(path)) as connection:
        quality = dict(connection.execute((ROOT/'sql/day9-quality.sql').read_text()).fetchone())
        rows = connection.execute('''SELECT l.title AS left_title, r.title AS right_title
            FROM labeled_pairs p
            JOIN listings l ON l.listing_id=p.left_id
            JOIN listings r ON r.listing_id=p.right_id
            WHERE p.split_name='train' ORDER BY p.pair_id''').fetchall()
    if not rows or quality['broken_references']:
        raise ValueError('Training pairs are missing or contain broken listing references.')
    counts = {field: {state: 0 for state in STATES} for field in FIELDS}
    for row in rows:
        result = compare_titles(row['left_title'], row['right_title'])
        for field, item in result['comparisons'].items():
            counts[field][item['state']] += 1
    return {'feature_version': FEATURE_VERSION, 'extraction_version': EXTRACTION_VERSION,
            'scope': 'training pairs only', 'numeric_feature_count': len(FEATURE_NAMES),
            'sql_quality': quality, 'comparison_counts': counts,
            'note': 'Heuristic evidence states, not verified conflicts or predictions.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/day9-feature-summary.json')
    args = parser.parse_args()
    try:
        report = training_report(args.db)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+'\n')
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.exit(1, f'Feature preview failed: {error}\n')
    print(json.dumps(report, indent=2))
    print(f'Aggregate report: {args.output}')


if __name__ == '__main__':
    main()
