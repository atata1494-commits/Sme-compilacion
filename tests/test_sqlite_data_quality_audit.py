"""Unit tests for the read-only SQLite data quality auditor."""
import importlib.util
from pathlib import Path
import sqlite3
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sme_quality",ROOT/"scripts"/"audit_sqlite_data_quality.py")
AUDIT=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
SCHEMA=ROOT/"docs"/"SQLITE_SCHEMA.sql"

class DataQualityTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))
    def tearDown(self): self.db.close()
    def test_duplicate_document_and_plate_are_detected_case_insensitively(self):
        self.db.execute("INSERT INTO clientes(id,nombre,documento,payload_json) VALUES('c1','Uno',' 123 ','{}')")
        self.db.execute("INSERT INTO clientes(id,nombre,documento,payload_json) VALUES('c2','Dos','123','{}')")
        self.db.execute("INSERT INTO vehiculos(id,patente,payload_json) VALUES('v1','AB123CD','{}')")
        self.db.execute("INSERT INTO vehiculos(id,patente,payload_json) VALUES('v2',' ab123cd ','{}')")
        findings=AUDIT.audit_quality(self.db)
        duplicate_cols={(f["table"],f["column"]) for f in findings if f["type"]=="duplicate_value"}
        self.assertIn(("clientes","documento"),duplicate_cols)
        doc_alert=next(x for x in findings if x["table"]=="clientes" and x["type"]=="duplicate_value")
        self.assertEqual(doc_alert["severity"],"alta")
        self.assertIn(("vehiculos","patente"),duplicate_cols)
        plate_alert=next(x for x in findings if x["table"]=="vehiculos" and x["type"]=="duplicate_value")
        self.assertEqual(plate_alert["severity"],"alta")
    def test_empty_required_fields_are_warnings(self):
        self.db.execute("INSERT INTO clientes(id,nombre,payload_json) VALUES('c-empty','','{}')")
        self.db.execute("INSERT INTO vehiculos(id,patente,payload_json) VALUES('v-empty','','{}')")
        findings=AUDIT.audit_quality(self.db)
        warning={(f["table"],f["column"]) for f in findings if f["type"]=="missing_value"}
        self.assertIn(("clientes","nombre"),warning)
        self.assertIn(("vehiculos","patente"),warning)
    def test_no_mutation(self):
        self.db.execute("INSERT INTO clientes(id,nombre,payload_json) VALUES('c1','Cliente','{}')")
        before=self.db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        AUDIT.audit_quality(self.db)
        after=self.db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        self.assertEqual(before,after)

if __name__=="__main__": unittest.main(verbosity=2)
