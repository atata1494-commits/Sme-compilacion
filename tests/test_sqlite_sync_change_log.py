"""Regression checks for the first local change-log integration.

These checks complement (but do not replace) runtime tests on a real Capacitor
SQLite connection and end-to-end synchronization tests.
"""
from pathlib import Path
import re
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "SQLITE_SCHEMA.sql"
STORE = ROOT / "src" / "storage" / "sqlite-store.js"


class SQLiteSyncChangeLogTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))
        self.source = STORE.read_text(encoding="utf-8")

    def tearDown(self):
        self.db.close()

    def test_change_log_supports_pending_insert_update_and_delete_records(self):
        columns = {
            row[1] for row in self.db.execute("PRAGMA table_info(cambios_sync)")
        }
        self.assertTrue({
            "change_id", "entidad_tipo", "entidad_id", "operacion",
            "revision_base", "revision", "dispositivo_id", "fecha_utc",
            "payload_json", "estado",
        }.issubset(columns))

        changes = [
            ("c1", "clientes", "client-1", "INSERT", 0, 1, "device-a", "2026-10-20T12:00:00Z", '{"id":"client-1"}', "pendiente"),
            ("c2", "clientes", "client-1", "UPDATE", 1, 2, "device-a", "2026-10-20T12:01:00Z", '{"id":"client-1","nombre":"Actualizado"}', "pendiente"),
            ("c3", "clientes", "client-1", "DELETE", 2, 3, "device-a", "2026-10-20T12:02:00Z", '{"id":"client-1","deletedAt":"2026-10-20T12:02:00Z"}', "pendiente"),
        ]
        self.db.executemany(
            """INSERT INTO cambios_sync
            (change_id, entidad_tipo, entidad_id, operacion, revision_base,
             revision, dispositivo_id, fecha_utc, payload_json, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            changes,
        )
        self.db.commit()
        rows = self.db.execute(
            "SELECT operacion, revision_base, revision, estado FROM cambios_sync ORDER BY revision"
        ).fetchall()
        self.assertEqual(rows, [
            ("INSERT", 0, 1, "pendiente"),
            ("UPDATE", 1, 2, "pendiente"),
            ("DELETE", 2, 3, "pendiente"),
        ])

    def test_duplicate_change_id_is_rejected(self):
        row = ("same-id", "clientes", "client-1", "INSERT", 0, 1,
               "device-a", "2026-10-20T12:00:00Z", '{"id":"client-1"}', "pendiente")
        sql = """INSERT INTO cambios_sync
            (change_id, entidad_tipo, entidad_id, operacion, revision_base,
             revision, dispositivo_id, fecha_utc, payload_json, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        self.db.execute(sql, row)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, row)

    def test_storage_records_changes_and_uses_a_stable_device_id(self):
        self.assertIn("async function getDeviceId()", self.source)
        self.assertIn("key = 'device_id'", self.source)
        self.assertIn("async function recordSyncChange(", self.source)
        self.assertIn("INSERT INTO cambios_sync", self.source)
        self.assertIn("operation: previous ? 'UPDATE' : 'INSERT'", self.source)
        self.assertIn("operation: 'DELETE'", self.source)
        self.assertIn("estado", self.source)
        self.assertIn("'pendiente'", self.source)

    def test_change_log_write_is_inside_snapshot_transaction(self):
        start = self.source.index("async function persistSnapshot(snapshot)")
        end = self.source.index("\n  return {\n    isNative: true,", start)
        transaction_body = self.source[start:end]
        self.assertLess(transaction_body.index("await connection.beginTransaction()"),
                        transaction_body.index("await recordSyncChange("))
        self.assertLess(transaction_body.index("await recordSyncChange("),
                        transaction_body.index("await connection.commitTransaction()"))
        self.assertIn("await connection.rollbackTransaction()", transaction_body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
