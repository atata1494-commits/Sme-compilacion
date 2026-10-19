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
        self.assertIn("registros:'inicio',taller:'inicio',gestion:'inicio',mas:'inicio'", index)
        self.assertIn("clientes:'registros',vehiculos:'registros',trabajos:'registros'", index)
        self.assertIn("presupuestos:'gestion',tiempos:'gestion',caja:'gestion',cuentas:'gestion',agenda:'gestion'", index)
        self.assertIn("asistencias:'taller',terceros:'taller',tareas:'taller',avisos:'taller',gastos:'taller'", index)
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


class WelcomeTourTests(unittest.TestCase):
    def test_tour_is_permission_filtered_and_can_have_up_to_five_steps(self):
        index = INDEX.read_text(encoding="utf-8")
        builder = index.split("function smeBuildVisualTour(){", 1)[1].split(
            "function smeShowWelcomeTourStep", 1
        )[0]
        self.assertIn(".filter(item=>smeCan(item.key,'view'))", builder)
        self.assertIn("return steps.slice(0,5)", builder)
        self.assertIn("{key:'avisos',label:'Avisos internos'", builder)
        self.assertIn("const individualPriority=['tareas','asistencias','recepciones'", builder)
        self.assertIn("key:'mas',page:'mas',title:'Más: permisos y respaldos'", builder)
        self.assertIn("selectors:['#app [data-go=\"usuarios\"]','#app [data-go=\"respaldos\"]']", builder)
        self.assertIn("smeVisualTourSteps.length-1", index)
        self.assertIn("' / '+smeVisualTourSteps.length", index)

    def test_final_reminder_warns_and_confirms_permanent_decline(self):
        index = INDEX.read_text(encoding="utf-8")
        reminder = index.split("function smeShowWelcomeReminder(){", 1)[1].split(
            "function smeShowWelcomeIfNeeded", 1
        )[0]
        self.assertIn("Este es el último recordatorio", reminder)
        self.assertIn("¿Descartar el recorrido definitivamente?", reminder)
        self.assertIn("state.reminderDismissed=true", reminder)
        self.assertIn("state.completed=true", reminder)
        self.assertIn("Volver al recorrido", reminder)
        self.assertIn("No, gracias", reminder)
        self.assertIn("&&!state.reminderDismissed", index)
