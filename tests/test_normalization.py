"""Protect meaningful product distinctions during title normalization."""
from pathlib import Path
import tempfile
import unittest

from productmatch.normalization import normalize_title
from scripts.import_data import connect_database, import_batches
from scripts.preview_normalization import normalized_training_titles
from test_import_data import batch, pair


class NormalizationTests(unittest.TestCase):
    def test_case_and_whitespace(self):
        self.assertEqual(normalize_title('  Kingston\t DDR4\n16GB  HX432C16FB3/16  '),
                         'kingston ddr4 16gb hx432c16fb3/16')

    def test_distinct_variants_stay_distinct(self):
        examples = [('Canon PG-545 Black Ink 8ml', 'Canon PG-545 Black Ink 18ml'),
                    ('DDR4 1x16GB', 'DDR4 2x8GB'),
                    ('Apple 60W MagSafe 1', 'Apple 60W MagSafe 2'),
                    ('Model AB-12', 'Model AB12'),
                    ('Size 1.5L', 'Size 15L')]
        for left, right in examples:
            with self.subTest(left=left):
                self.assertNotEqual(normalize_title(left), normalize_title(right))

    def test_preserves_punctuation_and_multilingual_text(self):
        self.assertEqual(normalize_title('  日本語  ＡＢＣ  Café  2×8GB / 3.7GHz '),
                         '日本語 ａｂｃ café 2×8gb / 3.7ghz')

    def test_missing_empty_and_invalid_types(self):
        self.assertIsNone(normalize_title(None))
        self.assertEqual(normalize_title(''), '')
        self.assertEqual(normalize_title(' \t\n'), '')
        for invalid in (123, [], {}):
            with self.assertRaises(TypeError):
                normalize_title(invalid)

    def test_idempotent(self):
        for title in (None, '', ' \n ', 'Canon PG-545 8ml', ' DDR4  2x8GB ', '日本語 Café'):
            with self.subTest(title=title):
                result = normalize_title(title)
                self.assertEqual(normalize_title(result), result)

    def test_preview_preserves_originals_and_training_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'example.sqlite3'
            connection = connect_database(path)
            training = pair()
            training['title_left'] = '  Canon PG-545 8ml  '
            import_batches(connection, [batch([training]), batch([pair(3,4)], 'test_unseen')])
            connection.close()
            before = path.read_bytes()
            rows = normalized_training_titles(path)
            self.assertEqual({row['listing_id'] for row in rows}, {1,2})
            self.assertEqual(rows[0]['original_title'], '  Canon PG-545 8ml  ')
            self.assertEqual(rows[0]['normalized_title'], 'canon pg-545 8ml')
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
