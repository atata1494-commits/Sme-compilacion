"""Pruebas de integración del catálogo de tiempos con SME y Presupuestos."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "index.html").read_text(encoding="utf-8")
BUDGET = (ROOT / "src" / "budget" / "budget-module.js").read_text(encoding="utf-8")
SOURCE = SHELL + "\n" + BUDGET


class LaborTimeIntegrationTests(unittest.TestCase):
    def test_time_catalog_is_a_work_hours_reference_not_a_price_list(self):
        self.assertIn("const SME_LABOR_TIME_CATALOG = [", SHELL)
        self.assertIn("min:", SHELL)
        self.assertIn("suggested:", SHELL)
        self.assertIn("max:", SHELL)
        self.assertIn("no es una tabla de mano de obra argentina", SHELL)
        self.assertIn("const canUseBudget=smeCan('presupuestos','edit')", SHELL)

    def test_search_supports_gasket_distribution_engine_and_clutch_terms(self):
        for term in ("gasket-head-8v", "dist-k4m", "embrague", "distribucion"):
            self.assertIn(term, SHELL.lower())

    def test_independent_budget_module_consumes_catalog_and_uses_user_rate(self):
        self.assertIn("const catalog = Array.isArray(ctx.laborCatalog)", BUDGET)
        self.assertIn("Asistente de tiempos orientativos", BUDGET)
        self.assertIn("Tu tarifa por hora ($)", BUDGET)
        self.assertIn("rate=parseMoney(f.rate.value)", BUDGET)
        self.assertIn("usual*rate", BUDGET)

    def test_time_suggestions_are_only_applied_after_user_action(self):
        self.assertIn("form.elements.laborAmount.value=moneyInput(usual*rate)", BUDGET)
        self.assertIn("guardá el presupuesto manualmente", BUDGET)
        self.assertIn("form.elements.quickPrice.value=moneyInput(low)", BUDGET)

    def test_catalog_has_own_management_entry_and_permission(self):
        self.assertIn("['⏱','Tiempos de mano de obra','Promedios y referencias orientativas','tiempos']", SHELL)
        self.assertIn("{key:'tiempos',label:'Tiempos de mano de obra'}", SHELL)
        self.assertIn("if(!smeCan('tiempos','view'))", SHELL)

    def test_quote_hours_are_metadata_separate_from_customer_price_fields(self):
        self.assertIn("horasEstimadasMinimas", BUDGET)
        self.assertIn("horasEstimadasHabituales", BUDGET)
        self.assertIn("horasEstimadasMaximas", BUDGET)
        self.assertIn("tarifaHoraOrientativa", BUDGET)
        self.assertIn("importe:String(laborValue+partsValue+otherValue)", BUDGET)

    def test_time_catalog_is_compact_and_details_open_after_selection(self):
        self.assertIn("sme-time-table-head", SHELL)
        self.assertIn("sme-time-row", SHELL)
        self.assertIn("const paintDetail=()=>", SHELL)
        self.assertIn("selectedId=button.dataset.timeRow||'';draw(true)", SHELL)

    def test_specific_k4m_clio_time_has_a_technical_source_and_no_fake_range(self):
        self.assertIn("id:'dist-k4m-clio-748'", SHELL)
        self.assertIn("publishedHours:2.7", SHELL)
        self.assertIn("Referencia técnica específica", SHELL)
        self.assertIn("No extrapolar a todos los K4M", SHELL)

    def test_comparative_entries_show_source_quality_and_links(self):
        self.assertIn("Comparativo externo", SHELL)
        self.assertIn("sourceLinks:", SHELL)
        self.assertIn("Metodología y confianza de los datos", SHELL)

    def test_manual_clutch_and_gearbox_do_not_reuse_incompatible_times(self):
        self.assertIn("id:'clutch-sedan'", SHELL)
        self.assertIn("gearbox-pickup-4x2", SHELL)
        self.assertIn("gearbox-pickup-4x4", SHELL)

    def test_time_catalog_hides_unconfirmed_rows_by_default_and_has_a_filter(self):
        self.assertIn("Incluir trabajos sin horas confirmadas", SHELL)
        self.assertIn("item.suggested!==null", SHELL)

    def test_selected_time_detail_is_above_catalog_and_scrolls_into_view(self):
        self.assertLess(SHELL.index('id="smeLaborTimeDetail"'), SHELL.index('class="sme-time-table"'))
        self.assertIn("detail.scrollIntoView", SHELL)

    def test_grouped_average_clutch_catalog_covers_sedan_and_two_pickup_groups(self):
        self.assertIn("id:'clutch-sedan'", SHELL)
        self.assertIn("embrague-pickup-4x2", SHELL)
        self.assertIn("embrague-pickup-4x4", SHELL)

    def test_more_everyday_grouped_jobs_have_reference_hours(self):
        for entry in ("oil-pan-gasket", "head-bench", "brakes-discs-pads", "rear-drum-brakes", "fuel-pump"):
            self.assertIn("id:'" + entry + "'", SHELL)

    def test_grouped_average_records_include_scope_and_references(self):
        self.assertIn("scope:", SHELL)
        self.assertIn("sourceNote:", SHELL)

    def test_labor_entries_get_normalized_source_confidence_and_variant_metadata(self):
        self.assertIn("function smeLaborTimeMetadata(item)", SHELL)
        self.assertIn("confidence", SHELL)
        self.assertIn("vehicleGroup", SHELL)
        self.assertIn("variants", SHELL)

    def test_catalog_can_be_filtered_by_work_family_and_vehicle_group(self):
        self.assertIn("smeLaborTimeFamilyFilter", SHELL)
        self.assertIn("smeLaborTimeVehicleFilter", SHELL)

    def test_selected_detail_shows_source_hours_confidence_and_applicable_variants(self):
        self.assertIn("smeLaborTimeCardMarkup(item", SHELL)
        self.assertIn("sourceNote", SHELL)
        self.assertIn("publishedHours", SHELL)

    def test_published_hours_are_only_shown_when_the_value_exists(self):
        self.assertIn("Number.isFinite(item.publishedHours)", SHELL)
        self.assertIn("Sin tiempo confirmado", SHELL)


    def test_faatra_has_a_visible_expired_historical_fallback_without_cache(self):
        self.assertIn("const SME_FAATRA_FALLBACK=Object.freeze({value:84000", SOURCE)
        self.assertIn("period:'Julio, agosto y septiembre de 2026'", SOURCE)
        self.assertIn("usingFallback=!savedCurrent,current=savedCurrent||SME_FAATRA_FALLBACK", SOURCE)
        self.assertIn("Último valor oficial conocido · histórico", SOURCE)
        self.assertIn("no debe interpretarse como tarifa vigente", SOURCE)
        self.assertIn("Se mantiene este valor histórico de respaldo", SOURCE)


if __name__ == "__main__":
    unittest.main()
