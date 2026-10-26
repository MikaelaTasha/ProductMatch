"""SQLite integrity and repeatability tests using fictional records."""
import sqlite3
import unittest

from scripts.import_data import connect_database, import_batches


def pair(left=1, right=2, label=0):
    row = {'pair_id': f'{left}#{right}', 'id_left': left, 'id_right': right,
           'label': label, 'is_hard_negative': False}
    for side, identifier in (('left', left), ('right', right)):
        row.update({f'title_{side}': f"Fictional item's model {identifier}",
                    f'brand_{side}': None, f'description_{side}': '',
                    f'price_{side}': '001.50', f'priceCurrency_{side}': 'JPY',
                    f'cluster_id_{side}': identifier})
    return row


def batch(rows, split='train', digest='synthetic-hash'):
    return (split, (split+'.json.gz', digest, 'synthetic-archive', 'https://example.invalid/'), rows)


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.db = connect_database(':memory:')
        self.addCleanup(self.db.close)

    def counts(self):
        return tuple(self.db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                     for table in ('listings', 'labeled_pairs', 'dataset_splits'))

    def test_repeat_import_and_shared_listing(self):
        batches = [batch([pair(), pair(1, 3)])]
        import_batches(self.db, batches)
        self.assertEqual(self.counts(), (3, 2, 1))
        before = self.db.total_changes
        import_batches(self.db, batches)
        self.assertEqual(self.db.total_changes, before)
        self.assertEqual(self.counts(), (3, 2, 1))

    def test_same_pair_in_two_splits_preserves_memberships(self):
        import_batches(self.db, [batch([pair()]), batch([pair()], 'validation')])
        self.assertEqual(self.counts(), (2, 2, 2))

    def test_preserves_null_empty_text_price_and_join(self):
        import_batches(self.db, [batch([pair()])])
        self.assertEqual(self.db.execute(
            'SELECT brand, description, price FROM listings WHERE listing_id=1').fetchone(),
            (None, '', '001.50'))
        result = self.db.execute('''SELECT l.title, r.title, p.label FROM labeled_pairs p
            JOIN listings l ON l.listing_id=p.left_id
            JOIN listings r ON r.listing_id=p.right_id''').fetchone()
        self.assertEqual(result, ("Fictional item's model 1", "Fictional item's model 2", 0))

    def test_listing_conflict_rolls_back_all_new_rows(self):
        import_batches(self.db, [batch([pair()])])
        conflict = pair(1, 5)
        conflict['title_left'] = 'Unexpected changed title'
        with self.assertRaisesRegex(ValueError, 'Conflicting listings'):
            import_batches(self.db, [batch([pair(3, 4)], 'validation'),
                                     batch([conflict], 'test_seen')])
        self.assertEqual(self.counts(), (2, 1, 1))

    def test_conflicting_label_or_source_does_not_overwrite(self):
        import_batches(self.db, [batch([pair()])])
        for conflicting in (batch([pair(label=1)]), batch([pair()], digest='different')):
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                import_batches(self.db, [conflicting])
        self.assertEqual(self.db.execute('SELECT label FROM labeled_pairs').fetchone(), (0,))
        self.assertEqual(self.counts(), (2, 1, 1))

    def test_invalid_label_rolls_back(self):
        with self.assertRaises(ValueError):
            import_batches(self.db, [batch([pair(), pair(3, 4, label=2)])])
        self.assertEqual(self.counts(), (0, 0, 0))

    def test_foreign_keys_and_pair_id_constraint(self):
        import_batches(self.db, [batch([pair()])])
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO labeled_pairs VALUES ('train','1#999',1,999,0,0)")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO labeled_pairs VALUES ('train','wrong',1,2,0,0)")


if __name__ == '__main__':
    unittest.main()
