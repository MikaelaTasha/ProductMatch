"""Verify comparison semantics and training-only reporting."""
from pathlib import Path
import tempfile
import unittest

from productmatch.features import FIELDS, FEATURE_NAMES, compare_titles
from scripts.preview_features import training_report
from scripts.import_data import connect_database, import_batches
from test_import_data import batch, pair


def states(left, right):
    return {k: v['state'] for k, v in compare_titles(left, right)['comparisons'].items()}


class FeatureTests(unittest.TestCase):
    def test_equal_totals_different_configuration(self):
        result = states('2x4GB', '1x8GB')
        self.assertEqual(result['storage_total'], 'agrees')
        self.assertEqual(result['storage_count'], 'differs')
        self.assertEqual(result['storage_per_item'], 'differs')

    def test_missing_and_ambiguous_are_not_conflicts(self):
        result = states('8GB 16GB AB-12 XY-34', '8GB AB-12')
        self.assertEqual(result['storage_mention'], 'ambiguous')
        self.assertEqual(result['model_candidate'], 'ambiguous')
        self.assertEqual(states(None, '8GB')['storage_mention'], 'missing_one')
        self.assertEqual(states(None, None)['storage_mention'], 'missing_both')

    def test_unit_equivalence_and_case(self):
        result = states('AB-12 1TB 1.5L 3.2GHz', 'ab-12 1000GB 1500ml 3200MHz')
        for field in ('model_candidate', 'storage_mention', 'volume_mention', 'frequency'):
            self.assertEqual(result[field], 'agrees')

    def test_do_not_mix_quantity_roles(self):
        result = states('2x8GB', '16GB')
        for field in ('storage_total', 'storage_per_item', 'storage_mention', 'storage_count'):
            self.assertEqual(result[field], 'missing_one')

    def test_count_categories_and_synonyms(self):
        self.assertEqual(states('2-pack', '1-pack')['pack_count'], 'differs')
        self.assertEqual(states('2 pcs', '2 pieces')['piece_count'], 'agrees')
        result = states('2 sheets', '2 modules')
        self.assertEqual(result['sheet_count'], 'missing_one')
        self.assertEqual(result['module_count'], 'missing_one')

    def test_fixed_numeric_schema_symmetry_and_no_decision(self):
        left, right = '2x4GB AB-12', '8GB XY-34'
        result = compare_titles(left, right)
        self.assertEqual(tuple(result['features']), FEATURE_NAMES)
        self.assertEqual(sum(result['features'].values()), len(FIELDS))
        self.assertEqual(result['features'], compare_titles(right, left)['features'])
        self.assertNotIn('label', result)
        self.assertNotIn('prediction', result)

    def test_report_training_only_readonly_and_label_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.sqlite3'
            connection = connect_database(path)
            row = pair()
            row['title_left'], row['title_right'] = '2x4GB', '1x8GB'
            import_batches(connection, [batch([row]), batch([pair(3,4)], 'test_unseen')])
            connection.close()
            before = path.read_bytes()
            report = training_report(path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(report['sql_quality']['pairs'], 1)
            self.assertEqual(report['comparison_counts']['storage_total']['agrees'], 1)
            connection = connect_database(path)
            connection.execute("UPDATE labeled_pairs SET label=1 WHERE split_name='train'")
            connection.commit()
            connection.close()
            after = training_report(path)
            self.assertEqual(after['comparison_counts'], report['comparison_counts'])
            for counts in report['comparison_counts'].values():
                self.assertEqual(sum(counts.values()), 1)


if __name__ == '__main__':
    unittest.main()
