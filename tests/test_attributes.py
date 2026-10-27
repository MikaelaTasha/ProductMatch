"""Check explicit evidence without treating candidates as product identity."""
import unittest

from productmatch.attributes import extract_title_attributes as extract


class AttributeTests(unittest.TestCase):
    def test_teaching_example(self):
        result = extract('Kingston HyperX HX316C10F/8 DDR3 2x8GB 1600MHz')
        self.assertEqual(result['model_candidates'], [
            {'raw': 'HX316C10F/8', 'normalized': 'hx316c10f/8'}])
        pack = result['pack_candidates'][0]
        self.assertEqual((pack['count'], pack['per_item_base_value'],
                          pack['total_base_value'], pack['base_unit']), (2, 8, 16, 'GB'))
        self.assertEqual([(m['kind'], m['base_value']) for m in result['measurements']],
                         [('storage', 8), ('frequency', 1600)])

    def test_decimal_unit_conversion(self):
        result = extract('1.5L 2TB 3.2GHz')
        self.assertEqual([m['base_value'] for m in result['measurements']],
                         [1500, 2000, 3200])

    def test_total_and_per_item_are_separate(self):
        result = extract('16GB (2×8GB)')
        self.assertEqual(result['pack_candidates'][0]['total_base_value'], 16)
        self.assertEqual({(m['role'], m['base_value']) for m in result['measurements']},
                         {('per_item', 8), ('unspecified', 16)})

    def test_missing_does_not_mean_one(self):
        result = extract('8GB memory multipack')
        self.assertTrue(result['missing']['explicit_pack'])
        self.assertFalse(result['missing']['storage'])
        self.assertEqual(result['pack_candidates'], [])
        self.assertTrue(all(extract(None)['missing'].values()))
        self.assertTrue(all(extract('  ')['missing'].values()))

    def test_dimensions_are_not_pack_counts(self):
        for title in ('tire 29 x 2.4', 'filter 30,7 x 48,5', 'box 2x8cm'):
            self.assertEqual(extract(title)['pack_candidates'], [])

    def test_codes_and_rates_are_not_capacities(self):
        result = extract('CMK16GX4M1A2400C16 HX316C10F/8 8GB/s 16Gb DDR3 CL10')
        self.assertEqual(result['measurements'], [])
        self.assertEqual([m['raw'] for m in result['model_candidates']],
                         ['CMK16GX4M1A2400C16', 'HX316C10F/8'])

    def test_counts_and_volume_packs(self):
        result = extract('2-pack 20 sheets 3 x 1.5L')
        self.assertEqual([p['count'] for p in result['pack_candidates']], [3, 2, 20])
        self.assertEqual(result['pack_candidates'][0]['total_base_value'], 4500)

    def test_multiple_codes_remain_unverified_candidates(self):
        result = extract('AB-12 compatible with XY-34 ab-12')
        self.assertEqual([m['normalized'] for m in result['model_candidates']],
                         ['ab-12', 'xy-34'])
        self.assertNotIn('model', result)

    def test_invalid_quantities_and_types(self):
        for title in ('-8GB', '+8GB', '1,5L', '0GB', '0x8GB'):
            self.assertEqual(extract(title)['measurements'], [])
        with self.assertRaises(TypeError):
            extract(123)


if __name__ == '__main__':
    unittest.main()
