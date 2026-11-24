import importlib.util, sqlite3, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"diagnose_sme.py"
spec=importlib.util.spec_from_file_location("diagnose_sme",SCRIPT)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class UnifiedDiagnosticsTests(unittest.TestCase):
    def test_missing_database_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            report=mod.run_diagnostics(Path(td)/"missing.db")
            self.assertEqual(report["status"],"BLOCKED")
            self.assertTrue(report["warnings"])
    def test_runs_audits_on_read_only_database(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"sme.db"
            con=sqlite3.connect(db)
            con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, documento TEXT, nombre TEXT)")
            con.execute("CREATE TABLE vehiculos (id INTEGER PRIMARY KEY, cliente_id INTEGER, patente TEXT)")
            con.execute("CREATE TABLE trabajos (id INTEGER PRIMARY KEY, cliente_id INTEGER, vehiculo_id INTEGER, numero TEXT, estado TEXT)")
            con.execute("CREATE TABLE presupuestos (id INTEGER PRIMARY KEY, trabajo_id INTEGER, cliente_id INTEGER, vehiculo_id INTEGER, numero TEXT)")
            con.execute("CREATE TABLE movimientos (id INTEGER PRIMARY KEY, trabajo_id INTEGER, cliente_id INTEGER, cuenta_id INTEGER, pago_id INTEGER)")
            con.execute("CREATE TABLE cuentas (id INTEGER PRIMARY KEY, trabajo_id INTEGER, cliente_id INTEGER)")
            con.execute("CREATE TABLE pagos_cuenta (id INTEGER PRIMARY KEY, cuenta_id INTEGER, movimiento_id INTEGER)")
            con.commit(); con.close()
            before=db.read_bytes()
            report=mod.run_diagnostics(db)
            self.assertEqual(report["status"],"REQUIRES_MANUAL_REVIEW")
            self.assertEqual(report["summary"]["audits_run"],3)
            self.assertEqual(report["summary"]["audit_failures"],0)
            self.assertEqual(db.read_bytes(),before)
    def test_missing_backup_validation_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"sme.db"
            con=sqlite3.connect(db); con.execute("CREATE TABLE empty (id INTEGER)"); con.close()
            report=mod.run_diagnostics(db,Path(td)/"absent.zip")
            self.assertEqual(report["status"],"BLOCKED")
            self.assertIsNotNone(report["backup_validation"])

if __name__=="__main__": unittest.main()
