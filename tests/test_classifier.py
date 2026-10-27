"""Protect supervised fitting boundaries and feature/score alignment."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import numpy as np

from productmatch.classifier import MODEL_FEATURE_NAMES, PairClassifier
from scripts.import_data import connect_database, import_batches
from scripts.train_classifier import run_classifier
from test_import_data import batch, pair


def training():
    return {'titles': {1: 'alpha AB-12 2x4GB', 2: 'alpha AB-12 2x4GB',
                       3: 'beta XY-34 1x8GB', 4: 'gamma Z-99 16GB'},
            'pairs': [{'left_id': 1, 'right_id': 2, 'label': 1},
                      {'left_id': 3, 'right_id': 4, 'label': 0}]}


class ClassifierTests(unittest.TestCase):
    def test_matrix_and_probability_alignment(self):
        split = training()
        model = PairClassifier().fit(split)
        matrix, _ = model.matrix(split)
        scores, cosine, _ = model.score(split)
        self.assertEqual(matrix.shape, (2, len(MODEL_FEATURE_NAMES)))
        np.testing.assert_array_equal(cosine, matrix[:, 0])
        logits = matrix @ model.estimator.coef_[0] + model.estimator.intercept_[0]
        np.testing.assert_allclose(scores, 1 / (1 + np.exp(-logits)))
        self.assertGreater(scores[0], scores[1])

    def test_validation_labels_and_new_words_cannot_change_fit(self):
        model = PairClassifier().fit(training())
        coefficient = model.estimator.coef_.copy()
        idf = model.title_model.vectorizer.idf_.copy()
        validation = {'titles': {5: 'unseenword AB-12', 6: None},
                      'pairs': [{'left_id': 5, 'right_id': 6, 'label': 0}]}
        first, _, _ = model.score(validation)
        validation['pairs'][0]['label'] = 1
        second, _, _ = model.score(validation)
        np.testing.assert_array_equal(first, second)
        np.testing.assert_array_equal(coefficient, model.estimator.coef_)
        np.testing.assert_array_equal(idf, model.title_model.vectorizer.idf_)
        self.assertNotIn('unseenword', model.title_model.vectorizer.vocabulary_)

    def test_scores_symmetric_and_reproducible(self):
        split = training()
        a = PairClassifier().fit(split)
        b = PairClassifier().fit(split)
        np.testing.assert_array_equal(a.score(split)[0], b.score(split)[0])
        swapped = deepcopy(split)
        for row in swapped['pairs']:
            row['left_id'], row['right_id'] = row['right_id'], row['left_id']
        np.testing.assert_array_equal(a.score(split)[0], a.score(swapped)[0])

    def test_one_class_training_rejected(self):
        split = training()
        split['pairs'][0]['label'] = 0
        with self.assertRaisesRegex(ValueError, 'both binary'):
            PairClassifier().fit(split)

    def test_runner_without_tests_is_readonly_and_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.sqlite3'
            db = connect_database(path)
            import_batches(db, [batch([pair(1,2,1), pair(3,4,0)]),
                                batch([pair(5,6,1), pair(7,8,0)], 'validation')])
            db.close()
            before = path.read_bytes()
            report = run_classifier(path)
            self.assertEqual(report, run_classifier(path))
            self.assertEqual(before, path.read_bytes())
            self.assertFalse(report['test_sets_read'])
            self.assertEqual(report['training']['pairs'], 2)
            self.assertEqual(report['validation_metrics']['pairs'], 2)
            self.assertEqual(len(report['feature_names']), 71)

    def test_overlap_and_source_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.sqlite3'
            db = connect_database(path)
            import_batches(db, [batch([pair()]), batch([pair()], 'validation')])
            db.close()
            with self.assertRaisesRegex(ValueError, 'share 2 listing IDs'):
                run_classifier(path)
            path.unlink()
            db = connect_database(path)
            import_batches(db, [batch([pair()]), batch([pair(3,4)], 'validation')])
            db.execute("UPDATE dataset_splits SET archive_sha256='other' WHERE split_name='validation'")
            db.commit()
            db.close()
            with self.assertRaisesRegex(ValueError, 'different source archives'):
                run_classifier(path)


if __name__ == '__main__':
    unittest.main()
