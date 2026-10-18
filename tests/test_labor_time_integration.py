"""Pruebas de regresión para el catálogo de tiempos y su vínculo con Presupuestos."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "index.html").read_text(encoding="utf-8")


class LaborTimeIntegrationTests(unittest.TestCase):
    def test_time_catalog_is_a_work_hours_reference_not_a_price_list(self):
        self.assertIn("const SME_LABOR_TIME_CATALOG = [", SOURCE)
        self.assertIn("Referencias para estimar horas de trabajo", SOURCE)
        self.assertIn("min:4,suggested:5,max:6", SOURCE)
        self.assertIn("min:6,suggested:7,max:8", SOURCE)
        self.assertIn("status:'Pendiente de confirmar'", SOURCE)
        self.assertNotIn("ATIA Argentina · Categoría", SOURCE)

    def test_search_supports_gasket_distribution_engine_and_clutch_terms(self):
        self.assertIn("function smeLaborTimeSearchText(item)", SOURCE)
        self.assertIn("normalizeSearch", SOURCE)
        self.assertIn("keywords:'junta tapa 8v", SOURCE)
        self.assertIn("keywords:'distribucion 16v", SOURCE)
        self.assertIn("keywords:'embrague cambio embrague", SOURCE)

    def test_budget_has_a_separate_optional_time_helper(self):
        self.assertIn('id="smeBudgetLaborTimeAssist"', SOURCE)
        self.assertIn('id="smeBudgetLaborSearch"', SOURCE)
        self.assertIn('id="smeApplyLaborTime"', SOURCE)
        self.assertIn("smeInitBudgetLaborTimeAssist(form)", SOURCE)
        self.assertIn("form.elements.horasOrientativas.value=String(hours)", SOURCE)
        self.assertIn("form.elements.operacionTiempoOrientativa.value=selected.id", SOURCE)

    def test_time_suggestion_uses_user_entered_hourly_rate(self):
        self.assertIn('id="smeBudgetLaborRate"', SOURCE)
        self.assertIn("const amount=Math.round(hours*rate*100)/100", SOURCE)
        self.assertIn("parseMoneyInput(rateInput.value||'0')", SOURCE)
        self.assertIn("laborField.value=formatMoneyInput(amount)", SOURCE)

    def test_accepted_or_in_progress_budgets_are_not_modified_by_suggestions(self):
        self.assertIn("const lockedQuote=()=>", SOURCE)
        self.assertIn("['Aprobado','En ejecución','Entregado','Pendiente de pago','Finalizado'].includes", SOURCE)
        self.assertIn("La sugerencia no puede aplicarse a un presupuesto acordado", SOURCE)
        self.assertIn("if(lockedQuote()){preview.textContent='No se modificó el presupuesto", SOURCE)

    def test_catalog_has_own_management_entry_and_permission(self):
        self.assertIn("{key:'tiempos',label:'Tiempos de mano de obra'}", SOURCE)
        self.assertIn("else if(page==='tiempos') smeLaborTimesPage()", SOURCE)
        self.assertIn("Referencias orientativas para presupuestar','tiempos')", SOURCE)
        self.assertIn("tiempos:'mas'", SOURCE)
        self.assertIn("set(['tiempos'],'view')", SOURCE)

    def test_quote_hour_metadata_is_separate_from_client_price_fields(self):
        self.assertIn('name="horasOrientativas"', SOURCE)
        self.assertIn('name="operacionTiempoOrientativa"', SOURCE)
        self.assertIn('name="tarifaHoraOrientativa"', SOURCE)
        self.assertIn("la tarifa la ingresás vos", SOURCE)
        self.assertIn("No se altera ningún presupuesto guardado", SOURCE)


if __name__ == "__main__":
    unittest.main()
