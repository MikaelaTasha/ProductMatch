"""Download the pinned WDC archive and inspect its small training split."""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
from urllib.error import URLError
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / 'data' / 'raw' / 'wdc-products'
URL = ('https://data.dws.informatik.uni-mannheim.de/'
       'largescaleproductcorpus/data/wdc-products/50pair.zip')
SHA256 = '57fca0c66bd1d7a09298dfb5df4ed6428251487517e9cfbce209aad99388359d'
PREFIX = 'wdcproducts50cc50rnd'
FILES = {
    'train': PREFIX + '000un_train_small.json.gz',
    'validation': PREFIX + '000un_valid_small.json.gz',
    'test_seen': PREFIX + '000un_gs.json.gz',
    'test_half_unseen': PREFIX + '050un_gs.json.gz',
    'test_unseen': PREFIX + '100un_gs.json.gz',
}


def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(data_dir):
    """Reuse verified downloads; extract only explicitly selected filenames."""
    data_dir.mkdir(parents=True, exist_ok=True)
    archive = data_dir / '50pair.zip'
    if not archive.exists():
        temporary = data_dir / '50pair.zip.part'
        print('Downloading official WDC archive (about 22 MB)...', flush=True)
        try:
            with urlopen(URL, timeout=60) as source, temporary.open('wb') as target:
                shutil.copyfileobj(source, target)
            if checksum(temporary) != SHA256:
                raise ValueError('Downloaded archive checksum differs from the pinned version.')
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    if checksum(archive) != SHA256:
        raise ValueError(f'Archive checksum mismatch: {archive}. Move it aside and retry.')
    with zipfile.ZipFile(archive) as bundle:
        for name in FILES.values():
            # Fixed basenames avoid extracting arbitrary archive paths.
            payload = bundle.read(name)
            target = data_dir / name
            if not target.exists() or target.read_bytes() != payload:
                temporary = target.with_suffix('.part')
                temporary.write_bytes(payload)
                temporary.replace(target)
    print(f'Archive verified. Five selected split files ready in {data_dir}')


def load_pairs(path):
    """Read gzip JSON Lines without changing labels, text, or missing values."""
    rows = []
    pair_ids = set()
    with gzip.open(path, 'rt', encoding='utf-8') as source:
        for number, line in enumerate(source, 1):
            row = json.loads(line)
            required = {'pair_id', 'label', 'id_left', 'id_right',
                        'title_left', 'title_right'}
            if not isinstance(row, dict) or not required.issubset(row):
                raise ValueError(f'{path.name}:{number}: missing required pair fields')
            if type(row['label']) is not int or row['label'] not in (0, 1):
                raise ValueError(f'{path.name}:{number}: label must be 0 or 1')
            if any(type(row[f'id_{side}']) is not int for side in ('left', 'right')):
                raise ValueError(f'{path.name}:{number}: offer IDs must be integers')
            expected = f"{row['id_left']}#{row['id_right']}"
            if row['pair_id'] != expected:
                raise ValueError(f'{path.name}:{number}: inconsistent pair_id')
            if row['pair_id'] in pair_ids:
                raise ValueError(f'{path.name}:{number}: duplicate pair_id')
            pair_ids.add(row['pair_id'])
            rows.append(row)
    if not rows:
        raise ValueError(f'{path.name}: empty dataset')
    return rows


def inspect_training(data_dir, examples):
    rows = load_pairs(data_dir / FILES['train'])
    counts = Counter(row['label'] for row in rows)
    if (len(rows), counts[1], counts[0]) != (2500, 500, 2000):
        raise ValueError('Training counts differ from the selected official small split.')
    print(f'Training pairs: {len(rows):,}')
    print(f'Benchmark matches (1): {counts[1]:,}')
    print(f'Benchmark non-matches (0): {counts[0]:,}')
    print('Fields: ' + ', '.join(rows[0]))
    # Alternate labels so a short preview includes both classes, in stable order.
    groups = {label: iter([row for row in rows if row['label'] == label])
              for label in (0, 1)}
    print('\nTraining examples — benchmark labels, not model predictions:')
    for i in range(examples):
        row = next(groups[i % 2], None)
        if row is None:
            break
        label = 'Match' if row['label'] else 'Different'
        print(f"\n{i + 1}. {row['pair_id']} | benchmark label: {label}")
        print(f"   Left:  {row['title_left']}")
        print(f"   Right: {row['title_right']}")
    print('\nValidation and test examples were not previewed. No model was trained.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true',
                        help='Download/verify the archive and prepare selected splits.')
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument('--examples', type=int, default=4, choices=range(0, 11),
                        metavar='0..10', help='Number of training examples (default: 4).')
    args = parser.parse_args()
    try:
        if args.download:
            prepare(args.data_dir)
        inspect_training(args.data_dir, args.examples)
    except FileNotFoundError:
        parser.exit(1, 'Data not found. Run: python scripts/wdc_data.py --download\n')
    except (OSError, ValueError, URLError, zipfile.BadZipFile, KeyError, EOFError) as error:
        parser.exit(1, f'Data error: {error}\n')


if __name__ == '__main__':
    main()
