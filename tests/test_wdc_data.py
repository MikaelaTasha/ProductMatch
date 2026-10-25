"""Loader checks use fictional records, not redistributed benchmark data."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
import io
from unittest.mock import patch

from scripts.wdc_data import FILES, inspect_training, load_pairs, prepare


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'pairs.json.gz'
        self.row = {'id_left': 1, 'id_right': 2, 'pair_id': '1#2',
                    'title_left': 'Example A', 'title_right': 'Example B',
                    'brand_left': None, 'label': 0}

    def write_rows(self, rows):
        with gzip.open(self.path, 'wt', encoding='utf-8') as target:
            for row in rows:
                target.write(json.dumps(row) + '\n')

    def test_preserves_missing_values_and_labels(self):
        self.write_rows([self.row])
        self.assertEqual(load_pairs(self.path), [self.row])

    def test_rejects_duplicate_pairs(self):
        self.write_rows([self.row, self.row])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            load_pairs(self.path)

    def test_rejects_invalid_labels(self):
        for label in (2, '0', True, None):
            with self.subTest(label=label):
                self.write_rows([{**self.row, 'label': label}])
                with self.assertRaisesRegex(ValueError, 'label'):
                    load_pairs(self.path)

    def test_rejects_missing_fields_and_inconsistent_ids(self):
        for row in ({'label': 0}, {**self.row, 'pair_id': '2#1'}):
            self.write_rows([row])
            with self.assertRaises(ValueError):
                load_pairs(self.path)

    def test_rejects_empty_data(self):
        self.write_rows([])
        with self.assertRaisesRegex(ValueError, 'empty'):
            load_pairs(self.path)

    def test_refuses_corrupt_cached_download(self):
        directory = Path(self.temp.name)
        (directory / '50pair.zip').write_bytes(b'incomplete download')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            prepare(directory)
        self.assertFalse((directory / FILES['train']).exists())

    def test_preview_includes_both_classes_without_duplicates(self):
        rows = [{**self.row, 'pair_id': str(i), 'label': int(i >= 2000)}
                for i in range(2500)]
        output = io.StringIO()
        with patch('scripts.wdc_data.load_pairs', return_value=rows):
            with redirect_stdout(output):
                inspect_training(Path(self.temp.name), 4)
        text = output.getvalue()
        for expected in ('1. 0 | benchmark label: Different',
                         '2. 2000 | benchmark label: Match',
                         '3. 1 | benchmark label: Different',
                         '4. 2001 | benchmark label: Match'):
            self.assertIn(expected, text)


if __name__ == '__main__':
    unittest.main()
