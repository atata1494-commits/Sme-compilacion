"""Pruebas de la migración SQLite v3 para tareas, avisos y autorizaciones.
Solo usa sqlite3 estándar y datos sintéticos. No modifica la app en ejecución.
"""
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "docs" / "SQLITE_SCHEMA.sql"
V3 = ROOT / "docs" / "SQLITE_MIGRATION_V3_TAREAS_AVISOS.sql"


class SMEV3MigrationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(V1.read_text(encoding="utf-8"))
        self.db.executescript(V3.read_text(encoding="utf-8"))

    def tearDown(self):
        self.db.close()

    def test_version_and_new_tables(self):
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0], 3)
        metadata = dict(self.db.execute("SELECT key,value FROM app_metadata"))
        self.assertEqual(metadata["schema_version"], "3")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM schema_migrations WHERE version=3").fetchone()[0], 1)
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({
            "sme_tareas", "sme_tarea_eventos", "sme_tarea_dependencias",
            "sme_avisos", "sme_aviso_derivaciones", "sme_solicitudes_gasto",
            "sme_permisos_usuario", "sme_auditoria"
        }.issubset(tables))

    def test_migration_is_idempotent(self):
        self.db.executescript(V3.read_text(encoding="utf-8"))
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0], 3)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM schema_migrations WHERE version=3").fetchone()[0], 1)

    def test_task_and_notice_constraints(self):
        self.db.execute(
            "INSERT INTO sme_tareas(id,titulo,creada_por_usuario_id,created_at_utc,updated_at_utc) VALUES (?,?,?,?,?)",
            ("task-1", "Revisar elevador", "user-supervisor", "2026-10-15T12:00:00Z", "2026-10-15T12:00:00Z"),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO sme_tareas(id,titulo,creada_por_usuario_id,estado,created_at_utc,updated_at_utc) VALUES (?,?,?,?,?,?)",
                ("task-bad", "Estado inválido", "user-1", "terminada-mágicamente", "2026-10-15T12:00:00Z", "2026-10-15T12:00:00Z"),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO sme_avisos(id,titulo,categoria,creado_por_usuario_id,created_at_utc,updated_at_utc) VALUES (?,?,?,?,?,?)",
                ("notice-bad", "Aviso inválido", "categoria-no-permitida", "user-1", "2026-10-15T12:00:00Z", "2026-10-15T12:00:00Z"),
            )

    def test_spend_cannot_be_approved_without_authorizer_and_timestamp(self):
        self.db.execute(
            "INSERT INTO sme_tareas(id,titulo,creada_por_usuario_id,created_at_utc,updated_at_utc) VALUES (?,?,?,?,?)",
            ("task-2", "Comprar repuesto", "user-1", "2026-10-15T12:00:00Z", "2026-10-15T12:00:00Z"),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO sme_solicitudes_gasto(id,tarea_id,solicitante_usuario_id,concepto,estado,created_at_utc,updated_at_utc) VALUES (?,?,?,?,?,?,?)",
                ("spend-bad", "task-2", "user-1", "Filtro", "aprobada", "2026-10-15T12:00:00Z", "2026-10-15T12:00:00Z"),
            )

    def test_audit_history_is_append_only(self):
        self.db.execute(
            "INSERT INTO sme_auditoria(id,entidad_tipo,entidad_id,accion,usuario_id,created_at_utc) VALUES (?,?,?,?,?,?)",
            ("audit-1", "tarea", "task-1", "creada", "user-1", "2026-10-15T12:00:00Z"),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE sme_auditoria SET accion='alterada' WHERE id='audit-1'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM sme_auditoria WHERE id='audit-1'")

    def test_permissions_are_scoped_and_unique(self):
        row = ("perm-1", "user-cleaning", "avisos.crear", "sector", "limpieza", 1, "admin-1",
               "2026-10-15T12:00:00Z", "2026-10-15T12:00:00Z")
        self.db.execute(
            "INSERT INTO sme_permisos_usuario(id,usuario_id,permiso,alcance,sector_id,permitido,otorgado_por_usuario_id,created_at_utc,updated_at_utc) VALUES (?,?,?,?,?,?,?,?,?)",
            row,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO sme_permisos_usuario(id,usuario_id,permiso,alcance,sector_id,permitido,otorgado_por_usuario_id,created_at_utc,updated_at_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                ("perm-2", *row[1:]),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
