"""Pruebas de la migración SQLite v5 de pedidos rápidos de repuestos."""
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "SQLITE_SCHEMA.sql"
MIGRATION = ROOT / "docs" / "SQLITE_MIGRATION_V5_PEDIDOS_REPUESTOS.sql"


class SQLiteMigrationV5Tests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript(SCHEMA.read_text(encoding="utf-8"))

    def tearDown(self):
        self.connection.close()

    def test_v5_creates_persistent_reusable_parts_orders(self):
        self.connection.executescript(MIGRATION.read_text(encoding="utf-8"))
        columns = {row[1] for row in self.connection.execute(
            "PRAGMA table_info(sme_pedidos_repuestos)"
        )}
        self.assertTrue({"id", "titulo", "cliente_id", "vehiculo_id", "trabajo_id",
                         "estado", "created_at_utc", "payload_json", "revision"}.issubset(columns))
        self.assertEqual(self.connection.execute("PRAGMA user_version").fetchone()[0], 5)
        self.assertEqual(dict(self.connection.execute(
            "SELECT key, value FROM app_metadata"
        ))["schema_version"], "5")

    def test_v5_migration_is_idempotent_and_preserves_saved_order(self):
        self.connection.executescript(MIGRATION.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO sme_pedidos_repuestos "
            "(id, titulo, estado, created_at_utc, payload_json) VALUES (?, ?, ?, ?, ?)",
            ("parts-1", "Pedido prueba", "pendiente", "2026-11-18T12:00:00Z",
             '{"id":"parts-1","items":["Bieleta"]}'),
        )
        self.connection.executescript(MIGRATION.read_text(encoding="utf-8"))
        row = self.connection.execute(
            "SELECT titulo, payload_json FROM sme_pedidos_repuestos WHERE id='parts-1'"
        ).fetchone()
        self.assertEqual(row[0], "Pedido prueba")
        self.assertIn("Bieleta", row[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
