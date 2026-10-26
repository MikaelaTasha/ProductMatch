"""Verify browsing boundaries and UI behavior with a fictional database."""
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from scripts.import_data import connect_database, import_batches
from productmatch.browsing import connect_readonly, find_training_pairs, get_training_pair
from test_import_data import batch, pair

APP = Path(__file__).resolve().parents[1] / 'app.py'


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'test.sqlite3'
        db = connect_database(self.path)
        import_batches(db, [batch([pair(), pair(3, 4, label=1)]),
                            batch([pair(5, 6)], 'test_unseen')])
        db.close()
        self.env = patch.dict(os.environ, {'PRODUCTMATCH_DB': str(self.path)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_queries_exclude_test_pairs_and_escape_search(self):
        self.assertEqual(find_training_pairs(self.path), ['1#2', '3#4'])
        self.assertIsNone(get_training_pair(self.path, '5#6'))
        self.assertEqual(find_training_pairs(self.path, '3#4'), ['3#4'])
        self.assertEqual(find_training_pairs(self.path, '%'), [])
        self.assertEqual(find_training_pairs(self.path, "' OR 1=1 --"), [])

    def test_readonly_and_missing_file(self):
        db = connect_readonly(self.path)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('DELETE FROM listings')
        finally:
            db.close()
        missing = self.path.with_name('missing.sqlite3')
        with self.assertRaises(FileNotFoundError):
            connect_readonly(missing)
        self.assertFalse(missing.exists())

    def test_navigation_hides_answer_and_respects_boundaries(self):
        at = AppTest.from_file(str(APP), default_timeout=15).run()
        self.assertFalse(at.exception)
        self.assertTrue(at.button(key='previous').disabled)
        self.assertFalse(at.checkbox(key='reveal_label').value)
        at.checkbox(key='reveal_label').check().run()
        self.assertTrue(any('Benchmark label: Different' in v.value for v in at.info))
        at.button(key='next').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.number_input(key='position').value, 2)
        self.assertTrue(at.button(key='next').disabled)
        self.assertFalse(at.checkbox(key='reveal_label').value)
        at.checkbox(key='reveal_label').check().run()
        at.number_input(key='position').set_value(1).run()
        self.assertFalse(at.checkbox(key='reveal_label').value)
        self.assertFalse(at.exception)

    def test_search_reset_empty_and_clear(self):
        at = AppTest.from_file(str(APP), default_timeout=15).run()
        at.button(key='next').click().run()
        at.checkbox(key='reveal_label').check().run()
        at.text_input(key='search').input('1#2').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.number_input(key='position').value, 1)
        self.assertFalse(at.checkbox(key='reveal_label').value)
        self.assertTrue(at.button(key='next').disabled)
        at.text_input(key='search').input('unfindable').run()
        self.assertTrue(any('No training pairs' in v.value for v in at.info))
        at.text_input(key='search').input('').run()
        self.assertFalse(at.exception)
        self.assertFalse(at.button(key='next').disabled)

    def test_missing_database_shows_setup(self):
        missing = self.path.with_name('missing.sqlite3')
        with patch.dict(os.environ, {'PRODUCTMATCH_DB': str(missing)}):
            at = AppTest.from_file(str(APP), default_timeout=15).run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Set up the local dataset' in v.value for v in at.info))
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
