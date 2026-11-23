"""Tests for the read-only SQLite relationship audit."""
import importlib.util
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sme_rel_audit", ROOT / "scripts" / "audit_sqlite_relationships.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
SCHEMA = ROOT / "docs" / "SQLITE_SCHEMA.sql"

class RelationshipAuditTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))

    def tearDown(self):
        self.db.close()

    def insert_client(self, id):
        self.db.execute("INSERT INTO clientes(id,nombre,payload_json) VALUES(?,?,?)",
                        (id, "Cliente", "{}"))

    def test_valid_optional_relationships_are_not_flagged(self):
        self.insert_client("c1")
        self.db.execute("INSERT INTO vehiculos(id,cliente_id,payload_json) VALUES('v1','c1','{}')")
        self.db.execute("INSERT INTO trabajos(id,cliente_id,vehiculo_id,payload_json) VALUES('w1','c1','v1','{}')")
        self.assertEqual(AUDIT.audit_connection(self.db), [])

    def test_missing_client_vehicle_and_job_references_are_reported(self):
        self.db.execute("INSERT INTO vehiculos(id,cliente_id,payload_json) VALUES('v-orphan','missing-client','{}')")
        self.db.execute("INSERT INTO trabajos(id,cliente_id,vehiculo_id,payload_json) VALUES('w-orphan','missing-client','missing-vehicle','{}')")
        findings = AUDIT.audit_connection(self.db)
        pairs = {(f["source_table"],f["source_id"],f["column"],f["missing_target_id"]) for f in findings}
        self.assertIn(("vehiculos","v-orphan","cliente_id","missing-client"), pairs)
        self.assertIn(("trabajos","w-orphan","cliente_id","missing-client"), pairs)
        self.assertIn(("trabajos","w-orphan","vehiculo_id","missing-vehicle"), pairs)

    def test_missing_payment_account_and_movement_refs_are_reported(self):
        self.db.execute("""INSERT INTO pagos_cuenta(id,cuenta_id,movimiento_id,payload_json)
                          VALUES('p-orphan','missing-account','missing-movement','{}')""")
        findings = AUDIT.audit_connection(self.db)
        pairs = {(f["source_table"],f["source_id"],f["column"],f["missing_target_id"]) for f in findings}
        self.assertIn(("pagos_cuenta","p-orphan","cuenta_id","missing-account"), pairs)
        self.assertIn(("pagos_cuenta","p-orphan","movimiento_id","missing-movement"), pairs)

    def test_missing_spare_parts_request_links_are_reported(self):
        self.db.execute("""INSERT INTO sme_pedidos_repuestos(id,titulo,cliente_id,vehiculo_id,trabajo_id,created_at_utc,payload_json)
                          VALUES('pedido-orphan','Pedido','bad-client','bad-vehicle','bad-job','now','{}' )""")
        findings = AUDIT.audit_connection(self.db)
        pairs = {(f["source_table"],f["source_id"],f["column"],f["missing_target_id"]) for f in findings}
        self.assertIn(("sme_pedidos_repuestos","pedido-orphan","cliente_id","bad-client"), pairs)
        self.assertIn(("sme_pedidos_repuestos","pedido-orphan","vehiculo_id","bad-vehicle"), pairs)
        self.assertIn(("sme_pedidos_repuestos","pedido-orphan","trabajo_id","bad-job"), pairs)

    def test_blank_and_null_optional_references_are_ignored(self):
        self.db.execute("INSERT INTO vehiculos(id,cliente_id,payload_json) VALUES('v-free',NULL,'{}')")
        self.db.execute("INSERT INTO trabajos(id,cliente_id,vehiculo_id,payload_json) VALUES('w-free','','','{}')")
        self.assertEqual(AUDIT.audit_connection(self.db), [])

    def test_audit_is_read_only_and_does_not_rewrite_data(self):
        self.db.execute("INSERT INTO vehiculos(id,cliente_id,payload_json) VALUES('v-orphan','missing','{}')")
        before = self.db.execute("SELECT cliente_id FROM vehiculos WHERE id='v-orphan'").fetchone()
        AUDIT.audit_connection(self.db)
        after = self.db.execute("SELECT cliente_id FROM vehiculos WHERE id='v-orphan'").fetchone()
        self.assertEqual(before, after)

if __name__ == "__main__":
    unittest.main(verbosity=2)
