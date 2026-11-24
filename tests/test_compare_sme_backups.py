import importlib.util, sqlite3, tempfile, unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"compare_sme_backups.py"
spec=importlib.util.spec_from_file_location("compare_sme_backups",SCRIPT)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def make_db(path, tables):
    con=sqlite3.connect(path)
    try:
        for sql, rows in tables:
            con.execute(sql)
            for row in rows: con.execute("INSERT INTO sample VALUES (?)",row)
        con.commit()
    finally: con.close()

class BackupComparisonTests(unittest.TestCase):
    def test_table_inventory_and_counts(self):
        with tempfile.TemporaryDirectory() as td:
            old=Path(td)/"old.db"; new=Path(td)/"new.db"
            make_db(old,[("CREATE TABLE sample (value TEXT)",[("a",),("b",)])])
            make_db(new,[("CREATE TABLE sample (value TEXT)",[("a",)])])
            report=mod.compare(old,new)
            self.assertEqual(report["status"],"REQUIRES_MANUAL_REVIEW")
            self.assertEqual(report["row_count_changes"],[{"table":"sample","older_rows":2,"newer_rows":1,"delta":-1}])
            self.assertFalse(report["tables_missing_in_new"])\n            self.assertFalse(report["tables_empty_in_new"])
    def test_detects_removed_and_added_tables(self):
        with tempfile.TemporaryDirectory() as td:
            old=Path(td)/"old.db"; new=Path(td)/"new.db"
            c=sqlite3.connect(old); c.execute("CREATE TABLE gone (id INTEGER)"); c.commit(); c.close()
            c=sqlite3.connect(new); c.execute("CREATE TABLE fresh (id INTEGER)"); c.commit(); c.close()
            report=mod.compare(old,new)
            self.assertEqual(report["tables_missing_in_new"],["gone"])
            self.assertEqual(report["tables_added_in_new"],["fresh"])
    def test_detects_schema_change(self):
        with tempfile.TemporaryDirectory() as td:
            old=Path(td)/"old.db"; new=Path(td)/"new.db"
            for p,sql in [(old,"CREATE TABLE sample (value TEXT)"),(new,"CREATE TABLE sample (value TEXT, extra INTEGER)")]:
                c=sqlite3.connect(p); c.execute(sql); c.close()
            report=mod.compare(old,new)
            self.assertEqual(report["schema_changed"],["sample"])
    def test_does_not_modify_databases(self):
        with tempfile.TemporaryDirectory() as td:
            old=Path(td)/"old.db"; new=Path(td)/"new.db"
            c=sqlite3.connect(old); c.execute("CREATE TABLE t (id INTEGER)"); c.commit(); c.close()
            c=sqlite3.connect(new); c.execute("CREATE TABLE t (id INTEGER)"); c.close()
            before=old.read_bytes()
            mod.compare(old,new)
            self.assertEqual(old.read_bytes(),before)

    def test_integrity_failure_blocks_review(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            old=Path(td)/"old.db"; new=Path(td)/"new.db"
            for p in (old,new):
                c=sqlite3.connect(p); c.execute("CREATE TABLE t (id INTEGER)"); c.close()
            normal=mod.inspect_db(new)
            damaged=dict(normal); damaged["integrity"]="corrupt"
            with patch.object(mod,"inspect_db",side_effect=[damaged,normal]):
                report=mod.compare(old,new)
            self.assertEqual(report["status"],"BLOCKED")
            self.assertTrue(any("Integridad" in warning for warning in report["warnings"]))
\n    def test_missing_path_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError): mod.inspect_db(Path(td)/"missing.db")

if __name__=="__main__": unittest.main()
