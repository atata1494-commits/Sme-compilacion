"""Regression checks for incremental sync package preparation.

These checks validate schema and integration shape. Runtime tests on a real
Capacitor SQLite device and package round-trip tests are still required.
"""
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "SQLITE_SCHEMA.sql"
STORE = ROOT / "src" / "storage" / "sqlite-store.js"


class SQLiteSyncPackageTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))
        self.source = STORE.read_text(encoding="utf-8")

    def tearDown(self):
        self.db.close()

    def test_exchange_table_records_package_metadata(self):
        columns = {
            row[1] for row in self.db.execute("PRAGMA table_info(paquetes_intercambio)")
        }
        self.assertTrue({
            "package_id", "dispositivo_origen", "creado_at_utc",
            "version_esquema", "tipo", "sha256_hex", "estado",
        }.issubset(columns))

        self.db.execute(
            """INSERT INTO paquetes_intercambio
            (package_id, dispositivo_origen, creado_at_utc, version_esquema,
             tipo, sha256_hex, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("pkg-1", "device-1", "2026-10-20T12:00:00Z", 1,
             "incremental", "a" * 64, "preparado"),
        )
        row = self.db.execute(
            "SELECT tipo, estado, length(sha256_hex) FROM paquetes_intercambio WHERE package_id = ?",
            ("pkg-1",),
        ).fetchone()
        self.assertEqual(row, ("incremental", "preparado", 64))

    def test_storage_exposes_package_preparation_api(self):
        self.assertIn("async function prepareSyncPackage()", self.source)
        self.assertIn("async prepareSyncPackage()", self.source)
        self.assertIn("formato: 'SME_SYNC_PACKAGE'", self.source)
        self.assertIn("version_formato: 1", self.source)
        self.assertIn("sha256_hex: hash", self.source)
        self.assertIn("WHERE estado = 'pendiente'", self.source)
        self.assertIn("ORDER BY fecha_utc, change_id", self.source)

    def test_package_persists_hash_and_metadata_before_returning(self):
        start = self.source.index("async function prepareSyncPackage()")
        end = self.source.index("\n  async function recordSyncChange(", start)
        body = self.source[start:end]
        self.assertIn("await sha256Hex(JSON.stringify(unsignedPackage))", body)
        self.assertIn("INSERT INTO paquetes_intercambio", body)
        self.assertLess(body.index("await connection.beginTransaction()"),
                        body.index("await connection.commitTransaction()"))
        self.assertIn("await connection.rollbackTransaction()", body)

    def test_package_creation_waits_for_queued_saves(self):
        self.assertIn("await saveQueue;\n      return prepareSyncPackage();", self.source)

    def test_import_validation_is_non_mutating_and_checks_integrity(self):
        start = self.source.index("async function validateSyncPackage(input)")
        end = self.source.index("  async function prepareSyncPackage()", start)
        body = self.source[start:end]
        self.assertIn("pkg.formato !== 'SME_SYNC_PACKAGE'", body)
        self.assertIn("pkg.version_formato !== 1", body)
        self.assertIn("await sha256Hex(JSON.stringify(unsignedPackage))", body)
        self.assertIn("El paquete contiene identificadores de cambio duplicados.", body)
        self.assertIn("El contenido del cambio no coincide con su identificador.", body)
        self.assertIn("No se aplicaron cambios a la base local.", body)
        self.assertNotIn("connection.beginTransaction()", body)
        self.assertIn("async validateSyncPackage(input)", self.source)
        self.assertIn("async function inspectSyncPackage(input)", self.source)
        self.assertIn("cambios_recibidos WHERE change_id = ?", self.source)
        self.assertIn("La revisión local cambió desde la revisión base del paquete.", self.source)
        self.assertIn("No se aplicaron cambios ni se modificó la base local.", self.source)
        self.assertIn("async inspectSyncPackage(input)", self.source)
        self.assertIn("SELECT package_id FROM cambios_recibidos WHERE package_id = ? LIMIT 1", self.source)
        self.assertIn("El paquete contiene más de un cambio para el mismo registro", self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
