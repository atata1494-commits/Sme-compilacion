"""Tests for the non-destructive backup validator."""
import importlib.util,json,sqlite3,tempfile,zipfile
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("sme_backup_validator",ROOT/"scripts"/"validate_sme_backup.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
class BackupValidatorTests(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.dir=Path(self.tmp.name)
 def tearDown(self): self.tmp.cleanup()
 def test_valid_json(self):
  p=self.dir/"backup.json"; p.write_text('{"records":[]}',encoding="utf-8")
  self.assertEqual(MOD.validate_backup(p),[])
 def test_invalid_json_warns(self):
  p=self.dir/"bad.json"; p.write_text("{bad",encoding="utf-8")
  self.assertTrue(MOD.validate_backup(p))
 def test_zip_valid_json_and_crc(self):
  p=self.dir/"backup.zip"
  with zipfile.ZipFile(p,"w") as z: z.writestr("backup.json",'{"ok":true}')
  self.assertEqual(MOD.validate_backup(p),[])
 def test_zip_traversal_is_reported(self):
  p=self.dir/"unsafe.zip"
  with zipfile.ZipFile(p,"w") as z: z.writestr("../escape.json",'{"x":1}')
  self.assertTrue(any("Ruta insegura" in x for x in MOD.validate_backup(p)))
 def test_sqlite_integrity(self):
  p=self.dir/"snapshot.db"; con=sqlite3.connect(p); con.execute("CREATE TABLE demo(id)"); con.close()
  self.assertEqual(MOD.validate_backup(p),[])
if __name__=="__main__": unittest.main(verbosity=2)
