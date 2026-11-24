import importlib.util,json,sqlite3,tempfile,zipfile
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("preview",ROOT/"scripts"/"preview_sme_recovery.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
class RecoveryPreviewTests(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
 def tearDown(self): self.tmp.cleanup()
 def test_preview_json_does_not_modify(self):
  p=self.d/"data.json"; p.write_text('{"clients":[1,2]}',encoding="utf8")
  report=MOD.preview_backup(p)
  self.assertFalse(report["warnings"]); self.assertEqual(report["contents"][0]["record_count"],1)
  self.assertEqual(json.loads(p.read_text()),{"clients":[1,2]})
 def test_preview_zip_json_and_sqlite(self):
  db=self.d/"temp.db"; con=sqlite3.connect(db); con.execute("create table sample(id)"); con.execute("insert into sample values(1)"); con.commit(); con.close()
  p=self.d/"backup.zip"
  with zipfile.ZipFile(p,"w") as z:
   z.writestr("metadata.json",'{"version":2}'); z.write(db,"database.sqlite")
  report=MOD.preview_backup(p)
  self.assertFalse(report["warnings"]); self.assertEqual(len(report["contents"]),2)
  self.assertEqual(report["contents"][1]["preview"]["tables"][0]["rows"],1)
 def test_traversal_aborts_preview(self):
  p=self.d/"unsafe.zip"
  with zipfile.ZipFile(p,"w") as z: z.writestr("../evil.json",'{"x":1}')
  report=MOD.preview_backup(p)
  self.assertTrue(any("Ruta insegura" in w for w in report["warnings"])); self.assertEqual(report["contents"],[])
 def test_missing_file_warns(self):
  self.assertTrue(MOD.preview_backup(self.d/"missing.zip")["warnings"])
if __name__=="__main__": unittest.main()
