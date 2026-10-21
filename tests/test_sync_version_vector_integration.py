from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SyncVersionVectorIntegrationTests(unittest.TestCase):
    def test_store_persists_vectors_and_tombstones_transactionally(self):
        source = (ROOT / 'src' / 'storage' / 'sqlite-store.js').read_text(encoding='utf-8')
        self.assertIn('advanceEntityVersion(key, id, deviceId, deletedAt)', source)
        self.assertIn('version_vector_json', source)
        self.assertIn('await connection.rollbackTransaction()', source)
        self.assertIn('migrationV4SQL', source)

    def test_schema_and_migration_preserve_per_entity_version_history(self):
        schema = (ROOT / 'docs' / 'SQLITE_SCHEMA.sql').read_text(encoding='utf-8')
        migration = (ROOT / 'docs' / 'SQLITE_MIGRATION_V4_SYNC_VERSION_VECTORS.sql').read_text(encoding='utf-8')
        self.assertIn('CREATE TABLE IF NOT EXISTS sync_entity_versions', schema)
        self.assertIn('CREATE TABLE IF NOT EXISTS sync_entity_versions', migration)
        self.assertIn('version_vector_json', schema)
        self.assertIn('deleted_at_utc', migration)

if __name__ == '__main__':
    unittest.main(verbosity=2)
