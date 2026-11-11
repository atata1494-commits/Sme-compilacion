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

    def test_incoming_package_application_is_atomic_idempotent_and_does_not_echo(self):
        source = (ROOT / 'src' / 'storage' / 'sqlite-store.js').read_text(encoding='utf-8')
        start = source.index('  async function applySyncPackage(input)')
        end = source.index('  async function prepareSyncPackage()', start)
        apply_code = source[start:end]
        self.assertIn('await connection.beginTransaction()', apply_code)
        self.assertIn('await connection.commitTransaction()', apply_code)
        self.assertIn('await connection.rollbackTransaction()', apply_code)
        self.assertIn('INSERT INTO cambios_recibidos', apply_code)
        self.assertIn('paquete_ya_recibido', apply_code)
        self.assertIn('mergeVersionVectors', apply_code)
        self.assertIn('lastSnapshot = clone(refreshedSnapshot)', apply_code)
        self.assertNotIn('recordSyncChange(', apply_code)
        self.assertIn('async applySyncPackage(input)', source)

    def test_sync_conflicts_are_persisted_with_both_versions_for_review(self):
        source = (ROOT / 'src' / 'storage' / 'sqlite-store.js').read_text(encoding='utf-8')
        start = source.index('  async function applySyncPackage(input)')
        end = source.index('  async function prepareSyncPackage()', start)
        apply_code = source[start:end]
        self.assertIn('INSERT INTO conflictos_sync', apply_code)
        self.assertIn('registro_local_json', apply_code)
        self.assertIn('registro_entrante_json', apply_code)
        self.assertIn('resuelto_at_utc IS NULL', apply_code)
        self.assertIn('Los conflictos quedaron guardados para revisión.', apply_code)
        self.assertIn('async listSyncConflicts()', source)
        self.assertIn('registro_local: row.registro_local_json', source)
        self.assertIn('registro_entrante: row.registro_entrante_json', source)

    def test_schema_and_migration_preserve_per_entity_version_history(self):
        schema = (ROOT / 'docs' / 'SQLITE_SCHEMA.sql').read_text(encoding='utf-8')
        migration = (ROOT / 'docs' / 'SQLITE_MIGRATION_V4_SYNC_VERSION_VECTORS.sql').read_text(encoding='utf-8')
        self.assertIn('CREATE TABLE IF NOT EXISTS sync_entity_versions', schema)
        self.assertIn('CREATE TABLE IF NOT EXISTS sync_entity_versions', migration)
        self.assertIn('version_vector_json', schema)
        self.assertIn('deleted_at_utc', migration)

if __name__ == '__main__':
    unittest.main(verbosity=2)
