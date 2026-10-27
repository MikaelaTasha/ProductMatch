"""Check abstention accounting, threshold search and disabled decision classes."""
import itertools
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np

from productmatch.review import decisions, review_metrics, select_review_policy, MAX_THRESHOLD
from scripts.evaluate_review import run_review
from scripts.import_data import connect_database, import_batches
from test_import_data import batch, pair


class ReviewTests(unittest.TestCase):
    def test_boundary_equality_and_partition(self):
        self.assertEqual(decisions([.1,.2,.5,.8,.9], .2,.8).tolist(),
                         ['Different','Review','Review','Match','Match'])
        self.assertEqual(decisions([.5], .5,.5).tolist(), ['Match'])
        metrics = review_metrics([0,1,0,1,0], [.1,.2,.5,.8,.9], .2,.8)
        self.assertEqual(metrics['false_matches'], 1)
        self.assertEqual(metrics['review_matches'], 1)
        self.assertEqual(metrics['review_nonmatches'], 1)
        self.assertEqual(metrics['automatic_match_recall'], .5)
        self.assertEqual(metrics['match_precision'], .5)
        self.assertAlmostEqual(metrics['review_rate'] + metrics['automatic_decision_coverage'], 1)

    def test_all_review_is_not_perfect_precision(self):
        policy = select_review_policy([0,1], [.5,.5], .95, 20)
        metrics = policy['validation_metrics']
        self.assertIsNone(metrics['match_precision'])
        self.assertIsNone(metrics['different_precision'])
        self.assertEqual(metrics['review_rate'], 1)
        self.assertFalse(policy['match_enabled'])
        self.assertFalse(policy['different_enabled'])

    def test_separable_scores_and_ties(self):
        policy = select_review_policy([0,0,1,1], [.1,.1,.9,.9], 1, 2)
        self.assertEqual(policy['validation_metrics']['automatic_decision_coverage'], 1)
        self.assertEqual(policy['validation_metrics']['match_precision'], 1)
        self.assertEqual(policy['validation_metrics']['different_precision'], 1)

    def test_search_matches_exhaustive_reference(self):
        rng = np.random.default_rng(42)
        for _ in range(15):
            labels = np.r_[0,1,rng.integers(0,2,10)]
            scores = rng.choice([0,.2,.4,.8,1], len(labels))
            policy = select_review_policy(labels, scores, .75, 2)
            boundaries = np.unique(np.r_[0., scores, MAX_THRESHOLD])
            best = None
            for lower, upper in itertools.product(boundaries, repeat=2):
                if lower > upper:
                    continue
                m = review_metrics(labels, scores, lower, upper)
                if any(m[count] and (m[count] < 2 or m[precision] < .75)
                       for count, precision in [('automatic_matches','match_precision'),
                                                ('automatic_different','different_precision')]):
                    continue
                key = (m['automatic_matches']+m['automatic_different'],
                       -m['false_matches']-m['false_different'],m['correct_matches'],upper,-lower)
                if best is None or key > best[0]:
                    best = (key, lower, upper)
            self.assertEqual((policy['lower_threshold'],policy['upper_threshold']), best[1:])

    def test_invalid_inputs(self):
        for lower,upper in ((.8,.2),(-.1,.9),(0,math.inf)):
            with self.assertRaises(ValueError):
                decisions([.5],lower,upper)
        for target,support in ((0,1),(1.1,1),(.95,0),(.95,True)):
            with self.assertRaises(ValueError):
                select_review_policy([0,1],[.2,.8],target,support)
        with self.assertRaises(ValueError):
            select_review_policy([0,1],[float('nan'),.5])

    def test_runner_readonly_without_test_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.sqlite3'
            db = connect_database(path)
            import_batches(db,[batch([pair(1,2,1),pair(3,4,0)]),
                               batch([pair(5,6,1),pair(7,8,0)],'validation')])
            db.close()
            before = path.read_bytes()
            report = run_review(path)
            self.assertEqual(path.read_bytes(),before)
            self.assertFalse(report['test_sets_read'])
            self.assertEqual(report['default_policy']['validation_metrics']['review_rate'],1)


if __name__ == '__main__':
    unittest.main()
