"""Extract explicit title evidence; candidates are not verified product identity."""
import re

EXTRACTION_VERSION = 'title-attributes-v1'
NUMBER = r'\d+(?:\.\d+)?'
# Avoid matching suffixes of codes, comma-decimal numbers or signed quantities.
MEASUREMENT = re.compile(
    rf'(?<![\w.,+\-])(?P<value>{NUMBER})\s*(?P<unit>TB|GB|ml|l|MHz|GHz)(?![\w/])', re.I)
PACK = re.compile(
    rf'(?<![\w.,+\-])(?P<count>\d+)\s*[x×]\s*(?P<value>{NUMBER})\s*'
    r'(?P<unit>TB|GB|ml|l)(?![\w/])', re.I)
COUNT = re.compile(r'(?<![\w.,+\-])(?P<count>\d+)\s*[- ]?\s*'
                   r'(?P<kind>packs?|sheets?|pieces?|pcs|modules?)(?!\w)', re.I)
TOKEN = re.compile(r'(?<!\w)[A-Za-z0-9]+(?:[-/.][A-Za-z0-9]+)*(?!\w)')
STANDARD = re.compile(r'(?:ddr\d+[a-z]*|cl\d+|\d+k|\d+bit|\d+pin)', re.I)
UNITS = {'gb': ('storage', 'GB', 1), 'tb': ('storage', 'GB', 1000),
         'ml': ('volume', 'ml', 1), 'l': ('volume', 'ml', 1000),
         'mhz': ('frequency', 'MHz', 1), 'ghz': ('frequency', 'MHz', 1000)}


def measurement(value, unit):
    kind, base_unit, factor = UNITS[unit.lower()]
    return {'kind': kind, 'value': float(value), 'unit': unit,
            'base_value': float(value) * factor, 'base_unit': base_unit}


def extract_title_attributes(title):
    if title is not None and not isinstance(title, str):
        raise TypeError('title must be a string or None')
    text = title or ''
    result = {'extraction_version': EXTRACTION_VERSION, 'source': 'title',
              'model_candidates': [], 'measurements': [], 'pack_candidates': []}
    occupied = []
    for match in PACK.finditer(text):
        # Mixed-case Gb/Tb explicitly denote bits, not bytes; skip rather than convert.
        if match['unit'] in ('Gb', 'Tb'):
            continue
        count = int(match['count'])
        if count <= 0 or float(match['value']) <= 0:
            continue
        item = measurement(match['value'], match['unit'])
        result['pack_candidates'].append({'raw': match[0], 'count': count,
            'kind': item['kind'], 'per_item_base_value': item['base_value'],
            'total_base_value': count * item['base_value'], 'base_unit': item['base_unit']})
        # Per-item evidence is separate from total; do not infer that both are conflicts.
        result['measurements'].append({'raw': match[0], 'role': 'per_item', **item})
        occupied.append(match.span())
    for match in MEASUREMENT.finditer(text):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        if match['unit'] in ('Gb', 'Tb') or float(match['value']) <= 0:
            continue
        result['measurements'].append({'raw': match[0], 'role': 'unspecified',
                                      **measurement(match['value'], match['unit'])})
        occupied.append(match.span())
    for match in COUNT.finditer(text):
        if int(match['count']) > 0:
            result['pack_candidates'].append({'raw': match[0], 'count': int(match['count']),
                                             'kind': match['kind'].lower()})
            occupied.append(match.span())
    seen = set()
    for match in TOKEN.finditer(text):
        token = match[0]
        if any(start < match.end() and match.start() < end for start,end in occupied):
            continue
        if not (re.search('[A-Za-z]', token) and re.search('[0-9]', token)):
            continue
        if STANDARD.fullmatch(token) or token.lower() in seen:
            continue
        # Unrecognized measurements and rate tokens should not masquerade as models.
        if re.fullmatch(r'\d+(?:\.\d+)?(?:gb|tb|ml|l|mhz|ghz|mbps|gbps|w|v|mm|cm)(?:/s)?', token, re.I):
            continue
        seen.add(token.lower())
        result['model_candidates'].append({'raw': token, 'normalized': token.lower()})
    result['missing'] = {
        'title': not text.strip(),
        'model_candidate': not result['model_candidates'],
        'storage': not any(m['kind']=='storage' for m in result['measurements']),
        'volume': not any(m['kind']=='volume' for m in result['measurements']),
        'frequency': not any(m['kind']=='frequency' for m in result['measurements']),
        'explicit_pack': not result['pack_candidates'],
    }
    return result
