"""Symmetric, label-free comparisons of uncertain title evidence."""
from productmatch.attributes import EXTRACTION_VERSION, extract_title_attributes

FEATURE_VERSION = 'attribute-comparisons-v1'
STATES = ('missing_both', 'missing_one', 'ambiguous', 'agrees', 'differs')
FIELDS = ('model_candidate', 'storage_mention', 'storage_per_item', 'storage_total',
          'storage_count', 'volume_mention', 'volume_per_item', 'volume_total',
          'volume_count', 'frequency', 'pack_count', 'sheet_count', 'piece_count', 'module_count')
FEATURE_NAMES = tuple(f'{field}_{state}' for field in FIELDS for state in STATES)


def evidence_values(title):
    evidence = extract_title_attributes(title)
    values = {field: set() for field in FIELDS}
    values['model_candidate'] = {m['normalized'] for m in evidence['model_candidates']}
    for item in evidence['measurements']:
        kind = item['kind']
        field = 'frequency' if kind == 'frequency' else (
            f'{kind}_per_item' if item['role'] == 'per_item' else f'{kind}_mention')
        values[field].add(item['base_value'])
    for item in evidence['pack_candidates']:
        if 'total_base_value' in item:
            values[f"{item['kind']}_total"].add(item['total_base_value'])
            values[f"{item['kind']}_count"].add(item['count'])
        else:
            category = {'pack': 'pack', 'packs': 'pack', 'sheet': 'sheet',
                        'sheets': 'sheet', 'piece': 'piece', 'pieces': 'piece',
                        'pcs': 'piece', 'module': 'module', 'modules': 'module'}[item['kind']]
            values[f'{category}_count'].add(item['count'])
    return values


def compare_values(left, right):
    # Missing takes precedence; do not report conflict from absent evidence.
    if not left and not right:
        return 'missing_both'
    if not left or not right:
        return 'missing_one'
    if len(left) != 1 or len(right) != 1:
        return 'ambiguous'
    return 'agrees' if left == right else 'differs'


def compare_titles(left_title, right_title):
    left, right = evidence_values(left_title), evidence_values(right_title)
    comparisons = {field: {'state': compare_values(left[field], right[field]),
                           'left': sorted(left[field]), 'right': sorted(right[field])}
                   for field in FIELDS}
    numeric = {f'{field}_{state}': int(comparisons[field]['state'] == state)
               for field in FIELDS for state in STATES}
    return {'feature_version': FEATURE_VERSION, 'extraction_version': EXTRACTION_VERSION,
            'comparisons': comparisons, 'features': numeric}
