"""One predeclared validation experiment; no test scoring or threshold tuning."""
import argparse
import json
from pathlib import Path
import sqlite3

from sklearn.exceptions import ConvergenceWarning
from productmatch.baseline import load_development_split, select_threshold
from productmatch.candidate import CandidatePairClassifier, CANDIDATE_VERSION, CANDIDATE_FEATURE_NAMES
from productmatch.classifier import PairClassifier, CLASSIFIER_VERSION, MODEL_FEATURE_NAMES
from productmatch.review import select_review_policy
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT

SELECTION_RULE = 'Retain the candidate only if validation-selected binary F1 strictly improves; ties retain Day 10. Report review-policy tradeoffs separately.'


def run_experiment(path):
    train, validation = (load_development_split(path,s) for s in ('train','validation'))
    if set(train['titles']) & set(validation['titles']):
        raise ValueError('Train/validation offer overlap.')
    if train['source']['archive_sha256'] != validation['source']['archive_sha256']:
        raise ValueError('Different training/validation archives.')
    labels = [p['label'] for p in validation['pairs']]
    results = {}
    models = {}
    for version, cls, names in ((CLASSIFIER_VERSION,PairClassifier,MODEL_FEATURE_NAMES),
                                (CANDIDATE_VERSION,CandidatePairClassifier,CANDIDATE_FEATURE_NAMES)):
        model = cls().fit(train)
        scores, _, _ = model.score(validation)
        threshold, metrics = select_threshold(labels,scores)
        results[version] = {'feature_names':list(names),'binary_threshold':threshold,
                            'binary_metrics':metrics, 'review_policy':select_review_policy(labels,scores),
                            'iterations':int(model.estimator.n_iter_[0])}
        models[version] = model
    chosen = choose_version(results)
    report = {'selection_rule':SELECTION_RULE,'selected_version':chosen,'results':results,
              'test_predictions_computed':False,'evaluation_scope':'validation development only',
              'sources':{'train':train['source'],'validation':validation['source']}}
    return report, models[chosen]


def choose_version(results):
    return (CANDIDATE_VERSION if results[CANDIDATE_VERSION]['binary_metrics']['f1'] >
            results[CLASSIFIER_VERSION]['binary_metrics']['f1'] else CLASSIFIER_VERSION)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=DEFAULT_DB)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/day13-experiment.json')
    args=parser.parse_args()
    try:
        report,_=run_experiment(args.db)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    except (OSError,sqlite3.Error,ValueError,ConvergenceWarning) as error:
        parser.exit(1,f'Experiment failed: {error}\n')
    print('Selected:',report['selected_version'])
    for name,result in report['results'].items():
        print(name, result['binary_metrics'],result['review_policy']['validation_metrics'])


if __name__=='__main__':
    main()
