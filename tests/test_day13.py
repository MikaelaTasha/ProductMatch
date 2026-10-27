"""Check the auxiliary evidence and safeguards used before test evaluation."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import numpy as np

from productmatch.candidate import CandidatePairClassifier, code_alias_state, CANDIDATE_VERSION
from productmatch.classifier import PairClassifier, CLASSIFIER_VERSION
from productmatch.frozen import FROZEN_FILES, PROTOCOL, model_fingerprint, runtime, verify_freeze
from scripts.select_day13 import choose_version
from test_classifier import training


class Day13Tests(unittest.TestCase):
    def test_alias_preserves_digits_and_ambiguity(self):
        self.assertEqual(code_alias_state('ATHM40X','ATH-M40X'),'agrees')
        self.assertEqual(code_alias_state('AB-12','AB-13'),'differs')
        self.assertEqual(code_alias_state('AB-12 AB12','AB12'),'ambiguous')
        self.assertEqual(code_alias_state(None,'AB12'),'missing_one')
        self.assertEqual(code_alias_state(None,None),'missing_both')
        self.assertEqual(code_alias_state('AB/12','AB.12'),'agrees')

    def test_original_columns_unchanged_and_extra_columns_symmetric(self):
        train=training()
        base=PairClassifier().fit(train)
        candidate=CandidatePairClassifier().fit(train)
        original,_=base.matrix(train)
        extended,_=candidate.matrix(train)
        np.testing.assert_array_equal(original,extended[:,:71])
        np.testing.assert_array_equal(extended[:,71:].sum(axis=1),[1,1])
        swapped=deepcopy(train)
        for p in swapped['pairs']:
            p['left_id'],p['right_id']=p['right_id'],p['left_id']
            p['label']=1-p['label']
        np.testing.assert_array_equal(extended,candidate.matrix(swapped)[0])

    def test_selection_requires_strict_improvement(self):
        results={CLASSIFIER_VERSION:{'binary_metrics':{'f1':.6}},
                 CANDIDATE_VERSION:{'binary_metrics':{'f1':.6}}}
        self.assertEqual(choose_version(results),CLASSIFIER_VERSION)
        results[CANDIDATE_VERSION]['binary_metrics']['f1']=.61
        self.assertEqual(choose_version(results),CANDIDATE_VERSION)
        results[CANDIDATE_VERSION]['binary_metrics']['f1']=.59
        self.assertEqual(choose_version(results),CLASSIFIER_VERSION)

    def test_fingerprint_repeatability_and_weight_change(self):
        a=CandidatePairClassifier().fit(training())
        b=CandidatePairClassifier().fit(training())
        self.assertEqual(model_fingerprint(a),model_fingerprint(b))
        b.estimator.coef_[0,0] += .01
        self.assertNotEqual(model_fingerprint(a),model_fingerprint(b))

    def test_changed_code_and_runtime_block_verification(self):
        freeze={'freeze_version':'evaluation-freeze-v1','protocol':PROTOCOL,
                'runtime':runtime(),'file_sha256':{name:'original' for name in FROZEN_FILES}}
        with patch('productmatch.frozen.checksum',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'Frozen file changed'):
                verify_freeze(freeze,None)
        freeze['runtime']={}
        with self.assertRaisesRegex(ValueError,'Runtime differs'):
            verify_freeze(freeze,None)


if __name__=='__main__':
    unittest.main()
