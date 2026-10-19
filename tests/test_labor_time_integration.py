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
        self.assertIn("min:4.5,suggested:5.5,max:7.5,status:'Promedio agrupado SME'", SOURCE)
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
        self.assertIn("Tiempos de mano de obra", SOURCE)
        self.assertIn("Promedios y referencias orientativas", SOURCE)
        self.assertIn("else if(page==='gestion')smeRenderHubPage('Gestión'", SOURCE)
        self.assertIn("tiempos:'gestion'", SOURCE)
        self.assertIn("set(['tiempos'],'view')", SOURCE)

    def test_quote_hour_metadata_is_separate_from_client_price_fields(self):
        self.assertIn('name="horasOrientativas"', SOURCE)
        self.assertIn('name="operacionTiempoOrientativa"', SOURCE)
        self.assertIn('name="tarifaHoraOrientativa"', SOURCE)
        self.assertIn("la tarifa la ingresás vos", SOURCE)
        self.assertIn("No se altera ningún presupuesto guardado", SOURCE)


    def test_faatra_has_a_visible_expired_historical_fallback_without_cache(self):
        self.assertIn("const SME_FAATRA_FALLBACK=Object.freeze({value:84000", SOURCE)
        self.assertIn("period:'Julio, agosto y septiembre de 2026'", SOURCE)
        self.assertIn("usingFallback=!savedCurrent,current=savedCurrent||SME_FAATRA_FALLBACK", SOURCE)
        self.assertIn("Último valor oficial conocido · histórico", SOURCE)
        self.assertIn("no debe interpretarse como tarifa vigente", SOURCE)
        self.assertIn("Se mantiene este valor histórico de respaldo", SOURCE)

    def test_time_catalog_is_compact_and_detail_opens_only_after_selection(self):
        self.assertIn('class="sme-time-table"', SOURCE)
        self.assertIn("function smeLaborTimeCompactRowMarkup(item,selected,actionAttribute)", SOURCE)
        self.assertIn('id="smeLaborTimeDetail" class="sme-time-detail" hidden', SOURCE)
        self.assertIn("selectedId=button.dataset.timeRow||'';draw(true)", SOURCE)
        self.assertIn("results.innerHTML=matches.length?matches.map(item=>smeLaborTimeCompactRowMarkup", SOURCE)

    def test_budget_search_shows_compact_matches_and_one_selected_detail(self):
        self.assertIn('id="smeBudgetLaborResults" class="sme-budget-time-results"', SOURCE)
        self.assertIn('id="smeBudgetLaborSelected" class="sme-time-selected-detail" hidden', SOURCE)
        self.assertIn('id="smeBudgetLaborCalculation" class="sme-budget-time-calculation" hidden', SOURCE)
        self.assertIn("Escribí el nombre de un trabajo o motor para ver coincidencias", SOURCE)
        self.assertIn("calculation.hidden=!(selected&&selected.suggested!==null)", SOURCE)


    def test_k4m_clio_time_has_a_specific_technical_source_and_no_fake_range(self):
        self.assertIn("id:'dist-k4m-clio-748'", SOURCE)
        self.assertIn("publishedHours:2.7,status:'Referencia técnica específica'", SOURCE)
        self.assertIn("Ficha técnica ContiTech · K4M 748", SOURCE)
        self.assertIn("Tiempo publicado: '+smeLaborHoursLabel(item.publishedHours)", SOURCE)

    def test_comparative_entries_show_source_quality_and_links(self):
        self.assertIn("status:'Comparativo externo'", SOURCE)
        self.assertIn("Open Labor Project publica 0,3 h", SOURCE)
        self.assertIn("sourceLinks.map(link=>'<a href=", SOURCE)
        self.assertIn("https://openlaborproject.com/data-provenance", SOURCE)
        self.assertIn("Contexto del dato:", SOURCE)
        self.assertIn("id:'dist-aveo-16-2014'", SOURCE)

    def test_manual_clutch_and_gearbox_do_not_reuse_incompatible_transmission_times(self):
        self.assertIn("id:'clutch-sedan'", SOURCE)
        self.assertIn("id:'clutch-pickup-4x2'", SOURCE)
        self.assertIn("id:'clutch-pickup-4x4'", SOURCE)
        self.assertIn("min:5.5,suggested:7,max:8.5,status:'Promedio agrupado SME'", SOURCE)
        self.assertIn("min:6.5,suggested:8,max:10,status:'Promedio agrupado SME'", SOURCE)
        self.assertIn("id:'gearbox-pickup-4x2'", SOURCE)
        self.assertIn("id:'gearbox-pickup-4x4'", SOURCE)


    def test_time_catalog_hides_unconfirmed_rows_by_default_and_provides_a_filter(self):
        self.assertIn('id="smeLaborTimesShowPending" type="checkbox"', SOURCE)
        self.assertIn("Incluir trabajos sin horas confirmadas", SOURCE)
        self.assertIn("const includePending=showPending.checked||words.length>0", SOURCE)
        self.assertIn("(includePending||item.suggested!==null)", SOURCE)
        self.assertIn("showPending.addEventListener('change',()=>draw())", SOURCE)

    def test_selected_time_detail_is_above_catalog_and_scrolls_into_view(self):
        page = SOURCE[SOURCE.index("function smeLaborTimesPage()"):SOURCE.index("let smePendingLaborTimeId")]
        self.assertLess(page.index('id="smeLaborTimeDetail"'), page.index('id="smeLaborTimeResults"'))
        self.assertIn("draw(true)", page)
        self.assertIn("detail.scrollIntoView({behavior:'smooth',block:'start'})", page)

    def test_budget_detail_and_calculation_precede_results_and_auto_scroll(self):
        self.assertLess(SOURCE.index('id="smeBudgetLaborSelected"'), SOURCE.index('id="smeBudgetLaborResults"'))
        self.assertLess(SOURCE.index('id="smeBudgetLaborCalculation"'), SOURCE.index('id="smeBudgetLaborResults"'))
        self.assertIn("selectedBox.scrollIntoView({behavior:'smooth',block:'start'})", SOURCE)


    def test_grouped_average_clutch_catalog_covers_sedan_pickup_4x2_and_4x4(self):
        for row_id in ["clutch-sedan", "clutch-pickup-4x2", "clutch-pickup-4x4", "gearbox-pickup-4x2", "gearbox-pickup-4x4"]:
            self.assertIn("id:'" + row_id + "'", SOURCE)
        self.assertIn("Promedio agrupado SME", SOURCE)
        self.assertIn("No es una norma argentina", SOURCE)
        self.assertIn("No sumar el tiempo de caja por separado", SOURCE)

    def test_more_everyday_grouped_jobs_have_reference_hours(self):
        for row_id in [
            "gasket-head-diesel-4cyl", "valve-cover-gasket", "oil-pan-gasket",
            "valve-adjustment-8v", "radiator-replace", "coolant-hose",
            "accessory-belt-tensioner", "rear-shocks-pair", "front-control-arm",
            "stabilizer-links", "cv-axle", "rear-drum-brakes", "rear-disc-brakes",
            "brake-fluid-bleed", "brake-caliper", "air-filter", "cabin-filter",
            "fuel-filter", "spark-plugs-4cyl", "battery-replace", "fuel-pump", "ac-compressor"
        ]:
            self.assertIn("id:'" + row_id + "'", SOURCE)
            self.assertIn("status:'Promedio agrupado SME'", SOURCE)

    def test_grouped_average_records_include_scope_and_references(self):
        self.assertIn("sourceNote:'Comparativos externos", SOURCE)
        self.assertIn("sourceLinks:[{label:'Ford F-150 manual 4×4 · embrague'", SOURCE)
        self.assertIn("sourceLinks:[{label:'Ford Fiesta · pastillas delanteras'", SOURCE)
        self.assertIn("la tarifa la ingresás vos", SOURCE)
        self.assertIn("No se altera ningún presupuesto guardado", SOURCE)



    def test_every_labor_entry_gets_normalized_source_confidence_and_variant_metadata(self):
        self.assertIn("function smeLaborTimeMetadata(item)", SOURCE)
        self.assertIn("vehicleGroup:item.vehicleGroup||smeInferLaborTimeVehicleGroup(item)", SOURCE)
        self.assertIn("variants:item.variants||item.application", SOURCE)
        self.assertIn("sourceName", SOURCE)
        self.assertIn("confidenceDetail", SOURCE)
        self.assertIn("publishedHours:Number.isFinite(item.publishedHours)?item.publishedHours:null", SOURCE)
        self.assertIn("SME_LABOR_TIME_CATALOG.forEach(smeLaborTimeMetadata)", SOURCE)

    def test_catalog_can_be_filtered_by_work_family_and_vehicle_group(self):
        self.assertIn('id="smeLaborTimeFamilyFilter"', SOURCE)
        self.assertIn('id="smeLaborTimeVehicleFilter"', SOURCE)
        self.assertIn("familyFilter.addEventListener('change',()=>draw())", SOURCE)
        self.assertIn("vehicleFilter.addEventListener('change',()=>draw())", SOURCE)
        self.assertIn("item.family===familyFilter.value", SOURCE)
        self.assertIn("item.vehicleGroup===vehicleFilter.value", SOURCE)

    def test_selected_detail_shows_source_hours_confidence_and_applicable_variants(self):
        self.assertIn("<strong>Confianza:</strong>", SOURCE)
        self.assertIn("<strong>Fuente principal:</strong>", SOURCE)
        self.assertIn("<strong>Horas publicadas:</strong>", SOURCE)
        self.assertIn("<strong>Aplicación/variantes:</strong>", SOURCE)
        self.assertIn("No hay una hora única publicada para este promedio", SOURCE)

    def test_published_hours_are_only_shown_when_the_value_exists(self):
        self.assertIn("if(Number.isFinite(item.publishedHours))return 'Tiempo publicado: '+smeLaborHoursLabel(item.publishedHours)", SOURCE)


    def test_quick_quote_supports_single_price_and_ranges(self):
        self.assertIn('id="smeQuickUsePriceRange" name="usarRangoPrecio"', SOURCE)
        self.assertIn('id="smeQuickPriceRangeFields" hidden', SOURCE)
        self.assertIn("rangeRequested=fd.get('usarRangoPrecio')==='on'", SOURCE)
        self.assertIn("max=rangeRequested?maxEntered:min", SOURCE)
        self.assertIn("smeOrientativePriceLabel(min,max)", SOURCE)
        self.assertIn("Importe único sujeto a inspección y confirmación del alcance", SOURCE)
        self.assertIn("PRECIO ESTIMADO", SOURCE)

    def test_quick_estimator_draft_refreshes_search_and_table_navigation_is_resilient(self):
        self.assertIn("restored.forEach(el=>{try{el.dispatchEvent(new Event", SOURCE)
        self.assertIn("smeInitQuickLaborEstimate(form)", SOURCE)
        self.assertIn("function smeLaborTimeSearchText(item)", SOURCE)
        self.assertNotIn("document.addEventListener('click',event=>{const button=event.target?.closest?.('#smeOpenLaborTimesFromQuick')", SOURCE)
        self.assertIn("const openLaborTimesButton=document.getElementById('smeOpenLaborTimesFromQuick')", SOURCE)
        self.assertIn("smeReturnToQuickQuote=true;smeNavigateTo('tiempos')", SOURCE)

    def test_quick_installment_offer_shows_calculated_amount_per_payment(self):
        self.assertIn('id="smeQuickInstallmentPreview"', SOURCE)
        self.assertIn("const repaintQuickInstallments=()=>", SOURCE)
        self.assertIn("count+' cuotas de '+smeOrientativePriceLabel(low,high)+' cada una", SOURCE)


if __name__ == "__main__":
    unittest.main()
