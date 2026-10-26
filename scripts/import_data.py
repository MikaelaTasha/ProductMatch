"""Import the pinned WDC splits into SQLite without duplicating or relabeling data."""
import argparse
import json
from pathlib import Path
import sqlite3

from scripts.wdc_data import DEFAULT_DATA_DIR, FILES, ROOT, checksum, load_pairs

DEFAULT_DB = ROOT / 'data' / 'productmatch.sqlite3'
ATTRIBUTES = ('title', 'brand', 'description', 'price', 'priceCurrency', 'cluster_id')


def connect_database(path):
    connection = sqlite3.connect(path)
    connection.execute('PRAGMA foreign_keys = ON')
    connection.executescript((ROOT / 'sql/schema.sql').read_text())
    return connection


def insert_checked(connection, table, columns, key_columns, values):
    """Accept an identical existing row, but never silently overwrite conflicts."""
    keys = tuple(values[columns.index(key)] for key in key_columns)
    where = ' AND '.join(f'{key} = ?' for key in key_columns)
    existing = connection.execute(
        f'SELECT {", ".join(columns)} FROM {table} WHERE {where}', keys).fetchone()
    if existing is not None:
        if existing != values:
            raise ValueError(f'Conflicting {table} record {keys}; import rolled back.')
        return
    placeholders = ', '.join('?' for _ in values)
    connection.execute(
        f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({placeholders})', values)


def import_batches(connection, batches):
    """Commit all requested splits together; any conflict rolls the batch back."""
    with connection:
        for split, metadata, rows in batches:
            insert_checked(connection, 'dataset_splits',
                ('split_name', 'source_filename', 'source_sha256', 'archive_sha256', 'source_url'),
                ('split_name',), (split, *metadata))
            for row in rows:
                if type(row['label']) is not int or row['label'] not in (0, 1):
                    raise ValueError('Pair label must be integer 0 or 1.')
                if type(row['is_hard_negative']) is not bool:
                    raise ValueError('is_hard_negative must be boolean.')
                for side in ('left', 'right'):
                    listing_id = row[f'id_{side}']
                    attributes = tuple(row[f'{field}_{side}'] for field in ATTRIBUTES)
                    if type(listing_id) is not int or type(attributes[-1]) is not int:
                        raise ValueError('Listing and cluster IDs must be integers.')
                    if any(value is not None and not isinstance(value, str)
                           for value in attributes[:-1]):
                        raise ValueError('Listing attributes must be strings or null.')
                    insert_checked(connection, 'listings',
                        ('listing_id', 'title', 'brand', 'description', 'price',
                         'price_currency', 'cluster_id'), ('listing_id',),
                        (listing_id, *attributes))
                insert_checked(connection, 'labeled_pairs',
                    ('split_name', 'pair_id', 'left_id', 'right_id', 'label', 'is_hard_negative'),
                    ('split_name', 'pair_id'),
                    (split, row['pair_id'], row['id_left'], row['id_right'],
                     row['label'], int(row['is_hard_negative'])))


def read_batches(data_dir):
    manifest = json.loads((ROOT / 'docs/dataset-manifest.json').read_text())
    batches = []
    for split, filename in FILES.items():
        expected = manifest['splits'][split]
        path = data_dir / filename
        if checksum(path) != expected['sha256']:
            raise ValueError(f'{filename}: checksum differs from pinned snapshot.')
        rows = load_pairs(path)
        counts = {'pairs': len(rows), 'matches': sum(r['label'] for r in rows),
                  'non_matches': sum(1-r['label'] for r in rows),
                  'unique_offers': len({r[f'id_{s}'] for r in rows for s in ('left','right')})}
        if any(expected[key] != value for key, value in counts.items()):
            raise ValueError(f'{filename}: counts differ from pinned snapshot.')
        metadata = (filename, expected['sha256'], manifest['archive_sha256'], manifest['source_url'])
        batches.append((split, metadata, rows))
    return batches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    connection = None
    try:
        batches = read_batches(args.data_dir)
        args.db.parent.mkdir(parents=True, exist_ok=True)
        connection = connect_database(args.db)
        before = connection.total_changes
        import_batches(connection, batches)
        print(f'Database: {args.db}')
        print(f'New rows inserted: {connection.total_changes - before}')
        print('Distinct listings:', connection.execute('SELECT COUNT(*) FROM listings').fetchone()[0])
        for split, count, matches in connection.execute(
                'SELECT split_name, COUNT(*), SUM(label) FROM labeled_pairs GROUP BY split_name'):
            print(f'{split}: {count:,} pairs ({matches:,} benchmark matches)')
        print('Official split overlaps are preserved; see docs/dataset.md.')
        print('No human decisions, predictions, or test performance were imported/computed.')
    except (OSError, ValueError, KeyError, sqlite3.Error, EOFError) as error:
        parser.exit(1, f'Import failed: {error}\nIf files are missing, run python scripts/wdc_data.py --download\n')
    finally:
        if connection is not None:
            connection.close()


if __name__ == '__main__':
    main()
