"""Read-only queries for the training-pair browser."""
from contextlib import closing
from pathlib import Path
import sqlite3


def connect_readonly(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def find_training_pairs(path, search=''):
    # Search is literal, including SQL LIKE's special characters.
    term = search.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    pattern = '%' + term + '%'
    with closing(connect_readonly(path)) as connection:
        rows = connection.execute('''
            SELECT p.pair_id FROM labeled_pairs AS p
            JOIN listings AS l ON l.listing_id=p.left_id
            JOIN listings AS r ON r.listing_id=p.right_id
            WHERE p.split_name='train' AND
              (p.pair_id LIKE ? ESCAPE '\\' OR l.title LIKE ? ESCAPE '\\'
               OR r.title LIKE ? ESCAPE '\\')
            ORDER BY p.pair_id
        ''', (pattern, pattern, pattern)).fetchall()
    return [row['pair_id'] for row in rows]


def get_training_pair(path, pair_id):
    with closing(connect_readonly(path)) as connection:
        pair = connection.execute('''
            SELECT pair_id, left_id, right_id, label FROM labeled_pairs
            WHERE split_name='train' AND pair_id=?
        ''', (pair_id,)).fetchone()
        if pair is None:
            return None
        result = dict(pair)
        for side in ('left', 'right'):
            listing = connection.execute('''
                SELECT listing_id, title, brand, description, price, price_currency
                FROM listings WHERE listing_id=?
            ''', (pair[f'{side}_id'],)).fetchone()
            if listing is None:
                raise ValueError('A pair references a missing listing.')
            result[side] = dict(listing)
    return result
