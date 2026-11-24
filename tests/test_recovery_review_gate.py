import importlib.util, json, sqlite3, tempfile, zipfile
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("gate",ROOT/"scripts"/"recovery_review_gate.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
class RecoveryGateTests(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
 def tearDown(self): self.tmp.cleanup()
 def test_report_does_not_touch_current_db(self):
  current=self.d/"current.sqlite"; con=sqlite3.connect(current); con.execute("create table keep(id)"); con.commit(); con.close()
  backup=self.d/"backup.json"; backup.write_text('{"data":[1,2]}',encoding="utf8")
  before=MOD.sha256(current)
  report=MOD.build_review(current,backup)
  self.assertEqual(report["status"],"REQUIRES_MANUAL_REVIEW")
  self.assertEqual(before,MOD.sha256(current))
  self.assertIn("sha256",report["current_database"]); self.assertIn("sha256",report["backup"])
 def test_missing_backup_blocks(self):
  current=self.d/"current.db"; current.write_bytes(b"placeholder")
  report=MOD.build_review(current,self.d/"missing.zip")
  self.assertEqual(report["status"],"BLOCKED")
  self.assertTrue(report["validation_issues"])
if __name__=="__main__": unittest.main()
