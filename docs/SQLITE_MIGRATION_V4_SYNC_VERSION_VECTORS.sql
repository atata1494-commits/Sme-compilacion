-- SME SQLite migration v4: per-record version vectors for safe synchronization.
-- Re-runnable on every app start; preserves existing records and change history.
CREATE TABLE IF NOT EXISTS sync_entity_versions (
  entidad_tipo TEXT NOT NULL,
  entidad_id TEXT NOT NULL,
  version_vector_json TEXT NOT NULL DEFAULT '{}',
  deleted_at_utc TEXT,
  updated_at_utc TEXT NOT NULL,
  PRIMARY KEY (entidad_tipo, entidad_id)
);
CREATE INDEX IF NOT EXISTS idx_sync_entity_versions_deleted
  ON sync_entity_versions(deleted_at_utc);
INSERT OR IGNORE INTO schema_migrations(version, applied_at_utc, description)
VALUES (4, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), 'Versionado causal por dispositivo para sincronización segura');
INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('schema_version', '4');
PRAGMA user_version = 4;
