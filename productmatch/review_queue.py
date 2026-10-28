"""Source-scoped training review queue; history never changes model evidence."""
from contextlib import closing

from productmatch.browsing import connect_readonly
from productmatch.predictions import connect_store, prediction_history, record_review
from scripts.wdc_data import checksum


def available_models(store_path,source_hash):
    with closing(connect_readonly(store_path)) as db:
        return [dict(row) for row in db.execute('''SELECT DISTINCT m.model_id,m.classifier_version
            FROM model_versions m JOIN predictions p ON p.model_id=m.model_id
            WHERE p.split_name='train' AND p.source_database_sha256=? ORDER BY m.model_id''',(source_hash,))]


def queue_rows(store_path,source_hash,model_id,*,status='Pending',model_decision='Review'):
    if status not in ('Pending','Completed','All') or model_decision not in ('Review','All'):
        raise ValueError('Invalid queue filter.')
    with closing(connect_readonly(store_path)) as db:
        rows=db.execute('''SELECT p.prediction_id,p.pair_id,p.decision,p.score,
                                  r.decision AS human_decision,r.reviewer
            FROM predictions p LEFT JOIN review_events r ON r.rowid=(
                SELECT MAX(e.rowid) FROM review_events e WHERE e.prediction_id=p.prediction_id)
            WHERE p.source_database_sha256=? AND p.model_id=? AND p.split_name='train'
            ORDER BY p.pair_id''',(source_hash,model_id)).fetchall()
    return [dict(r) for r in rows
            if (model_decision=='All' or r['decision']=='Review') and
               (status=='All' or (status=='Pending' and r['human_decision'] in (None,'Review')) or
                (status=='Completed' and r['human_decision'] in ('Match','Different')))]


def get_review_record(store_path,prediction_id,source_hash,model_id):
    with closing(connect_readonly(store_path)) as db:
        result=prediction_history(db,prediction_id)
    if result is None:
        raise ValueError('Prediction is no longer available.')
    p=result['prediction']
    if p['split_name']!='train' or p['source_database_sha256']!=source_hash or p['model_id']!=model_id:
        raise ValueError('Prediction does not belong to this source/model training queue.')
    return result


def submit_review(store_path,source_path,*,model_id,prediction_id,event_id,decision,reviewer,note):
    source_hash=checksum(source_path)
    # Recheck source/prediction membership at save time, not just on page display.
    get_review_record(store_path,prediction_id,source_hash,model_id)
    with closing(connect_store(store_path,source_path)) as db:
        return record_review(db,event_id=event_id,prediction_id=prediction_id,
                             decision=decision,reviewer=reviewer,note=note)
