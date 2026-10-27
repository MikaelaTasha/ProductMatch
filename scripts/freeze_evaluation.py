"""Create once or verify a frozen pipeline; never score test pairs."""
import argparse
import json
from pathlib import Path
import sqlite3

from sklearn.exceptions import ConvergenceWarning
from productmatch.frozen import build_freeze, verify_freeze
from scripts.select_day13 import run_experiment
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=DEFAULT_DB)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/evaluation-freeze.json')
    parser.add_argument('--create',action='store_true',help='Create a new freeze; refuse to overwrite.')
    args=parser.parse_args()
    try:
        if args.create:
            if args.output.exists():
                raise ValueError('Freeze already exists; creation refuses to overwrite it.')
            report,model=run_experiment(args.db)
            expected=json.loads((ROOT/'docs/day13-experiment-results.json').read_text())
            if report != expected:
                raise ValueError('Experiment differs from published Day 13 result.')
            freeze=build_freeze(report,model,args.db)
            verify_freeze(freeze,args.db)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open('x') as output:
                output.write(json.dumps(freeze,indent=2,allow_nan=False)+'\n')
        else:
            verify_freeze(json.loads(args.output.read_text()),args.db)
    except (OSError,sqlite3.Error,ValueError,KeyError,ConvergenceWarning) as error:
        parser.exit(1,f'Freeze check failed: {error}\n')
    print('Freeze verified: inputs, code, runtime, thresholds and refitted model agree.')
    print('No test predictions or performance computed.')


if __name__=='__main__':
    main()
