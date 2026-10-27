"""Protect metadata-only overlap accounting and validation error summaries."""
from pathlib import Path
import tempfile
import unittest

from scripts.audit_day12 import split_audit, validation_audit
from scripts.import_data import connect_database, import_batches
from test_import_data import batch, pair


class AuditTests(unittest.TestCase):
    def test_unordered_pairs_clusters_and_development_union(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.sqlite3'
            db=connect_database(path)
            val=pair(3,4)
            val['cluster_id_left'],val['cluster_id_right']=1,2
            import_batches(db,[batch([pair()]),batch([val],'validation'),
                               batch([pair(2,1)],'test_half_unseen')])
            db.close()
            before=path.read_bytes()
            report=split_audit(path)
            by_pair={(r['left'],r['right']):r for r in report['overlaps']}
            overlap=by_pair[('test_half_unseen','train')]
            self.assertEqual(overlap['shared_pairs'],1)
            self.assertEqual(overlap['shared_offers'],2)
            self.assertEqual(by_pair[('train','validation')]['shared_clusters'],2)
            self.assertEqual(by_pair[('train','validation')]['shared_offers'],0)
            self.assertEqual(report['splits']['test_half_unseen']['pairs_touching_development_offers'],1)
            self.assertEqual(path.read_bytes(),before)
            db=connect_database(path)
            db.execute("UPDATE listings SET title='changed text', description='changed'")
            db.execute('UPDATE labeled_pairs SET label=1-label')
            db.commit()
            db.close()
            self.assertEqual(split_audit(path),report)

    def test_missing_listing_fails_instead_of_disappearing(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.sqlite3'
            db=connect_database(path)
            import_batches(db,[batch([pair()])])
            db.execute('PRAGMA foreign_keys=OFF')
            db.execute('DELETE FROM listings WHERE listing_id=1')
            db.commit()
            db.close()
            with self.assertRaisesRegex(ValueError,'Missing listing'):
                split_audit(path)

    def test_validation_error_counts_and_samples_without_test_splits(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.sqlite3'
            db=connect_database(path)
            import_batches(db,[batch([pair(1,2,1),pair(3,4,0)]),
                               batch([pair(5,6,1),pair(7,8,0)],'validation')])
            db.close()
            before=path.read_bytes()
            report,samples=validation_audit(path)
            self.assertEqual(before,path.read_bytes())
            self.assertEqual(report['error_slices']['binary_false_match']['pairs'],
                             report['binary_metrics']['false_positives'])
            self.assertEqual(report['error_slices']['binary_missed_match']['pairs'],
                             report['binary_metrics']['false_negatives'])
            for item in report['error_slices'].values():
                for counts in item['evidence_counts'].values():
                    self.assertEqual(sum(counts.values()),item['pairs'])
            for rows in samples.values():
                self.assertTrue(all(r['pair_id'] in ('5#6','7#8') for r in rows))
            self.assertEqual((report,samples),validation_audit(path))


if __name__=='__main__':
    unittest.main()
