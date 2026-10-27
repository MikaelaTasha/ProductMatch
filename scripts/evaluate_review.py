"""Fit the unchanged Day 10 classifier and select a validation review policy."""
import argparse
import json
from pathlib import Path
import sqlite3

from sklearn.exceptions import ConvergenceWarning
from productmatch.baseline import load_development_split, select_threshold
from productmatch.classifier import PairClassifier, CLASSIFIER_VERSION, PARAMETERS
from productmatch.features import FEATURE_VERSION
from productmatch.review import select_review_policy
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT


def run_review(path):
    train = load_development_split(path, 'train')
    validation = load_development_split(path, 'validation')
    if set(train['titles']) & set(validation['titles']):
        raise ValueError('Train/validation share listing IDs; refusing to fit.')
    if train['source']['archive_sha256'] != validation['source']['archive_sha256']:
        raise ValueError('Train and validation have different source archives.')
    model = PairClassifier().fit(train)
    scores, _, diagnostics = model.score(validation)
    labels = [p['label'] for p in validation['pairs']]
    threshold, binary = select_threshold(labels, scores)
    policies = [select_review_policy(labels, scores, target, 20) for target in (.90, .95, .99)]
    return {'classifier_version': CLASSIFIER_VERSION, 'feature_version': FEATURE_VERSION,
            'parameters': PARAMETERS, 'evaluation_scope': 'validation-selected policies, not held-out performance',
            'selection_rule': 'maximize automatic coverage subject to precision/support for each enabled class; ties: fewer errors, more correct Matches, higher upper then lower lower threshold',
            'decision_rule': 'score < lower: Different; score >= upper: Match; otherwise Review',
            'default_policy': policies[1], 'sensitivity_policies': policies,
            'binary_reference': {'threshold': threshold, 'validation_metrics': binary},
            'validation_diagnostics': diagnostics,
            'sources': {'train': train['source'], 'validation': validation['source']},
            'test_sets_read': False,
            'limitations': '95% is a provisional learning target, not a guarantee or calibrated confidence. No human outcomes assumed; no model saved or UI integration.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/day11-review.json')
    args = parser.parse_args()
    try:
        report = run_review(args.db)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    except (OSError, sqlite3.Error, ValueError, ConvergenceWarning) as error:
        parser.exit(1, f'Review evaluation failed: {error}\n')
    print(json.dumps(report['default_policy'], indent=2))
    print(f'Validation only; report: {args.output}')


if __name__ == '__main__':
    main()
