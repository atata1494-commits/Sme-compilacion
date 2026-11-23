"""Pruebas de regresión para el resumen de movimientos relevantes SME."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "index.html").read_text(encoding="utf-8")
BUDGET = (ROOT / "src" / "budget" / "budget-module.js").read_text(encoding="utf-8")


class BusinessActivitySummaryTests(unittest.TestCase):
    def test_activity_helper_records_business_events_and_attention_state(self):
        self.assertIn("function smeBusinessActivity(action,detail,options={})", SOURCE)
        self.assertIn("kind:'business'", SOURCE)
        self.assertIn("requiresAttention:!!options.requiresAttention", SOURCE)
        self.assertIn("status:options.status||(options.requiresAttention?'pendiente':'informativo')", SOURCE)

    def test_activity_widget_excludes_generic_save_and_navigation_noise(self):
        self.assertIn("x.kind==='business'&&String(x.time||'').slice(0,10)===today", SOURCE)
        self.assertNotIn("action:'Guardado de datos',detail:'La base de datos local confirmó el guardado.'", SOURCE)
        self.assertNotIn("smeActivityWrite({id:newRecordId(),time:new Date().toISOString(),userId:", SOURCE)

    def test_pending_attention_panel_uses_unresolved_events_only(self):
        self.assertIn("logs.filter(x=>x.requiresAttention&&x.status==='pendiente')", SOURCE)
        self.assertIn("x.status='resuelto';x.resolvedAt=now", SOURCE)
        self.assertIn("Requiere atención", SOURCE)
        self.assertIn("Pendiente resuelto", SOURCE)

    def test_task_creation_and_state_changes_are_instrumented(self):
        self.assertIn("smeBusinessActivity('Tarea creada',t.titulo+", SOURCE)
        self.assertIn("smeBusinessActivity('Tarea · '+smeTaskStateLabel(next)", SOURCE)

    def test_attendance_actions_are_logged_for_admin_summary(self):
        self.assertIn("smeBusinessActivity(\'Control horario · \'+punchLabel", SOURCE)
        self.assertIn("Horario laboral actualizado", SOURCE)
        self.assertIn("Excepción de horario configurada", SOURCE)
        self.assertIn("Registro horario corregido", SOURCE)

    def test_expense_requests_and_approval_cycle_are_logged(self):
        self.assertIn("Solicitud de gasto enviada · Pendiente de autorización", SOURCE)
        self.assertIn("Gasto autorizado", SOURCE)
        self.assertIn("Compra realizada · Pendiente de rendición", SOURCE)
        self.assertIn("Rendición verificada", SOURCE)
        self.assertIn("recordId:g.id,status:'pendiente'", SOURCE)

    def test_budget_module_reports_successful_create_or_update(self):
        self.assertIn("activity((editingQuote?'Presupuesto actualizado · ':'Presupuesto creado · ')+label", BUDGET)
        self.assertIn("if(!ok){db.presupuestos.splice(0,db.presupuestos.length,...old)", BUDGET)


if __name__ == "__main__":
    unittest.main()
