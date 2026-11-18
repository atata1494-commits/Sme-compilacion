-- SME SQLite migration v5: pedidos rápidos de repuestos.
-- Los pedidos quedan como registros propios, exportables y sincronizables.
CREATE TABLE IF NOT EXISTS sme_pedidos_repuestos (
  id TEXT PRIMARY KEY,
  titulo TEXT NOT NULL,
  cliente_id TEXT,
  vehiculo_id TEXT,
  trabajo_id TEXT,
  estado TEXT NOT NULL DEFAULT 'pendiente',
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_sme_pedidos_repuestos_estado
  ON sme_pedidos_repuestos(estado, created_at_utc);
INSERT OR IGNORE INTO schema_migrations(version, applied_at_utc, description)
VALUES (5, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), 'Pedidos rápidos de repuestos');
INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('schema_version', '5');
PRAGMA user_version = 5;
