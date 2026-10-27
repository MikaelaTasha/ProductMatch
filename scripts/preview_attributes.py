"""Inspect extracted title evidence on unique training listings only."""
import argparse
import json
from pathlib import Path
import sqlite3

from productmatch.attributes import EXTRACTION_VERSION, extract_title_attributes
from scripts.import_data import DEFAULT_DB
from scripts.preview_normalization import normalized_training_titles
from scripts.wdc_data import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--examples', type=int, choices=range(0,21), default=5, metavar='0..20')
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/day8-attribute-coverage.json')
    args = parser.parse_args()
    try:
        rows = normalized_training_titles(args.db)
        if not rows:
            raise ValueError('No training listings found; run python -m scripts.import_data.')
        evidence = [extract_title_attributes(row['original_title']) for row in rows]
        report = {'extraction_version': EXTRACTION_VERSION, 'scope':'unique training titles only',
                  'listings':len(rows), 'missing_counts':{
                      key:sum(item['missing'][key] for item in evidence) for key in evidence[0]['missing']},
                  'note':'Coverage of heuristic evidence, not extraction accuracy or matching performance.'}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    except (OSError,sqlite3.Error,ValueError,TypeError) as error:
        parser.exit(1,f'Attribute preview failed: {error}\n')
    print(json.dumps(report,indent=2))
    for row,item in list(zip(rows,evidence))[:args.examples]:
        print(f"\nListing {row['listing_id']}: {row['original_title']}")
        print(json.dumps(item,ensure_ascii=False,indent=2))
    print(f'Aggregate report: {args.output}')
    print('No source data changed. No match decisions made; descriptions are not parsed.')


if __name__ == '__main__':
    main()
