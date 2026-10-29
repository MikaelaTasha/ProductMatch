"""Check faithful explanations of stored snapshots, not invented reasons."""
from contextlib import closing
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from productmatch.candidate import CANDIDATE_VERSION,CANDIDATE_FEATURE_NAMES,code_alias_state
from productmatch.evidence import explain_prediction
from productmatch.features import compare_titles,STATES
from productmatch.predictions import connect_store,save_predictions
from productmatch.review import MAX_THRESHOLD
from scripts.import_data import connect_database,import_batches
from scripts.wdc_data import checksum
from test_import_data import batch,pair


def example(left='AB-12 2x4GB',right='AB12 1x8GB'):
    features={'title_cosine':.6,**compare_titles(left,right)['features']}
    state=code_alias_state(left,right)
    features.update({f'code_alias_{s}':int(s==state) for s in STATES})
    freeze={'selected_version':CANDIDATE_VERSION,'feature_names':list(CANDIDATE_FEATURE_NAMES),
            'review_policy':{'lower_threshold':.2,'upper_threshold':MAX_THRESHOLD}}
    values=[features[name] for name in CANDIDATE_FEATURE_NAMES]
    record={'model':{'freeze_json':json.dumps(freeze)},'prediction':{
        'input_json':json.dumps({'left_title':left,'right_title':right}),
        'features_json':json.dumps(values),'decision':'Review','score':.5}}
    return record,freeze,values


class EvidenceTests(unittest.TestCase):
    def test_same_total_different_configuration_and_alias(self):
        record,_,_=example()
        result=explain_prediction(record)
        rows={r['Detail']:r for r in result['rows']}
        self.assertEqual(rows['Calculated pack storage']['Left'],'8 GB')
        self.assertEqual(rows['Calculated pack storage']['Evidence'],'Same extracted value')
        self.assertEqual(rows['Storage pack item count']['Evidence'],'Different extracted values')
        self.assertEqual(rows['Possible model code']['Evidence'],'Different extracted values')
        self.assertEqual(result['alias_evidence'],'Same extracted value')
        self.assertIn('Automatic Match is disabled',result['decision_reason'])

    def test_missing_and_multiple_values_do_not_become_conflicts(self):
        record,_,_=example(None,'8GB 16GB')
        rows={r['Detail']:r for r in explain_prediction(record)['rows']}
        self.assertEqual(rows['Storage mentioned (role unspecified)']['Left'],'Not extracted')
        self.assertEqual(rows['Storage mentioned (role unspecified)']['Evidence'],'Missing on one side')
        record,_,_=example('8GB 16GB','8GB')
        rows={r['Detail']:r for r in explain_prediction(record)['rows']}
        self.assertEqual(rows['Storage mentioned (role unspecified)']['Evidence'],'Multiple possible values')

    def test_stale_evidence_and_decision_mismatch_rejected(self):
        record,_,_=example()
        stale=deepcopy(record)
        stale['prediction']['input_json']=json.dumps({'left_title':'', 'right_title':''})
        with self.assertRaisesRegex(ValueError,'no longer agree'):
            explain_prediction(stale)
        record['prediction']['decision']='Match'
        with self.assertRaisesRegex(ValueError,'decision does not agree'):
            explain_prediction(record)

    def test_unknown_schema_and_nonfinite_values_rejected(self):
        record,_,_=example()
        altered=deepcopy(record);altered['model']['freeze_json']='{"selected_version":"unknown","feature_names":[]}'
        with self.assertRaises(ValueError):
            explain_prediction(altered)
        values=json.loads(record['prediction']['features_json']);values[0]=float('nan')
        record['prediction']['features_json']=json.dumps(values)
        with self.assertRaises(ValueError):
            explain_prediction(record)

    def test_equality_at_lower_threshold_routes_to_review(self):
        record,_,_=example();record['prediction']['score']=.2
        self.assertIn('review range',explain_prediction(record)['decision_reason'])
        record['prediction'].update(score=.19,decision='Different')
        self.assertIn('below',explain_prediction(record)['decision_reason'])

    def test_ui_displays_evidence_without_writing_review(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.sqlite3';store=Path(folder)/'store.sqlite3'
            row=pair();row['title_left']='AB-12 2x4GB';row['title_right']='AB12 1x8GB'
            db=connect_database(source);import_batches(db,[batch([row])]);db.close()
            record,freeze,features=example();freeze['database_sha256']=checksum(source)
            with closing(connect_store(store,source)) as db:
                save_predictions(db,freeze,{'database_sha256':checksum(source),'split':'train','split_sha256':'fixture'},
                    [{'pair_id':'1#2','left_id':1,'right_id':2,'left_title':row['title_left'],
                      'right_title':row['title_right'],'features':features,'score':.5}])
                pid=db.execute('SELECT prediction_id FROM predictions').fetchone()[0]
            with patch.dict(os.environ,{'PRODUCTMATCH_DB':str(source),'PRODUCTMATCH_STORE':str(store)}):
                at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run()
                at.radio(key='workspace_mode').set_value('Review queue').run()
                at.selectbox(key='review_prediction').set_value(pid).run()
                self.assertFalse(at.exception)
                self.assertEqual(len(at.dataframe),1)
                data=at.dataframe[0].value
                self.assertIn('Calculated pack storage',data['Detail'].tolist())
                self.assertTrue(any('Automatic Match is disabled' in m.value for m in at.markdown))
                self.assertFalse([w for w in at.checkbox if w.label=='Show benchmark label'][0].value)
            with closing(connect_store(store,source)) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM review_events').fetchone()[0],0)


if __name__=='__main__':
    unittest.main()
