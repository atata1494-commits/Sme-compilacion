"""Pruebas de regresión para el módulo de Presupuestos independiente de SME."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "index.html").read_text(encoding="utf-8")
MODULE = (ROOT / "src" / "budget" / "budget-module.js").read_text(encoding="utf-8")
STYLE = (ROOT / "src" / "budget" / "budget-module.css").read_text(encoding="utf-8")


class BudgetQualityTests(unittest.TestCase):
    def test_presupuestos_is_mounted_as_a_separate_module(self):
        self.assertIn("import { renderBudgetModule } from './src/budget/budget-module.js';", SHELL)
        self.assertIn("else if(page==='presupuestos') renderBudgetModule(", SHELL)
        self.assertIn("export function renderBudgetModule(ctx)", MODULE)
        self.assertIn("import './budget-module.css';", MODULE)

    def test_previous_monolithic_budget_implementation_is_removed(self):
        for legacy in ("function smeOrientativeAmount(", "function smeOrientativePdfBase64(", "function smeInitQuickLaborEstimate(", "function smeInitBudgetLaborTimeAssist(", "function smeBudgetDocumentHtml(", "function smeSetOrientativeBudgetExpanded("):
            self.assertNotIn(legacy, SHELL)
        self.assertIn("sme-budget-v2", MODULE)
        self.assertIn("sme-budget-v2", STYLE)

    def test_formal_quote_has_separate_concepts_and_calculated_total(self):
        self.assertIn('name="laborAmount"', MODULE)
        self.assertIn('name="partsAmount"', MODULE)
        self.assertIn('name="otherAmount"', MODULE)
        self.assertIn("const totalValue=()=>parseMoney(labor.value)+parseMoney(parts.value)+parseMoney(other.value);", MODULE)
        self.assertIn("importe:String(laborValue+partsValue+otherValue)", MODULE)
        self.assertIn("Los importes no pueden ser negativos.", MODULE)

    def test_money_inputs_use_argentine_thousands_separators(self):
        self.assertIn("replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.')", MODULE)
        self.assertIn("new Intl.NumberFormat('es-AR'", MODULE)
        self.assertIn("input.addEventListener('blur',()=>{if(input.value)input.value=moneyInput(input.value)});", MODULE)

    def test_quick_quote_defaults_to_one_price_and_range_is_opt_in(self):
        self.assertIn('name="quickPrice"', MODULE)
        self.assertIn('name="usePriceRange"', MODULE)
        self.assertIn('name="quickPriceMax"', MODULE)
        self.assertIn("if(requestedRange&&(high<low||high<=0))", MODULE)
        self.assertIn("usarRangoPrecio:!!requestedRange", MODULE)

    def test_installment_options_are_calculated_and_conditions_are_visible(self):
        self.assertIn("Opciones de cuotas para el cliente", MODULE)
        self.assertIn('name="installmentCount"', MODULE)
        self.assertIn("count+' cuotas estimadas de '+amount(total/count)", MODULE)
        self.assertIn("Confirmá que el medio de pago realmente ofrece esta condición.", MODULE)

    def test_time_assistant_searches_and_can_open_the_full_catalog(self):
        self.assertIn("Asistente de tiempos orientativos", MODULE)
        self.assertIn("Abrir tabla completa de tiempos", MODULE)
        self.assertIn("data-budget-time-select", MODULE)
        self.assertIn("form.elements.hoursEstimatedUsual.value=String(usual)", MODULE)
        self.assertIn("form.elements.laborAmount.value=moneyInput(usual*rate)", MODULE)

    def test_saved_quote_is_restored_if_storage_save_fails(self):
        self.assertIn("const old=[...db.presupuestos];", MODULE)
        self.assertIn("db.presupuestos.splice(0,db.presupuestos.length,...old);", MODULE)
        self.assertIn("Los datos del formulario siguen disponibles", MODULE)

    def test_customer_document_never_includes_private_cost_analysis(self):
        start = MODULE.index("const customerDocument = q =>")
        end = MODULE.index("const buildDocumentHtml = q =>", start)
        document = MODULE[start:end]
        for field in ("hourlyCost", "partsCost", "targetMarginPct", "paymentFeePct", "analisisInterno"):
            self.assertNotIn(field, document)
        self.assertIn("Los costos, márgenes y cálculos internos", MODULE)

    def test_internal_profitability_analysis_is_permission_gated(self):
        self.assertIn("const canReadCosts = can('presupuestos', 'costs');", MODULE)
        self.assertIn("const canEditCosts = can('presupuestos', 'costs-edit');", MODULE)
        self.assertIn("SOLO USO INTERNO", MODULE)
        self.assertIn("if(!canEditCosts)return;", MODULE)
        self.assertIn("const denominator=1-(v.targetMarginPct+v.paymentFeePct+v.taxRatePct)/100", MODULE)

    def test_only_draft_budgets_can_receive_suggested_price_and_price_is_never_reduced(self):
        self.assertIn("String(r.q.estado||'Borrador')!=='Borrador'", MODULE)
        self.assertIn("Math.ceil(Math.max(previousPrice,r.suggested,lineTotal))", MODULE)
        self.assertIn("lastAppliedPrice", MODULE)

    def test_module_keeps_customer_vehicle_work_relationships(self):
        self.assertIn("clienteId:String(values.get('clienteId')||'')", MODULE)
        self.assertIn("vehiculoId:String(values.get('vehiculoId')||'')", MODULE)
        self.assertIn("trabajoId:String(values.get('trabajoId')||'')", MODULE)
        self.assertIn('data-budget-related="trabajos"', MODULE)


if __name__ == "__main__":
    unittest.main()
