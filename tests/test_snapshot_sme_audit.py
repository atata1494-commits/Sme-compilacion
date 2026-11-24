import importlib.util, sqlite3, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"snapshot_sme_audit.py"
spec=importlib.util.spec_from_file_location("snapshot_sme_audit",SCRIPT)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def create_db(path):
    con=sqlite3.connect(path)
    con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, documento TEXT, nombre TEXT)")
    con.execute("CREATE TABLE vehiculos (id INTEGER PRIMARY KEY, cliente_id INTEGER, patente TEXT)")
    con.execute("CREATE TABLE trabajos (id INTEGER PRIMARY KEY, cliente_id INTEGER, vehiculo_id INTEGER, numero TEXT, estado TEXT)")
    con.execute("CREATE TABLE presupuestos (id INTEGER PRIMARY KEY, trabajo_id INTEGER, cliente_id INTEGER, vehiculo_id INTEGER, numero TEXT)")
    con.execute("CREATE TABLE movimientos (id INTEGER PRIMARY KEY, trabajo_id INTEGER, cliente_id INTEGER, cuenta_id INTEGER, pago_id INTEGER)")
    con.execute("CREATE TABLE cuentas (id INTEGER PRIMARY KEY, trabajo_id INTEGER, cliente_id INTEGER)")
    con.execute("CREATE TABLE pagos_cuenta (id INTEGER PRIMARY KEY, cuenta_id INTEGER, movimiento_id INTEGER)")
    con.commit(); con.close()

class AuditSnapshotTests(unittest.TestCase):\n    def test_finding_diff_detects_new_resolved_and_persistent(self):\n        old={"relaciones":[{"id":1},{"id":2}]}; new={"relaciones":[{"id":2},{"id":3}]}\n        diff=mod.compare_findings(old,new)\n        self.assertEqual(diff["new_count"],1)\n        self.assertEqual(diff["resolved_count"],1)\n        self.assertEqual(diff["persistent_count"],1)\n        self.assertEqual(diff["new"][0]["finding"]["id"],3)\n        self.assertEqual(diff["resolved"][0]["finding"]["id"],1)\n
    def test_two_snapshots_compare_and_database_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); db=root/"sme.db"; history=root/"history"
            create_db(db); before=db.read_bytes()
            first,path1=mod.history_snapshot(db,history)
            second,path2=mod.history_snapshot(db,history)
            self.assertTrue(path1.exists()); self.assertTrue(path2.exists())
            self.assertNotEqual(path1,path2)
            self.assertEqual(second["comparison"]["sha_changed"],False)
            self.assertEqual(second["comparison"]["finding_delta"],0)
            self.assertEqual(second["database_sha256"],first["database_sha256"])
            self.assertEqual(db.read_bytes(),before)
    def test_history_is_isolated_by_database_filename(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); h=root/"history"; a=root/"a.db"; b=root/"b.db"
            create_db(a); create_db(b)
            mod.history_snapshot(a,h)
            second,_=mod.history_snapshot(b,h)
            self.assertIsNone(second["comparison"])

if __name__=="__main__": unittest.main()
