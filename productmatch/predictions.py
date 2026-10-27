"""Versioned local predictions and explicitly authored review events."""
import hashlib
import json
import math
from pathlib import Path
import sqlite3

from productmatch.review import decisions
from scripts.wdc_data import ROOT

DEFAULT_STORE = ROOT/'data/predictions.sqlite3'


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def connect_store(path, source_path):
    path,source_path=Path(path).resolve(),Path(source_path).resolve()
    if path==source_path or (path.exists() and source_path.exists() and path.samefile(source_path)):
        raise ValueError('Prediction storage must be separate from the source database.')
    path.parent.mkdir(parents=True,exist_ok=True)
    connection=sqlite3.connect(path)
    connection.execute('PRAGMA foreign_keys=ON')
    tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if tables and not tables <= {'model_versions','predictions','review_events'}:
        connection.close()
        raise ValueError('Destination contains unrelated tables; refusing to alter it.')
    connection.executescript((ROOT/'sql/predictions.sql').read_text())
    return connection


def insert_identical(connection,table,columns,values):
    existing=connection.execute(f'SELECT {", ".join(columns)} FROM {table} WHERE {columns[0]}=?',
                                (values[0],)).fetchone()
    if existing is not None:
        if tuple(existing)!=tuple(values):
            raise ValueError(f'Conflicting {table} record; existing evidence preserved.')
        return False
    connection.execute(f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({", ".join("?" for _ in columns)})',values)
    return True


def save_predictions(connection,freeze,source,rows):
    """Atomically save an identical rerunnable batch; never overwrite old evidence."""
    if source['database_sha256']!=freeze['database_sha256']:
        raise ValueError('Prediction source differs from model freeze.')
    if source['split'] not in ('train','validation'):
        raise ValueError('Only development predictions may be stored in this workflow.')
    model_id=digest(freeze)
    added=0
    policy=freeze['review_policy']
    with connection:
        insert_identical(connection,'model_versions',('model_id','classifier_version','freeze_json'),
                         (model_id,freeze['selected_version'],canonical(freeze)))
        for row in rows:
            if row['pair_id']!=f"{row['left_id']}#{row['right_id']}":
                raise ValueError('Pair ID does not match input listing IDs.')
            features=row['features']
            if len(features)!=len(freeze['feature_names']) or not all(math.isfinite(v) for v in features):
                raise ValueError('Feature vector does not match frozen schema.')
            score=float(row['score'])
            decision=str(decisions([score],policy['lower_threshold'],policy['upper_threshold'])[0])
            inputs={key:row[key] for key in ('left_id','right_id','left_title','right_title')}
            prediction_id=digest([model_id,source['database_sha256'],source['split'],row['pair_id']])
            added+=insert_identical(connection,'predictions',
                ('prediction_id','model_id','source_database_sha256','source_split_sha256',
                 'split_name','pair_id','input_json','features_json','score','decision'),
                (prediction_id,model_id,source['database_sha256'],source['split_sha256'],
                 source['split'],row['pair_id'],canonical(inputs),canonical(features),score,decision))
    return {'model_id':model_id,'inserted_predictions':added}


def record_review(connection,*,event_id,prediction_id,decision,reviewer,note=''):
    """Caller supplies a stable request ID; repeated submissions are idempotent."""
    if not isinstance(event_id,str) or not event_id.strip():
        raise ValueError('A nonempty event ID is required.')
    if not isinstance(reviewer,str) or not reviewer.strip():
        raise ValueError('A reviewer name or local identifier is required.')
    if decision not in ('Match','Different','Review') or not isinstance(note,str):
        raise ValueError('Invalid review decision or note.')
    with connection:
        return insert_identical(connection,'review_events',
            ('event_id','prediction_id','decision','reviewer','note'),
            (event_id,prediction_id,decision,reviewer.strip(),note))


def prediction_history(connection,prediction_id):
    connection.row_factory=sqlite3.Row
    prediction=connection.execute('SELECT * FROM predictions WHERE prediction_id=?',(prediction_id,)).fetchone()
    if prediction is None:
        return None
    reviews=connection.execute('SELECT * FROM review_events WHERE prediction_id=? ORDER BY rowid',
                               (prediction_id,)).fetchall()
    model=connection.execute('SELECT * FROM model_versions WHERE model_id=?',(prediction['model_id'],)).fetchone()
    return {'prediction':dict(prediction),'model':dict(model),'reviews':[dict(r) for r in reviews]}
