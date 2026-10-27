"""Test storage integrity with fictional predictions and review events only."""
from copy import deepcopy
from pathlib import Path
import sqlite3
import tempfile
import unittest

from productmatch.predictions import connect_store, save_predictions, record_review, prediction_history
from scripts.store_predictions import run_storage


def fixture():
    freeze={'selected_version':'fictional-model-v1','database_sha256':'source-hash',
            'feature_names':['example'],'review_policy':{'lower_threshold':.2,'upper_threshold':.8}}
    source={'database_sha256':'source-hash','split':'train','split_sha256':'split-hash'}
    rows=[{'pair_id':'1#2','left_id':1,'right_id':2,'left_title':'Example AB-12',
           'right_title':None,'features':[1.0],'score':.5}]
    return freeze,source,rows


class PredictionTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source=Path(self.directory.name)/'source.sqlite3'
        self.source.write_bytes(b'fictional source snapshot')
        self.store=Path(self.directory.name)/'predictions.sqlite3'
        self.db=connect_store(self.store,self.source)
        self.addCleanup(self.db.close)
        self.freeze,self.metadata,self.rows=fixture()

    def test_idempotence_provenance_and_original_inputs(self):
        self.assertEqual(save_predictions(self.db,self.freeze,self.metadata,self.rows)['inserted_predictions'],1)
        self.assertEqual(save_predictions(self.db,self.freeze,self.metadata,self.rows)['inserted_predictions'],0)
        pid=self.db.execute('SELECT prediction_id FROM predictions').fetchone()[0]
        history=prediction_history(self.db,pid)
        self.assertEqual(history['prediction']['decision'],'Review')
        self.assertEqual(history['prediction']['source_database_sha256'],'source-hash')
        self.assertIn('Example AB-12',history['prediction']['input_json'])
        self.assertEqual(history['reviews'],[])
        self.assertEqual(self.source.read_bytes(),b'fictional source snapshot')

    def test_conflicting_rerun_rolls_back_whole_batch(self):
        save_predictions(self.db,self.freeze,self.metadata,self.rows)
        changed=deepcopy(self.rows[0]);changed['score']=.9
        new=deepcopy(self.rows[0]);new.update(pair_id='3#4',left_id=3,right_id=4)
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            save_predictions(self.db,self.freeze,self.metadata,[new,changed])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM predictions').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT score FROM predictions').fetchone()[0],.5)

    def test_new_version_keeps_old_predictions(self):
        save_predictions(self.db,self.freeze,self.metadata,self.rows)
        revised=deepcopy(self.freeze);revised['selected_version']='fictional-model-v2'
        save_predictions(self.db,revised,self.metadata,self.rows)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM model_versions').fetchone()[0],2)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM predictions').fetchone()[0],2)

    def test_reviews_append_retrieve_and_retry_without_overwriting_prediction(self):
        save_predictions(self.db,self.freeze,self.metadata,self.rows)
        pid=self.db.execute('SELECT prediction_id FROM predictions').fetchone()[0]
        event=dict(event_id='request-1',prediction_id=pid,decision='Different',reviewer='fictional reviewer',note='example')
        self.assertTrue(record_review(self.db,**event))
        self.assertFalse(record_review(self.db,**event))
        event['decision']='Match'
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            record_review(self.db,**event)
        event['event_id']='request-2'
        record_review(self.db,**event)
        history=prediction_history(self.db,pid)
        self.assertEqual([r['decision'] for r in history['reviews']],['Different','Match'])
        self.assertEqual(history['prediction']['decision'],'Review')
        self.assertEqual(history['prediction']['score'],.5)
        self.assertIsNone(prediction_history(self.db,'missing'))

    def test_foreign_keys_validation_and_append_only(self):
        with self.assertRaises(sqlite3.IntegrityError):
            record_review(self.db,event_id='fake',prediction_id='missing',decision='Match',reviewer='test')
        with self.assertRaises(ValueError):
            record_review(self.db,event_id='fake',prediction_id='missing',decision='Match',reviewer=' ')
        save_predictions(self.db,self.freeze,self.metadata,self.rows)
        for statement in ('UPDATE predictions SET score=.9','DELETE FROM predictions',
                          "UPDATE model_versions SET classifier_version='changed'"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(statement)

    def test_invalid_score_or_features_rolls_back(self):
        for changes in ({'score':float('nan')},{'score':1.1},{'features':[]}, {'pair_id':'bad'}):
            rows=deepcopy(self.rows);rows[0].update(changes)
            with self.assertRaises(ValueError):
                save_predictions(self.db,self.freeze,self.metadata,rows)
            self.assertEqual(self.db.execute('SELECT COUNT(*) FROM model_versions').fetchone()[0],0)
        metadata=dict(self.metadata,split='test_unseen')
        with self.assertRaises(ValueError):
            save_predictions(self.db,self.freeze,metadata,self.rows)

    def test_source_destination_aliases_and_unrelated_tables_rejected(self):
        with self.assertRaises(ValueError):
            connect_store(self.source,self.source)
        with self.assertRaises(ValueError):
            run_storage(self.source,self.source,Path('not-read.json'))
        alias=Path(self.directory.name)/'alias.sqlite3'
        alias.hardlink_to(self.source)
        with self.assertRaises(ValueError):
            connect_store(alias,self.source)
        other=Path(self.directory.name)/'other.sqlite3'
        with sqlite3.connect(other) as db:
            db.execute('CREATE TABLE unrelated (id INTEGER)')
        with self.assertRaisesRegex(ValueError,'unrelated tables'):
            connect_store(other,self.source)


if __name__=='__main__':
    unittest.main()
