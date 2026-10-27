"""Store frozen-model training predictions separately; never fabricate reviews."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from sklearn.exceptions import ConvergenceWarning
from productmatch.baseline import load_development_split
from productmatch.frozen import verify_freeze, model_fingerprint
from productmatch.predictions import DEFAULT_STORE, connect_store, save_predictions
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT,checksum


def run_storage(source_path,store_path,freeze_path):
    # Check destination before fitting; connect_store also rejects hard-link aliases.
    source_path,store_path=Path(source_path),Path(store_path)
    if source_path.resolve()==store_path.resolve() or (store_path.exists() and store_path.samefile(source_path)):
        raise ValueError('Prediction storage must be separate from the source database.')
    freeze=json.loads(Path(freeze_path).read_text())
    model=verify_freeze(freeze,source_path)
    split=load_development_split(source_path,'train')
    matrix,_=model.matrix(split)
    scores=model.estimator.predict_proba(matrix)[:,1]
    rows=[{'pair_id':p['pair_id'],'left_id':p['left_id'],'right_id':p['right_id'],
           'left_title':split['titles'][p['left_id']], 'right_title':split['titles'][p['right_id']],
           'features':features.tolist(),'score':float(score)}
          for p,features,score in zip(split['pairs'],matrix,scores)]
    if checksum(source_path)!=freeze['database_sha256'] or model_fingerprint(model)!=freeze['model_fingerprint_sha256']:
        raise ValueError('Frozen source or fitted model changed.')
    with closing(connect_store(store_path,source_path)) as connection:
        result=save_predictions(connection,freeze,
            {'database_sha256':freeze['database_sha256'],'split':'train',
             'split_sha256':split['source']['source_sha256']},rows)
        result['stored_predictions']=connection.execute('SELECT COUNT(*) FROM predictions').fetchone()[0]
        result['review_events']=connection.execute('SELECT COUNT(*) FROM review_events').fetchone()[0]
    result['scope']='Training predictions for workflow development; not evaluation results.'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=DEFAULT_DB)
    parser.add_argument('--store',type=Path,default=DEFAULT_STORE)
    parser.add_argument('--freeze',type=Path,default=ROOT/'docs/evaluation-freeze.json')
    args=parser.parse_args()
    try:
        result=run_storage(args.db,args.store,args.freeze)
    except (OSError,sqlite3.Error,ValueError,KeyError,ConvergenceWarning) as error:
        parser.exit(1,f'Prediction storage failed: {error}\n')
    print(json.dumps(result,indent=2))
    print(f'Local store: {args.store}')


if __name__=='__main__':
    main()
