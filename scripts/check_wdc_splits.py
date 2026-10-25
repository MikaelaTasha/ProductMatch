"""Check pinned file hashes and offer-ID overlap without displaying test examples."""
import json

from scripts.wdc_data import DEFAULT_DATA_DIR, FILES, ROOT, checksum, load_pairs


def main():
    manifest = json.loads((ROOT / 'docs/dataset-manifest.json').read_text())
    offers = {}
    for split, filename in FILES.items():
        path = DEFAULT_DATA_DIR / filename
        expected = manifest['splits'][split]
        if checksum(path) != expected['sha256']:
            raise ValueError(f'{split}: file hash differs from recorded download')
        rows = load_pairs(path)
        offers[split] = {row[f'id_{side}'] for row in rows for side in ('left', 'right')}
        measured = {'pairs': len(rows), 'matches': sum(row['label'] for row in rows),
                    'non_matches': sum(1 - row['label'] for row in rows),
                    'unique_offers': len(offers[split])}
        if any(expected[key] != value for key, value in measured.items()):
            raise ValueError(f'{split}: counts differ from recorded download')
        print(f'{split}: hash and counts verified ({len(rows):,} pairs)')
    print('\nShared offer IDs (structural audit only):')
    comparisons = [('train', 'validation')]
    comparisons += [(development, test) for development in ('train', 'validation')
                    for test in ('test_seen', 'test_half_unseen', 'test_unseen')]
    overlaps = []
    for left, right in comparisons:
        count = len(offers[left] & offers[right])
        overlaps.append(count)
        print(f'  {left} / {right}: {count}')
    if any(overlaps):
        print('WARNING: overlap found. See docs/dataset.md before evaluation.')
    print('No predictions or performance metrics were computed.')


if __name__ == '__main__':
    main()
