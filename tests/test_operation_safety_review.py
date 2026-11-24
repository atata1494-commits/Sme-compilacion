import importlib.util, unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"operation_safety_review.py"
spec=importlib.util.spec_from_file_location("operation_safety_review",SCRIPT)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class OperationSafetyReviewTests(unittest.TestCase):
    def test_all_sensitive_operations_are_review_only(self):
        for op in ("import","overwrite","delete","restore"):
            report=mod.build_review(op)
            self.assertEqual(report["operation"],op)
            self.assertEqual(report["decision"],"REVIEW_ONLY")
            self.assertGreater(len(report["checks"]),0)
    def test_flags_only_mark_related_checks(self):
        report=mod.build_review("restore",backup_validated=True,preview_done=True,admin_approved=True)
        statuses=[x["status"] for x in report["checks"]]
        self.assertIn("confirmed",statuses)
        self.assertIn("pending",statuses)
    def test_overwrite_restore_are_critical(self):
        self.assertEqual(mod.build_review("overwrite")["risk"],"CRITICAL")
        self.assertEqual(mod.build_review("restore")["risk"],"CRITICAL")
if __name__=="__main__": unittest.main()
