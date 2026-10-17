"""Regresión para la migración v3 y tablas heredadas de SME."""
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "SQLITE_SCHEMA.sql"
MIGRATION_V3 = ROOT / "docs" / "SQLITE_MIGRATION_V3_TAREAS_AVISOS.sql"


class SQLiteMigrationV3Tests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))

    def tearDown(self):
        self.db.close()

    def _apply_runtime_revision_compatibility(self):
        # El código de almacenamiento de la app agrega revision a tablas
        # creadas por versiones previas; la migración SQL por sí sola no lo hace.
        for table in ("sme_tareas", "sme_avisos", "sme_solicitudes_gasto"):
            columns = {
                row[1] for row in self.db.execute(f"PRAGMA table_info({table})")
            }
            if "revision" not in columns:
                self.db.execute(
                    f"ALTER TABLE {table} "
                    "ADD COLUMN revision INTEGER NOT NULL DEFAULT 1"
                )

    def test_v3_creates_generic_storage_columns(self):
        self.db.executescript(MIGRATION_V3.read_text(encoding="utf-8"))
        self._apply_runtime_revision_compatibility()
        for table in ("sme_tareas", "sme_avisos", "sme_solicitudes_gasto"):
            columns = {
                row[1] for row in self.db.execute(f"PRAGMA table_info({table})")
            }
            self.assertIn("id", columns, table)
            self.assertIn("payload_json", columns, table)
            self.assertIn("revision", columns, table)
            self.assertIn("updated_at_utc", columns, table)

    def test_legacy_expense_table_gets_revision_without_losing_data(self):
        # Simula una instalación anterior: la tabla ya existe, pero no tiene
        # revision. CREATE TABLE IF NOT EXISTS no puede reparar esa columna.
        self.db.execute("""
            CREATE TABLE sme_solicitudes_gasto (
                id TEXT PRIMARY KEY,
                estado TEXT,
                created_at_utc TEXT,
                updated_at_utc TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}'
            )
        """)
        original_payload = '{"id":"gasto-antiguo","concepto":"Repuesto","importe":1250}'
        self.db.execute(
            """INSERT INTO sme_solicitudes_gasto
               (id, estado, created_at_utc, updated_at_utc, payload_json)
               VALUES (?, ?, ?, ?, ?)""",
            ("gasto-antiguo", "pendiente", "2026-10-15T10:00:00Z",
             "2026-10-15T10:00:00Z", original_payload),
        )

        self.db.executescript(MIGRATION_V3.read_text(encoding="utf-8"))
        self._apply_runtime_revision_compatibility()

        row = self.db.execute(
            "SELECT payload_json, revision FROM sme_solicitudes_gasto "
            "WHERE id = 'gasto-antiguo'"
        ).fetchone()
        self.assertEqual(row, (original_payload, 1))

    def test_v3_migration_is_idempotent(self):
        migration = MIGRATION_V3.read_text(encoding="utf-8")
        self.db.executescript(migration)
        self.db.executescript(migration)
        self.assertEqual(
            self.db.execute("PRAGMA user_version").fetchone()[0], 3
        )
        self.assertEqual(
            self.db.execute(
                "SELECT COUNT(*) FROM schema_migrations WHERE version = 3"
            ).fetchone()[0],
            1,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
