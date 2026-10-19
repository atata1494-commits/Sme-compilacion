"""Source regressions for SME formal budgeting and profitability controls."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "index.html").read_text(encoding="utf-8")


class BudgetQualityTests(unittest.TestCase):
    def test_formal_quote_breakdown_adds_other_customer_facing_concepts(self):
        self.assertIn("['otrosConceptos','Servicios externos, insumos y otros trabajos ($)','number']", SOURCE)
        self.assertIn("obj.importe=String(m+r+other)", SOURCE)
        self.assertIn("const named=name=>form.elements.namedItem(name)", SOURCE)
        self.assertIn("const calcTotal=()=>{const fields=[labor,parts,other]", SOURCE)
        self.assertIn("formatMoneyInput(sum)", SOURCE)
        self.assertIn("Los importes del presupuesto no pueden ser negativos.", SOURCE)
        self.assertIn("const isMoney=['importe','manoObra','repuestos','otrosConceptos','comision','materiales','otrosGastos'].includes(name)", SOURCE)
        self.assertIn("Se calcula automáticamente con mano de obra + repuestos + otros conceptos.", SOURCE)

    def test_customer_document_explains_diagnosis_solution_scope_and_exclusions(self):
        for field in ("diagnosticoCliente", "solucionRecomendada", "alcanceTrabajo", "trabajosExcluidos", "condicionesGarantia", "condicionesPago"):
            self.assertIn(f'name="{field}"', SOURCE)
        self.assertIn("Motivo / diagnóstico comunicado", SOURCE)
        self.assertIn("Solución recomendada", SOURCE)
        self.assertIn("Fuera del alcance de esta propuesta", SOURCE)
        self.assertIn("Nombre y firma del cliente", SOURCE)
        self.assertIn('name="detalleOtrosConceptos"', SOURCE)
        self.assertIn("esc(o.detalleOtrosConceptos||'Conceptos adicionales indicados en la propuesta')", SOURCE)

    def test_pdf_is_branded_and_has_clear_economic_summary(self):
        self.assertIn("function smeBudgetDocumentHtml(o)", SOURCE)
        self.assertIn("Servicios Mecánicos Enzo", SOURCE)
        self.assertIn("Detalle económico", SOURCE)
        self.assertIn("Total propuesto", SOURCE)
        self.assertIn("Propuesta válida por ", SOURCE)
        self.assertIn("Conservá una copia de esta propuesta.", SOURCE)
        self.assertIn("Printer.printHtml({html,name:recordTitle(key,o)})", SOURCE)

    def test_internal_cost_model_accounts_for_payment_processing(self):
        self.assertIn('name="paymentFeePct"', SOURCE)
        self.assertIn('name="paymentFeeFixed"', SOURCE)
        self.assertIn("const paymentFee=customerTotal*paymentFeePct/100", SOURCE)
        self.assertIn("requiredDenominator=1-targetMarginPct/100-(1+taxRatePct/100)*paymentFeePct/100", SOURCE)
        self.assertIn("comisión de cobro estimada", SOURCE)

    def test_suggested_price_application_is_explicit_and_draft_only(self):
        self.assertIn("data-apply-cost-price", SOURCE)
        self.assertIn("String(liveQuote.estado||'Borrador')!=='Borrador'", SOURCE)
        self.assertIn("originalTotal>=currentResult.suggestedMinimum", SOURCE)
        self.assertIn("const target=Math.ceil(currentResult.suggestedMinimum)", SOURCE)
        self.assertIn("!savedAnalysis.updatedAt||!formMatches||Number(savedAnalysis.precioClienteAlAnalizar)!==originalTotal", SOURCE)
        self.assertIn("analysisHistory.push({fecha:appliedAt", SOURCE)
        self.assertIn("result.salePrice<result.suggestedMinimum", SOURCE)
        self.assertIn("Aplicar precio recomendado", SOURCE)
        self.assertIn("Los costos internos no se mostrarán al cliente.", SOURCE)
        self.assertIn("Cambios de precio registrados", SOURCE)
        self.assertIn("result.salePrice<result.suggestedMinimum", SOURCE)

    def test_private_cost_data_is_not_in_customer_pdf_template(self):
        start = SOURCE.index("function smeBudgetDocumentHtml(o)")
        end = SOURCE.index("async function printRecord", start)
        document = SOURCE[start:end]
        self.assertNotIn("hourlyCost", document)
        self.assertNotIn("partsCost", document)
        self.assertNotIn("externalCost", document)
        self.assertNotIn("targetMarginPct", document)
        self.assertNotIn("paymentFeePct", document)
        self.assertIn("analysis.taxRatePct", document)



    def test_formal_budget_total_updates_after_draft_restoration_and_live_input(self):
        self.assertIn("function smeRestoreFormDrafts()", SOURCE)
        self.assertIn("restored.forEach(el=>{try{el.dispatchEvent(new Event", SOURCE)
        self.assertIn("form.addEventListener('input',event=>{if(['manoObra','repuestos','otrosConceptos']", SOURCE)
        self.assertIn("[labor,parts,other].filter(Boolean).forEach(input=>['input','change','keyup','blur'].forEach(type=>input.addEventListener(type,calcTotal)))", SOURCE)
        self.assertIn("total.setAttribute('value',total.value)", SOURCE)
        self.assertIn("function formatMoneyWhileTyping(value)", SOURCE)
        self.assertIn("input.type='text';input.inputMode='numeric';input.autocomplete='off'", SOURCE)

    def test_formal_installments_are_configurable_calculated_and_printed(self):
        for fragment in ('name="ofrecerCuotasFormal"', 'name="cantidadCuotasFormal"', 'name="condicionesCuotasFormal"', 'id="smeFormalInstallmentPreview"'):
            self.assertIn(fragment, SOURCE)
        self.assertIn("const paintFormalInstallments=()=>", SOURCE)
        self.assertIn("const formalInstallmentsHtml=!orientative&&formalInstallmentOffer", SOURCE)

    def test_save_errors_do_not_discard_session(self):
        self.assertIn("let beforeSnapshot=null,wasSaved=false;try{const obj=Object.fromEntries", SOURCE)
        self.assertIn("if(smeAuthenticated)smeResetIdleTimer()", SOURCE)
        self.assertIn("La sesión se mantiene abierta. Revisá los datos", SOURCE)


if __name__ == "__main__":
    unittest.main()
