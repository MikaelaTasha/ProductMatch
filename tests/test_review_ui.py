"""Review UI tests use isolated fictional data, never the real review store."""
from contextlib import closing
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from productmatch.predictions import connect_store, save_predictions
from productmatch.review_queue import queue_rows, get_review_record, submit_review
from scripts.import_data import connect_database, import_batches
from scripts.wdc_data import checksum
from test_import_data import batch, pair

APP=Path(__file__).resolve().parents[1]/'app.py'


class ReviewUITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.source=Path(self.temp.name)/'source.sqlite3'
        self.store=Path(self.temp.name)/'reviews.sqlite3'
        db=connect_database(self.source)
        import_batches(db,[batch([pair(),pair(3,4,1)])]);db.close()
        self.source_hash=checksum(self.source)
        freeze={'selected_version':'fictional-v1','database_sha256':self.source_hash,
                'feature_names':['x'],'review_policy':{'lower_threshold':.2,'upper_threshold':.8}}
        records=[{'pair_id':f'{a}#{b}','left_id':a,'right_id':b,'left_title':f'Item {a}',
                  'right_title':f'Item {b}','features':[1.0],'score':.5} for a,b in ((1,2),(3,4))]
        with closing(connect_store(self.store,self.source)) as db:
            self.model=save_predictions(db,freeze,{'database_sha256':self.source_hash,
                'split':'train','split_sha256':'fixture'},records)['model_id']
        self.ids=[r['prediction_id'] for r in queue_rows(self.store,self.source_hash,self.model)]
        env=patch.dict(os.environ,{'PRODUCTMATCH_DB':str(self.source),'PRODUCTMATCH_STORE':str(self.store)})
        env.start();self.addCleanup(env.stop)

    def app(self):
        at=AppTest.from_file(str(APP),default_timeout=15).run()
        at.radio(key='workspace_mode').set_value('Review queue').run()
        return at

    def save(self,at,decision='Different',reviewer='Fictional reviewer'):
        [w for w in at.text_input if w.label=='Your name or reviewer ID'][0].input(reviewer)
        [w for w in at.radio if w.label=='Your judgment'][0].set_value(decision)
        [b for b in at.button if b.label=='Save review'][0].click().run()

    def test_save_moves_completed_preserves_model_and_source(self):
        at=self.app()
        at.selectbox(key='review_prediction').set_value(self.ids[0]).run()
        self.assertFalse(at.exception)
        self.assertFalse([w for w in at.checkbox if w.label=='Show benchmark label'][0].value)
        self.save(at)
        self.assertFalse(at.exception)
        self.assertTrue(any('Saved Different' in s.value for s in at.success))
        self.assertEqual(len(queue_rows(self.store,self.source_hash,self.model)),1)
        self.assertIsNone(at.selectbox(key='review_prediction').value)
        at.selectbox(key='queue_status').set_value('Completed').run()
        at.selectbox(key='review_prediction').set_value(self.ids[0]).run()
        self.assertTrue(any('Latest human judgment: Different' in m.value for m in at.markdown))
        result=get_review_record(self.store,self.ids[0],self.source_hash,self.model)
        self.assertEqual(result['prediction']['decision'],'Review')
        self.assertEqual(len(result['reviews']),1)
        self.assertEqual(checksum(self.source),self.source_hash)

    def test_review_remains_pending_and_revision_keeps_history(self):
        at=self.app()
        at.selectbox(key='review_prediction').set_value(self.ids[0]).run()
        self.save(at,'Review')
        self.assertEqual(len(queue_rows(self.store,self.source_hash,self.model)),2)
        at.selectbox(key='review_prediction').set_value(self.ids[0]).run()
        self.save(at,'Match')
        result=get_review_record(self.store,self.ids[0],self.source_hash,self.model)
        self.assertEqual([r['decision'] for r in result['reviews']],['Review','Match'])
        self.assertFalse(at.exception)

    def test_blank_reviewer_and_pair_switch(self):
        at=self.app()
        at.selectbox(key='review_prediction').set_value(self.ids[0]).run()
        self.save(at,'Different',' ')
        self.assertTrue(at.error)
        self.assertEqual(get_review_record(self.store,self.ids[0],self.source_hash,self.model)['reviews'],[])
        [w for w in at.text_area if w.label=='Reason or note (optional)'][0].input('Only first pair').run()
        [w for w in at.checkbox if w.label=='Show benchmark label'][0].check().run()
        at.selectbox(key='review_prediction').set_value(self.ids[1]).run()
        self.assertEqual(at.text_area[0].value,'')
        self.assertIsNone([w for w in at.radio if w.label=='Your judgment'][0].value)
        self.assertFalse(at.checkbox[0].value)

    def test_missing_store_does_not_create_it(self):
        missing=self.store.with_name('absent.sqlite3')
        with patch.dict(os.environ,{'PRODUCTMATCH_STORE':str(missing)}):
            at=self.app()
        self.assertFalse(at.exception)
        self.assertTrue(any('Prepare the prediction store' in s.value for s in at.info))
        self.assertFalse(missing.exists())

    def test_source_and_model_mismatch_block_saves(self):
        self.assertEqual(queue_rows(self.store,'wrong-source',self.model),[])
        with self.assertRaisesRegex(ValueError,'does not belong'):
            submit_review(self.store,self.source,model_id='wrong-model',prediction_id=self.ids[0],
                          event_id='request',decision='Match',reviewer='fixture',note='')
        db=connect_database(self.source)
        db.execute("UPDATE listings SET title='changed' WHERE listing_id=1")
        db.commit();db.close()
        with self.assertRaisesRegex(ValueError,'does not belong'):
            submit_review(self.store,self.source,model_id=self.model,prediction_id=self.ids[0],
                          event_id='request',decision='Match',reviewer='fixture',note='')


if __name__=='__main__':
    unittest.main()
