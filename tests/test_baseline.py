"""Guard fitting boundaries, cosine math, and threshold accounting."""
from pathlib import Path
import tempfile
import unittest

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from productmatch.baseline import TitleBaseline, binary_metrics, select_threshold, load_development_split
from scripts.import_data import connect_database, import_batches
from scripts.run_baseline import run_baseline
from test_import_data import batch, pair


class BaselineTests(unittest.TestCase):
    def test_vocabulary_and_idf_are_not_changed_by_validation(self):
        model = TitleBaseline().fit({1: 'alpha common', 2: 'beta common'})
        before = model.vectorizer.idf_.copy()
        scores, diagnostics = model.score({'titles': {3: 'unseenonly', 4: None},
                                          'pairs': [{'left_id':3, 'right_id':4}]})
        self.assertNotIn('unseenonly', model.vectorizer.vocabulary_)
        np.testing.assert_array_equal(before, model.vectorizer.idf_)
        np.testing.assert_array_equal(scores, [0.0])
        self.assertEqual(diagnostics['zero_vector_listings'], 2)
        self.assertAlmostEqual(model.vectorizer.idf_[model.vectorizer.vocabulary_['alpha']],
                               np.log(3/2)+1)

    def test_sparse_pair_scores_equal_cosine_reference(self):
        titles = {1:'canon pg-545 8ml', 2:'canon pg-545 18ml', 3:'seagate drive'}
        model = TitleBaseline().fit(titles)
        pairs = [{'left_id':1, 'right_id':1}, {'left_id':1, 'right_id':2},
                 {'left_id':1, 'right_id':3}]
        scores, _ = model.score({'titles': titles, 'pairs': pairs})
        vectors = model.vectorizer.transform(list(titles.values()))
        expected = cosine_similarity(vectors)[0]
        np.testing.assert_allclose(scores, expected)
        self.assertAlmostEqual(scores[0], 1.0)
        self.assertGreater(scores[1], scores[2])
        self.assertEqual(scores[2], 0.0)
        self.assertIn('pg-545', model.vectorizer.vocabulary_)
        self.assertIn('8ml', model.vectorizer.vocabulary_)
        self.assertIn('18ml', model.vectorizer.vocabulary_)

    def test_model_punctuation_and_single_digit_tokens(self):
        model = TitleBaseline().fit({1:'MagSafe 1 HX432C16FB3/16 3.7GHz', 2:'MagSafe 2'})
        for token in ('1', '2', 'hx432c16fb3/16', '3.7ghz'):
            self.assertIn(token, model.vectorizer.vocabulary_)

    def test_confusion_counts_include_threshold_equality(self):
        result = binary_metrics([1,0,1,0], [.8,.8,.2,.1], .8)
        self.assertEqual([result[k] for k in ('true_positives','false_positives',
                                             'false_negatives','true_negatives')], [1,1,1,1])
        self.assertEqual(result['precision'], .5)
        self.assertEqual(result['recall'], .5)
        self.assertEqual(result['f1'], .5)

    def test_threshold_uses_scores_and_grouped_ties(self):
        threshold, metrics = select_threshold([1,1,0,0], [.9,.8,.8,.1])
        self.assertEqual(threshold, .8)
        self.assertAlmostEqual(metrics['f1'], .8)
        self.assertEqual(metrics['predicted_matches'], 3)
        self.assertEqual(select_threshold([1,0], [0,0])[0], 0)

    def test_invalid_inputs_fail_clearly(self):
        for labels, scores in (([],[]), ([1],[.2,.3]), ([1,0],[float('nan'),.2]),
                               ([1,2],[.2,.3]), ([1,0],[-.1,.3]), ([1,0],[1.1,.3])):
            with self.assertRaises(ValueError):
                select_threshold(labels, scores)
        with self.assertRaises(ValueError):
            select_threshold([1,1], [.2,.3])
        with self.assertRaises(ValueError):
            TitleBaseline().fit({1: None, 2: ''})

    def test_pipeline_needs_no_test_split_and_leaves_database_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.sqlite3'
            db = connect_database(path)
            train = pair()
            positive = pair(3,4,label=1)
            negative = pair(5,6)
            positive['title_left'] = positive['title_right'] = train['title_left']
            negative['title_left'], negative['title_right'] = 'novelword', 'othernewword'
            import_batches(db, [batch([train]), batch([positive,negative], 'validation')])
            db.close()
            before = path.read_bytes()
            report = run_baseline(path)
            self.assertFalse(report['test_sets_read'])
            self.assertEqual(report['validation_metrics']['f1'], 1.0)
            self.assertEqual(report['training']['unique_listings'], 2)
            self.assertEqual(before, path.read_bytes())
            with self.assertRaises(ValueError):
                load_development_split(path, 'test_unseen')

    def test_overlap_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.sqlite3'
            db=connect_database(path)
            import_batches(db,[batch([pair()]),batch([pair()], 'validation')])
            db.close()
            with self.assertRaisesRegex(ValueError, 'share 2 listing IDs'):
                run_baseline(path)


if __name__ == '__main__':
    unittest.main()
