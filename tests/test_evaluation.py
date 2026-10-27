"""Synthetic checks before exposing the real test results."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from productmatch.review import MAX_THRESHOLD
from scripts.evaluate_frozen import load_test_split, retention_mask, summarize, run_evaluation
from scripts.import_data import connect_database, import_batches
from test_import_data import batch, pair


class EvaluationTests(unittest.TestCase):
    def test_fixed_thresholds_and_review_denominators(self):
        freeze={'binary_threshold':.5,'review_policy':{'lower_threshold':.2,'upper_threshold':MAX_THRESHOLD}}
        result=summarize([1,0,1,0],[.1,.1,.8,.8],freeze)
        self.assertEqual(result['review_policy']['false_different'],1)
        self.assertEqual(result['review_policy']['review_matches'],1)
        self.assertEqual(result['review_policy']['automatic_match_recall'],0)
        self.assertIsNone(result['review_policy']['match_precision'])
        self.assertEqual(result['binary_diagnostic']['false_positives'],1)
        self.assertEqual(result['binary_diagnostic']['false_negatives'],1)
        self.assertEqual(result['review_policy']['review_rate'],.5)

    def test_undefined_binary_precision_is_null(self):
        freeze={'binary_threshold':MAX_THRESHOLD,'review_policy':{'lower_threshold':0,'upper_threshold':MAX_THRESHOLD}}
        self.assertIsNone(summarize([0,1],[.2,.8],freeze)['binary_diagnostic']['precision'])

    def test_filter_uses_either_id_not_labels(self):
        rows=[{'left_id':1,'right_id':2,'label':1},
              {'left_id':3,'right_id':1,'label':0},
              {'left_id':3,'right_id':4,'label':1}]
        self.assertEqual(retention_mask(rows,{1}).tolist(),[False,False,True])
        for row in rows:
            row['label']=1-row['label']
        self.assertEqual(retention_mask(rows,{1}).tolist(),[False,False,True])

    def test_freeze_failure_prevents_test_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            freeze=Path(directory)/'freeze.json'
            freeze.write_text(json.dumps({}))
            with patch('scripts.evaluate_frozen.verify_freeze',side_effect=ValueError('changed')), \
                 patch('scripts.evaluate_frozen.load_test_split') as load:
                with self.assertRaisesRegex(ValueError,'changed'):
                    run_evaluation(Path(directory)/'db.sqlite3',freeze)
                load.assert_not_called()

    def test_loader_readonly_and_split_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'db.sqlite3'
            db=connect_database(path)
            import_batches(db,[batch([pair()]),batch([pair(3,4,1)],'test_unseen')])
            db.close()
            before=path.read_bytes()
            result=load_test_split(path,'test_unseen')
            self.assertEqual(set(result['titles']),{3,4})
            self.assertEqual(result['pairs'][0]['label'],1)
            self.assertEqual(before,path.read_bytes())
            with self.assertRaises(ValueError):
                load_test_split(path,'train')


if __name__=='__main__':
    unittest.main()
