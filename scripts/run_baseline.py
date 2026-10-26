"""Run the Day 7 title baseline on training/validation data only."""
import argparse
import json
from pathlib import Path
import platform
import sqlite3

import numpy as np
import scipy
import sklearn

from productmatch.baseline import BASELINE_VERSION, TOKEN_PATTERN, TitleBaseline
from productmatch.baseline import load_development_split, select_threshold
from productmatch.normalization import NORMALIZATION_VERSION
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT


def run_baseline(db_path):
    train = load_development_split(db_path, 'train')
    validation = load_development_split(db_path, 'validation')
    overlap = set(train['titles']) & set(validation['titles'])
    if overlap:
        raise ValueError(f'Train/validation share {len(overlap)} listing IDs; refusing to fit.')
    if train['source']['archive_sha256'] != validation['source']['archive_sha256']:
        raise ValueError('Train and validation have different source archives.')
    model = TitleBaseline().fit(train['titles'])
    scores, diagnostics = model.score(validation)
    labels = [pair['label'] for pair in validation['pairs']]
    threshold, metrics = select_threshold(labels, scores)
    return {
        'baseline_version': BASELINE_VERSION, 'normalization_version': NORMALIZATION_VERSION,
        'evaluation_scope': 'validation used to select threshold; not held-out test performance',
        'fit_scope': 'unique training listing titles only; no labels or metadata as features',
        'selection_rule': 'maximize match-class F1; ties: higher precision, then higher threshold',
        'decision_rule': 'Match if cosine >= threshold, otherwise Different; no Review policy yet',
        'threshold': threshold, 'token_pattern': TOKEN_PATTERN,
        'tfidf': {'norm': 'l2', 'smooth_idf': True, 'ngram_range': [1, 1],
                  'min_df': 1, 'max_df': 1.0, 'sublinear_tf': False, 'stop_words': None},
        'training': {'unique_listings': len(train['titles']), 'pairs': len(train['pairs']),
                     'vocabulary_size': len(model.vectorizer.vocabulary_)},
        'validation_diagnostics': diagnostics, 'validation_metrics': metrics,
        'always_different_validation_accuracy': 1 - sum(labels) / len(labels),
        'train_validation_offer_overlap': len(overlap),
        'sources': {'train': train['source'], 'validation': validation['source']},
        'runtime': {'python': platform.python_version(), 'scikit_learn': sklearn.__version__,
                    'numpy': np.__version__, 'scipy': scipy.__version__},
        'test_sets_read': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/day7-baseline.json')
    args = parser.parse_args()
    try:
        report = run_baseline(args.db)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    except (OSError, sqlite3.Error, ValueError, KeyError) as error:
        parser.exit(1, f'Baseline failed: {error}\n')
    metrics = report['validation_metrics']
    print(f"TF-IDF fitted on {report['training']['unique_listings']:,} unique training listings")
    print(f"Validation-selected threshold: {report['threshold']:.6f}")
    for key in ('precision', 'recall', 'f1'):
        print(f"Validation {key}: {metrics[key]:.2%}")
    print(f"False matches: {metrics['false_positives']}; missed matches: {metrics['false_negatives']}")
    print('Review rate: 0%; automatic-decision coverage: 100% (binary baseline only)')
    print('These are tuning-set results. Test sets were not read. No trained model was saved.')
    print(f'Report: {args.output}')


if __name__ == '__main__':
    main()
