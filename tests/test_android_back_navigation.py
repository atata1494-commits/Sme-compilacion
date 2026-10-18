"""Regresión estática para el botón Atrás en Android."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
PACKAGE = ROOT / "package.json"


class AndroidBackNavigationTests(unittest.TestCase):
    def test_capacitor_app_plugin_is_declared_and_imported(self):
        index = INDEX.read_text(encoding="utf-8")
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        self.assertIn("@capacitor/app", package["dependencies"])
        self.assertIn("import { App as CapacitorApp } from '@capacitor/app';", index)

    def test_back_button_follows_parent_menu_not_visit_history(self):
        index = INDEX.read_text(encoding="utf-8")
        self.assertIn("CapacitorApp.addListener('backButton'", index)
        self.assertIn("const SME_BACK_PARENT_BY_PAGE=Object.freeze({", index)
        self.assertIn("mas:'inicio'", index)
        self.assertIn("presupuestos:'mas'", index)
        self.assertIn("asistencias:'mas'", index)
        handler = index.split("async function smeHandleHardwareBack(){", 1)[1].split("async function save()", 1)[0]
        self.assertIn("const parentPage=SME_BACK_PARENT_BY_PAGE[page]||'inicio';", handler)
        self.assertIn("smeNavigateTo(parentPage);", handler)
        self.assertNotIn("pageHistory", index)

    def test_home_requires_a_second_back_press_to_exit(self):
        index = INDEX.read_text(encoding="utf-8")
        self.assertIn("Presioná Atrás otra vez para salir", index)
        self.assertIn("now-exitBackPressedAt<=2200", index)
        self.assertIn("await CapacitorApp.exitApp()", index)

    def test_standard_android_workflow_applies_sme_branding(self):
        workflow = (ROOT / ".github" / "workflows" / "android-apk-validation.yml").read_text(encoding="utf-8")
        self.assertIn("node scripts/generate-android-icons.mjs", workflow)
        self.assertIn("node scripts/configure-android-splash.mjs", workflow)

    def test_recent_apps_return_grace_period_is_2_5_seconds(self):
        index = INDEX.read_text(encoding="utf-8")
        self.assertIn("const SME_BACKGROUND_GRACE_MS=2500;", index)
        self.assertIn("document.visibilityState==='hidden'&&smeAuthenticated", index)
        self.assertIn("document.visibilityState==='visible'", index)
        self.assertIn("clearTimeout(smeBackgroundLockTimer)", index)


if __name__ == "__main__":
    unittest.main(verbosity=2)
