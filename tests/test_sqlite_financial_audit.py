"""Tests for financial SQLite auditor, including read-only behavior."""
import importlib.util,sqlite3,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sme_financial",ROOT/"scripts"/"audit_sqlite_financial.py")
AUDIT=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(AUDIT)
SCHEMA=ROOT/"docs"/"SQLITE_SCHEMA.sql"
class FinancialAuditTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:"); self.db.executescript(SCHEMA.read_text(encoding="utf-8"))
 def tearDown(self): self.db.close()
 def test_clean_budget_and_movement(self):
  self.db.execute("INSERT INTO presupuestos(id,mano_obra_centavos,repuestos_centavos,importe_centavos,payload_json) VALUES('b1',1000,2000,3000,'{}')")
  self.db.execute("INSERT INTO movimientos(id,importe_centavos,comision_centavos,importe_neto_centavos,payload_json) VALUES('m1',1000,100,900,'{}')")
  self.assertEqual(AUDIT.audit_financial(self.db),[])
 def test_mismatches_and_negative_amounts(self):
  self.db.execute("INSERT INTO presupuestos(id,mano_obra_centavos,repuestos_centavos,importe_centavos,payload_json) VALUES('b2',1000,2000,4000,'{}')")
  self.db.execute("INSERT INTO movimientos(id,importe_centavos,comision_centavos,importe_neto_centavos,payload_json) VALUES('m2',1000,100,850,'{}')")
  self.db.execute("INSERT INTO pagos_cuenta(id,cuenta_id,importe_centavos,payload_json) VALUES('p2','c-missing',-500,'{}')")
  types={f["kind"] for f in AUDIT.audit_financial(self.db)}
  self.assertIn("budget_total_mismatch",types); self.assertIn("movement_net_mismatch",types); self.assertIn("negative_payment",types)
 def test_no_write(self):
  self.db.execute("INSERT INTO presupuestos(id,mano_obra_centavos,repuestos_centavos,importe_centavos,payload_json) VALUES('b1',1,2,3,'{}')")
  before=self.db.execute("SELECT count(*) FROM presupuestos").fetchone()[0]
  AUDIT.audit_financial(self.db)
  self.assertEqual(before,self.db.execute("SELECT count(*) FROM presupuestos").fetchone()[0])
if __name__=="__main__": unittest.main(verbosity=2)
