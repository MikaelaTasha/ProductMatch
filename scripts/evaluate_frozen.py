"""Day 14: score the frozen pipeline without fitting or selecting on test data."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

import numpy as np
from sklearn.exceptions import ConvergenceWarning

from productmatch.baseline import binary_metrics
from productmatch.browsing import connect_readonly
from productmatch.frozen import model_fingerprint, verify_freeze
from productmatch.review import review_metrics
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT, checksum

TEST_SPLITS = ('test_unseen', 'test_seen', 'test_half_unseen')
EXPECTED_RETAINED = {'test_seen': 4465, 'test_half_unseen': 2836}


def load_test_split(path, split):
    if split not in TEST_SPLITS:
        raise ValueError('Only frozen test splits are permitted.')
    with closing(connect_readonly(path)) as db:
        source = db.execute('SELECT * FROM dataset_splits WHERE split_name=?',(split,)).fetchone()
        pairs = db.execute('''SELECT pair_id,left_id,right_id,label FROM labeled_pairs
            WHERE split_name=? ORDER BY pair_id''',(split,)).fetchall()
        listings = db.execute('''SELECT listing_id,title,cluster_id FROM listings
            WHERE listing_id IN (SELECT left_id FROM labeled_pairs WHERE split_name=?
            UNION SELECT right_id FROM labeled_pairs WHERE split_name=?) ORDER BY listing_id''',
                              (split,split)).fetchall()
    if not pairs or source is None:
        raise ValueError(f'Missing test split: {split}')
    return {'titles':{r['listing_id']:r['title'] for r in listings},
            'clusters':{r['cluster_id'] for r in listings},
            'pairs':[dict(r) for r in pairs], 'source':dict(source)}


def development_ids(path):
    with closing(connect_readonly(path)) as db:
        rows=db.execute('''SELECT listing_id,cluster_id FROM listings WHERE listing_id IN (
            SELECT left_id FROM labeled_pairs WHERE split_name IN ('train','validation')
            UNION SELECT right_id FROM labeled_pairs WHERE split_name IN ('train','validation'))''').fetchall()
    return {r['listing_id'] for r in rows}, {r['cluster_id'] for r in rows}


def retention_mask(pairs, dev_ids):
    return np.array([p['left_id'] not in dev_ids and p['right_id'] not in dev_ids
                     for p in pairs],dtype=bool)


def summarize(labels, scores, freeze):
    labels=np.asarray(labels)
    policy=freeze['review_policy']
    binary=binary_metrics(labels,scores,freeze['binary_threshold'])
    # The frozen legacy binary helper returns 0 for undefined precision.
    # The protocol requires null; change presentation, not decisions.
    if binary['predicted_matches']==0:
        binary['precision']=None
    return {'pairs':len(labels),'actual_matches':int(np.sum(labels==1)),
            'actual_nonmatches':int(np.sum(labels==0)),
            'review_policy':review_metrics(labels,scores,policy['lower_threshold'],policy['upper_threshold']),
            'binary_diagnostic':binary}


def run_evaluation(path, freeze_path):
    freeze=json.loads(freeze_path.read_text())
    model=verify_freeze(freeze,path)  # Stops before loading test records on any mismatch.
    before=model_fingerprint(model)
    dev_ids,dev_clusters=development_ids(path)
    manifest=json.loads((ROOT/'docs/dataset-manifest.json').read_text())
    results={}
    for split_name in TEST_SPLITS:
        split=load_test_split(path,split_name)
        source=manifest['splits'][split_name]
        if (len(split['pairs'])!=source['pairs'] or
            split['source']['source_sha256']!=source['sha256']):
            raise ValueError('Test source differs from frozen manifest.')
        shared_offers=len(set(split['titles']) & dev_ids)
        shared_clusters=len(split['clusters'] & dev_clusters)
        if split_name=='test_unseen' and (shared_offers or shared_clusters):
            raise ValueError('Primary split unexpectedly overlaps development.')
        keep=retention_mask(split['pairs'],dev_ids)
        if split_name in EXPECTED_RETAINED and int(keep.sum())!=EXPECTED_RETAINED[split_name]:
            raise ValueError('Supplementary subset size differs from predeclared protocol.')
        scores,_,diagnostics=model.score(split)
        labels=np.asarray([p['label'] for p in split['pairs']])
        item={'role':'primary' if split_name=='test_unseen' else 'secondary_overlap_affected',
              'official':summarize(labels,scores,freeze),'source':split['source'],
              'diagnostics':diagnostics,'shared_development_offers':shared_offers,
              'shared_development_clusters':shared_clusters,
              'pairs_touching_development_offers':int((~keep).sum())}
        if split_name in EXPECTED_RETAINED:
            item['supplementary_no_development_offers']={
                'filter':'Exclude either endpoint in train/validation offer IDs; not an official benchmark.',
                'retained':int(keep.sum()),'excluded':int((~keep).sum()),
                'excluded_matches':int(np.sum(labels[~keep]==1)),
                'excluded_nonmatches':int(np.sum(labels[~keep]==0)),
                'metrics':summarize(labels[keep],scores[keep],freeze)}
        results[split_name]=item
    if before!=model_fingerprint(model) or checksum(path)!=freeze['database_sha256']:
        raise ValueError('Model or database changed during evaluation.')
    return {'evaluation_version':'frozen-test-evaluation-v1',
            'freeze_sha256':checksum(freeze_path),'runner_sha256':checksum(Path(__file__)),
            'selected_version':freeze['selected_version'],'runtime':freeze['runtime'],
            'binary_threshold':freeze['binary_threshold'],
            'review_thresholds':{k:freeze['review_policy'][k] for k in ('lower_threshold','upper_threshold')},
            'model_fingerprint_sha256':before,'results':results,
            'test_performance_seen':True,'thresholds_retuned':False,
            'limitations':'Test sets are now exposed. No pooled estimate, independent-pair confidence interval, or completed human-review outcomes. Validation precision targets are not guarantees.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=DEFAULT_DB)
    parser.add_argument('--freeze',type=Path,default=ROOT/'docs/evaluation-freeze.json')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/day14-test-results.json')
    args=parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('Output already exists; preserve the recorded evaluation.')
        report=run_evaluation(args.db,args.freeze)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as output:
            output.write(json.dumps(report,indent=2,allow_nan=False)+'\n')
    except (OSError,sqlite3.Error,ValueError,KeyError,ConvergenceWarning) as error:
        parser.exit(1,f'Frozen evaluation failed: {error}\n')
    for name,result in report['results'].items():
        print(name,json.dumps(result['official']))
    print(f'Report: {args.output}. Test results are now exposed; no retuning performed.')


if __name__=='__main__':
    main()
