"""Audit split metadata and validation errors without scoring test pairs."""
import argparse
from contextlib import closing
from itertools import combinations
import json
from pathlib import Path
import sqlite3

import numpy as np
from sklearn.exceptions import ConvergenceWarning

from productmatch.baseline import load_development_split, select_threshold
from productmatch.browsing import connect_readonly
from productmatch.classifier import PairClassifier, CLASSIFIER_VERSION
from productmatch.features import compare_titles, FIELDS
from productmatch.review import decisions, select_review_policy
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT


def split_audit(path):
    # Deliberately exclude test titles, labels, descriptions and prediction features.
    with closing(connect_readonly(path)) as db:
        rows = db.execute('''SELECT p.split_name, p.left_id, p.right_id,
            l.cluster_id AS left_cluster, r.cluster_id AS right_cluster
            FROM labeled_pairs p LEFT JOIN listings l ON l.listing_id=p.left_id
            LEFT JOIN listings r ON r.listing_id=p.right_id''').fetchall()
        sources = [dict(r) for r in db.execute('SELECT * FROM dataset_splits ORDER BY split_name')]
    splits = {}
    for r in rows:
        if r['left_cluster'] is None or r['right_cluster'] is None:
            raise ValueError('Missing listing or cluster metadata in split audit.')
        split = splits.setdefault(r['split_name'], {'offers':set(), 'clusters':set(),
                                                  'pairs':set(), 'cluster_pairs':set(), 'rows':[]})
        split['offers'].update((r['left_id'],r['right_id']))
        split['clusters'].update((r['left_cluster'],r['right_cluster']))
        split['pairs'].add(tuple(sorted((r['left_id'],r['right_id']))))
        split['cluster_pairs'].add(tuple(sorted((r['left_cluster'],r['right_cluster']))))
        split['rows'].append((r['left_id'],r['right_id']))
    dev_offers = set().union(*(splits.get(s,{}).get('offers',set()) for s in ('train','validation')))
    summaries = {name: {'pairs':len(s['rows']), 'unique_offers':len(s['offers']),
                        'unique_clusters':len(s['clusters']), 'unordered_pairs':len(s['pairs']),
                        'pairs_touching_development_offers':sum(a in dev_offers or b in dev_offers
                                                                for a,b in s['rows'])}
                 for name,s in sorted(splits.items())}
    overlaps = []
    for a,b in combinations(sorted(splits),2):
        overlaps.append({'left':a,'right':b, **{f'shared_{key}':len(splits[a][key]&splits[b][key])
                                               for key in ('offers','clusters','pairs','cluster_pairs')}})
    return {'scope':'IDs, cluster IDs and provenance only; no test titles, labels or scores',
            'splits':summaries,'overlaps':overlaps,'sources':sources}


def validation_audit(path):
    train, validation = (load_development_split(path,s) for s in ('train','validation'))
    if set(train['titles']) & set(validation['titles']):
        raise ValueError('Train/validation offer overlap; refusing to fit.')
    if train['source']['archive_sha256'] != validation['source']['archive_sha256']:
        raise ValueError('Train and validation have different archives.')
    model = PairClassifier().fit(train)
    scores, cosine, _ = model.score(validation)
    labels = np.array([p['label'] for p in validation['pairs']])
    threshold, binary_metrics = select_threshold(labels,scores)
    policy = select_review_policy(labels,scores)
    predicted = decisions(scores,policy['lower_threshold'],policy['upper_threshold'])
    masks = {'binary_false_match':(scores>=threshold)&(labels==0),
             'binary_missed_match':(scores<threshold)&(labels==1),
             'review_policy_false_different':(predicted=='Different')&(labels==1),
             'review_queue':predicted=='Review'}
    evidence = [compare_titles(validation['titles'][p['left_id']],validation['titles'][p['right_id']])
                for p in validation['pairs']]
    slices = {}
    for name,mask in masks.items():
        indexes = np.flatnonzero(mask)
        slices[name] = {'pairs':len(indexes),'evidence_counts':{
            field:{state:sum(evidence[i]['comparisons'][field]['state']==state for i in indexes)
                   for state in ('missing_both','missing_one','ambiguous','agrees','differs')}
            for field in FIELDS}}
    # Local-only examples: five most confident errors per type, deterministic pair-ID order for ties.
    samples = {}
    for name in ('binary_false_match','binary_missed_match','review_policy_false_different'):
        indexes = sorted(np.flatnonzero(masks[name]),
                         key=lambda i: (-scores[i] if name=='binary_false_match' else scores[i],
                                        validation['pairs'][i]['pair_id']))[:5]
        samples[name] = [{'pair_id':validation['pairs'][i]['pair_id'], 'label':int(labels[i]),
                         'score':float(scores[i]), 'cosine':float(cosine[i]),
                         'left_title':validation['titles'][validation['pairs'][i]['left_id']],
                         'right_title':validation['titles'][validation['pairs'][i]['right_id']],
                         'comparisons':evidence[i]['comparisons']} for i in indexes]
    return {'classifier_version':CLASSIFIER_VERSION,'binary_threshold':threshold,
            'binary_metrics':binary_metrics,'policy':policy,'error_slices':slices,
            'note':'Slices overlap; extracted evidence states are not verified error causes.'}, samples


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=DEFAULT_DB)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/day12-audit.json')
    args=parser.parse_args()
    try:
        validation, samples=validation_audit(args.db)
        report={'split_audit':split_audit(args.db),'validation_audit':validation,
                'test_predictions_computed':False,'test_performance_computed':False}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        local=ROOT/'artifacts/day12-validation-examples.json'
        local.parent.mkdir(parents=True,exist_ok=True)
        local.write_text(json.dumps(samples,indent=2,ensure_ascii=False)+'\n')
    except (OSError,sqlite3.Error,ValueError,ConvergenceWarning) as error:
        parser.exit(1,f'Audit failed: {error}\n')
    print(f'Aggregate report: {args.output}\nLocal validation examples: {local}')
    print('Test metadata audited; no test predictions or performance computed.')


if __name__=='__main__':
    main()
