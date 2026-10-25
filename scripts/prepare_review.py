"""Prepare a repeatable local worksheet of 30 training pairs for human review."""
import json
import random
from pathlib import Path

from scripts.wdc_data import ROOT, DEFAULT_DATA_DIR, FILES, checksum, load_pairs

OUTPUT = ROOT / 'data' / 'reviews' / 'day3'
SEED = 42


def select_pairs(rows):
    groups = [
        [r for r in rows if r['label'] == 1],
        [r for r in rows if r['label'] == 0 and r['is_hard_negative']],
        [r for r in rows if r['label'] == 0 and not r['is_hard_negative']],
    ]
    rng = random.Random(SEED)
    chosen = []
    for group in groups:
        chosen.extend(rng.sample(sorted(group, key=lambda r: r['pair_id']), 10))
    rng.shuffle(chosen)
    return chosen


def quote(value):
    text = '(missing)' if value is None or value == '' else str(value)
    # Keep source content as quoted text, not worksheet headings or controls.
    return '\n'.join('> ' + line for line in text.splitlines())


def main():
    source = DEFAULT_DATA_DIR / FILES['train']
    manifest = json.loads((ROOT / 'docs/dataset-manifest.json').read_text())
    if checksum(source) != manifest['splits']['train']['sha256']:
        raise ValueError('Training file differs from the recorded snapshot.')
    rows = select_pairs(load_pairs(source))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    targets = [OUTPUT / name for name in ('worksheet.md', 'answer-key.md', 'selection.json')]
    if any(path.exists() for path in targets):
        raise SystemExit(f'Review files already exist in {OUTPUT}; preserving your notes.')
    worksheet = [
        '# Day 3 — review 30 training pairs\n',
        'Status: 0/30 human decisions recorded. Start with pairs 1–5.\n',
        'Choose **Match**, **Different**, or **Review** (uncertain). Size, model, and '
        'pack quantity must agree when known. Missing details alone are not a mismatch.\n',
        'Record your own decision and evidence before opening `answer-key.md`. '
        'Benchmark labels are not guaranteed truth; do not change the source data.\n',
        'This deliberately balanced learning sample is not representative of class '
        'frequencies and cannot estimate model accuracy.\n',
    ]
    answers = ['# Benchmark answer key\n', 'Open after recording your own judgments.\n']
    for number, row in enumerate(rows, 1):
        worksheet.append(f"## Pair {number} — {row['pair_id']}\n")
        for side in ('left', 'right'):
            worksheet.append(f'### {side.title()} listing\n')
            for field in ('title', 'brand', 'description', 'price', 'priceCurrency'):
                worksheet.append(f'**{field}:**\n\n{quote(row.get(field + "_" + side))}\n')
        worksheet.append('### Your review\n\n- Decision: \n- Evidence: \n'
                         '- Difficulty / missing information: \n'
                         '- Agreement with benchmark (after checking): \n')
        label = 'Match' if row['label'] else 'Different'
        answers.append(f"- Pair {number} (`{row['pair_id']}`): **{label}**\n")
    targets[0].write_text('\n'.join(worksheet), encoding='utf-8')
    targets[1].write_text('\n'.join(answers), encoding='utf-8')
    targets[2].write_text(json.dumps({'seed': SEED, 'source': FILES['train'],
        'source_sha256': checksum(source), 'pair_ids': [r['pair_id'] for r in rows]},
        indent=2) + '\n', encoding='utf-8')
    print(f'Prepared 30 unique training pairs in {OUTPUT}')
    print('Human review is pending. No validation or test data was read.')


if __name__ == '__main__':
    main()
