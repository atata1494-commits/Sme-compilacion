"""Pruebas automáticas del esquema SQLite propuesto para SME.
Usa únicamente sqlite3 de la biblioteca estándar y datos sintéticos.
"""
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "SQLITE_SCHEMA.sql"

REQUIRED_TABLES = {
    "schema_migrations", "app_metadata", "clientes", "vehiculos", "trabajos",
    "presupuestos", "movimientos", "eventos", "recepciones", "diagnosticos",
    "cuentas", "pagos_cuenta", "adjuntos", "cambios_sync", "cambios_recibidos",
    "asistencias", "terceros", "trabajos_externos", "config_horarios",
    "paquetes_intercambio", "conflictos_sync",
}


class SQLiteSchemaTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript(SCHEMA.read_text(encoding="utf-8"))

    def tearDown(self):
        self.connection.close()

    def test_all_tables_exist_and_schema_version_is_one(self):
        tables = {
            row[0] for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertTrue(REQUIRED_TABLES.issubset(tables))
        self.assertEqual(self.connection.execute("PRAGMA user_version").fetchone()[0], 2)
        metadata = dict(self.connection.execute("SELECT key, value FROM app_metadata"))
        self.assertEqual(metadata["schema_version"], "2")
        self.assertEqual(metadata["currency"], "ARS")

    def test_schema_can_be_applied_twice(self):
        self.connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(self.connection.execute("PRAGMA user_version").fetchone()[0], 2)

    def test_synthetic_records_and_cents_are_stored(self):
        self.connection.execute(
            "INSERT INTO clientes(id, nombre, payload_json) VALUES (?, ?, ?)",
            ("legacy:101", "Cliente de prueba", '{"id":101,"nombre":"Cliente de prueba"}'),
        )
        self.connection.execute(
            "INSERT INTO movimientos(id, fecha, tipo, concepto, importe_centavos, payload_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("test-movement-1", "2026-10-13", "Ingreso", "Prueba sintética", 123456,
             '{"importe":"1234,56"}'),
        )
        self.connection.execute(
            "INSERT INTO adjuntos(id, entidad_tipo, entidad_id, campo, mime_type, datos, "
            "sha256_hex) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test-photo-1", "recepciones", "test-reception-1", "fotos[0]",
             "image/jpeg", sqlite3.Binary(b"synthetic-image-bytes"), "synthetic-hash"),
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT importe_centavos FROM movimientos WHERE id='test-movement-1'"
            ).fetchone()[0],
            123456,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT datos FROM adjuntos WHERE id='test-photo-1'"
            ).fetchone()[0],
            b"synthetic-image-bytes",
        )

    def test_primary_keys_prevent_duplicate_change_import(self):
        self.connection.execute(
            "INSERT INTO cambios_recibidos(change_id, package_id, dispositivo_origen, aplicado_at_utc) "
            "VALUES ('change-1', 'package-1', 'device-A', '2026-10-13T00:00:00Z')"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO cambios_recibidos(change_id, package_id, dispositivo_origen, aplicado_at_utc) "
                "VALUES ('change-1', 'package-2', 'device-A', '2026-10-13T00:00:00Z')"
            )

    def test_expected_indexes_exist(self):
        indexes = {
            row[0] for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
        }
        for index in (
            "idx_vehiculos_cliente", "idx_trabajos_cliente",
            "idx_movimientos_fecha", "idx_pagos_cuenta_cuenta_fecha",
            "idx_adjuntos_entidad", "idx_cambios_sync_estado",
        ):
            self.assertIn(index, indexes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
