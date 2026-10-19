"""Pruebas de regresión para el Inicio y la navegación de SME."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


class SmeHomeNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX.read_text(encoding="utf-8")

    def test_fixed_navigation_uses_five_logical_sections(self):
        self.assertIn('data-page="registros"', self.html)
        self.assertIn('data-page="taller"', self.html)
        self.assertIn('data-page="gestion"', self.html)
        self.assertIn('data-page="mas"', self.html)
        self.assertIn('</span>Registros</button>', self.html)
        self.assertIn('</span>Taller</button>', self.html)
        self.assertIn('</span>Gestión</button>', self.html)
        self.assertIn('</span>Más</button>', self.html)
        nav = self.html[self.html.index('<nav id="nav"'):self.html.index('</nav>', self.html.index('<nav id="nav"'))]
        self.assertEqual(nav.count('data-page='), 5)

    def test_records_workshop_and_management_have_separate_hubs(self):
        for hub in ("Registros", "Taller", "Gestión"):
            self.assertIn("smeRenderHubPage('" + hub + "'", self.html)
        self.assertIn("if(key==='registros')return ['clientes','vehiculos','trabajos'].some", self.html)
        self.assertIn("if(key==='taller')return ['recepciones','diagnosticos','asistencias','terceros','tareas','avisos','gastos'].some", self.html)
        self.assertIn("function smeRenderHubPage", self.html)

    def test_dashboard_is_asymmetric_and_can_leave_space_empty(self):
        self.assertIn("home-layout", self.html)
        self.assertIn("home-feature", self.html)
        self.assertIn(",feature=", self.html)
        self.assertIn("metrics.length?", self.html)

    def test_dashboard_respects_task_and_attendance_permissions_and_shows_global_notices(self):
        self.assertIn("smeCan('tareas','view')", self.html)
        self.assertIn("smeCan('asistencias','view')", self.html)
        self.assertIn("if(key==='avisos'&&action!=='edit')return true;", self.html)
        self.assertIn("const notices=(db.avisos||[]).filter", self.html)

    def test_help_and_one_time_welcome_exist(self):
        self.assertIn('id="smeHelpButton"', self.html)
        self.assertIn("function smeShowContextHelp()", self.html)
        self.assertIn("function smeShowWelcomeIfNeeded()", self.html)
        self.assertIn("sme_welcome_state_v3_", self.html)
        self.assertIn("function smeShowWelcomeTourStep(step)", self.html)
        self.assertIn("function smeBuildVisualTour()", self.html)
        self.assertIn("const candidates=[", self.html)
        self.assertIn("].filter(item=>smeCan(item.key,'view'));", self.html)
        self.assertIn("if(steps.length>=4)break;", self.html)
        self.assertIn("key:'mas',page:'mas',title:'Más: permisos y respaldos'", self.html)
        self.assertIn("page:'taller'", self.html)
        self.assertIn("page:'gestion'", self.html)
        self.assertIn("return steps.slice(0,5)", self.html)
        self.assertIn("const workAccess=smeCan('trabajos','view')", self.html)
        self.assertIn("title:'Inicio: lo principal del día'", self.html)

        self.assertIn("sme-tour-spotlight", self.html)
        # El recorrido nuevo avanza con gestos táctiles, no con botones inferiores.
        self.assertIn("sme-tour-hint", self.html)
        self.assertIn("touchstart", self.html)
        self.assertIn("touchend", self.html)
        self.assertIn("smeShowWelcomeTourStep(smeVisualTourIndex+1)", self.html)
        self.assertIn("smeShowWelcomeTourStep(smeVisualTourIndex-1)", self.html)
        self.assertNotIn("data-tour-next", self.html)
        # La compactación existe solo durante el recorrido y se revierte al cerrarlo.
        self.assertIn("document.body.classList.add('sme-tour-layout')", self.html)
        self.assertIn("document.body.classList.remove('sme-tour-layout')", self.html)
        self.assertIn("smeCan(key,'view')", self.html)
        self.assertIn("smeCloseVisualTour()", self.html)
        self.assertIn("function smeSkipWelcome()", self.html)
        self.assertIn("Number(state.skippedAt)||1)+2", self.html)
        self.assertIn("reminderShown", self.html)
        self.assertIn("Omitir por ahora", self.html)

    def test_visual_tour_descriptions_do_not_overlap_spotlights_or_each_other(self):
        self.assertIn("const targetBoxes=targets.map(t=>", self.html)
        self.assertIn("const nav=document.querySelector('#nav')", self.html)
        self.assertIn("targetBoxes.some(t=>intersects(box,t,14))", self.html)
        self.assertIn("placed.some(p=>intersects(box,p,8))", self.html)
        self.assertIn("const findPosition=()=>", self.html)
        self.assertIn("if(chosen){", self.html)
        self.assertIn("note.remove()", self.html)

    def test_related_records_can_be_opened_from_record_cards(self):
        self.assertIn("function smeRelatedButtons(key,o)", self.html)
        self.assertIn("data-related-target", self.html)
        self.assertIn("function smeRelatedMatches(key,o,f)", self.html)

    def test_new_users_get_editable_recommended_permission_profiles(self):
        self.assertIn("function smeRecommendedPermissions(area,jobTitle)", self.html)
        self.assertIn("function smeApplyRecommendedPermissions(form)", self.html)
        self.assertIn("podés cambiar cada permiso antes de guardar", self.html)

    def test_user_name_and_surname_are_separate_fields(self):
        self.assertIn('id="smeUserFirstName" name="firstName"', self.html)
        self.assertIn('id="smeUserLastName" name="lastName"', self.html)
        self.assertIn("username,firstName,lastName,name,dni,phone,area,jobTitle", self.html)
        self.assertIn("function smeUserNameParts(user)", self.html)

    def test_user_confirmation_uses_sme_styled_preview_not_native_confirm(self):
        self.assertIn("function smeUserPreviewDialog(user,mode='view')", self.html)
        self.assertIn(".sme-review-overlay", self.html)
        self.assertIn("Confirmar y guardar", self.html)
        self.assertIn("Volver a editar", self.html)
        self.assertNotIn("confirm('Revisá el perfil de ", self.html)
        self.assertNotIn("¿Guardar estos permisos?", self.html)

    def test_registered_users_have_a_profile_preview_action(self):
        self.assertIn('data-user-view="', self.html)
        self.assertIn(">Ver perfil</button>", self.html)
        self.assertIn("if(action==='edit')smeUserPage(target.id)", self.html)

    def test_dashboard_uses_distinct_icons_for_tasks_and_active_orders(self):
        self.assertIn("listChecks:'<path", self.html)
        self.assertIn("clipboardList:'<rect", self.html)
        self.assertIn("label.startsWith('Órdenes')?'activeOrders'", self.html)
        self.assertIn("iconSvg('listChecks',22)", self.html)
        self.assertIn("target==='tareas'?'listChecks'", self.html)

    def test_quick_access_does_not_duplicate_fixed_bottom_navigation(self):
        self.assertIn("const quickChoices=[['tareas','Tareas','listChecks']", self.html)
        self.assertIn("['agenda','Agenda','calendar']", self.html)
        self.assertIn("['presupuestos','Presupuestos','receipt']", self.html)
        self.assertNotIn("quick.push('<button data-go=\"clientes\"", self.html)
        self.assertNotIn("quick.push('<button data-go=\"vehiculos\"", self.html)
        self.assertNotIn("quick.push('<button data-go=\"trabajos\"", self.html)

    def test_notice_widget_is_always_available_to_every_user(self):
        self.assertIn("if(key==='avisos'&&action!=='edit')return true;", self.html)
        self.assertIn("const notices=(db.avisos||[]).filter", self.html)
        self.assertIn("home-widget home-notices-widget", self.html)
        self.assertIn("Sin avisos nuevos.", self.html)
        self.assertIn("home-widget-empty", self.html)
        self.assertIn(".home-widget-empty{padding:7px 0!important", self.html)
        self.assertIn(".home-quick-grid button{min-height:58px", self.html)
        self.assertIn(".home-shift p{margin:5px 0 2px", self.html)
        self.assertIn("Ver todos los avisos", self.html)
        self.assertIn("const items=(db.avisos||[]).slice().sort", self.html)
        self.assertIn("noticesWidget+'<div class=\"home-layout\">", self.html)

    def test_notice_widget_has_a_dedicated_bell_icon(self):
        self.assertIn("bell:'<path", self.html)
        self.assertIn("iconSvg('bell',22)", self.html)

    def test_customer_and_user_icons_are_visually_distinct(self):
        self.assertIn("userRound:'<circle", self.html)
        self.assertIn("idCard:'<rect", self.html)
        self.assertIn("target==='clientes'?'userRound'", self.html)
        self.assertIn("target==='usuarios'?'users'", self.html)
        self.assertIn("value:'Dirección y Supervisión',icon:'idCard'", self.html)

    def test_safety_risk_has_a_distinct_no_risk_option_and_sme_picker(self):
        self.assertIn("['sin_riesgo','Sin riesgo de seguridad'", self.html)
        self.assertIn("smeShowChoiceDialog('Riesgo de seguridad'", self.html)
        self.assertIn("name=\"riesgoSeguridad\" value=\"sin_evaluar\"", self.html)
        self.assertNotIn('<label>Riesgo de seguridad<select name="riesgoSeguridad">', self.html)

    def test_biometric_warning_uses_sme_styled_confirmation(self):
        self.assertIn("function smeStyledConfirm(title,message)", self.html)
        self.assertIn(".sme-dialog-backdrop{", self.html)
        self.assertIn("await smeStyledConfirm('Seguridad de la huella'", self.html)
        self.assertNotIn("const personal=confirm('SEGURIDAD:", self.html)

    def test_every_user_can_view_and_punch_attendance_but_schedule_is_admin_only(self):
        self.assertIn("if(key==='asistencias')return action==='view'||!!smeCurrentUser.isPrimary;", self.html)
        self.assertIn('id="smeIn"', self.html)
        self.assertIn('id="smeBreakIn"', self.html)
        self.assertIn('id="smeBreakOut"', self.html)
        self.assertIn('id="smeOut"', self.html)
        self.assertIn("(admin?'<section class=\"panel\"><h3>Configurar horario por integrante</h3>", self.html)
        self.assertIn("if(!admin)return;const fd=new FormData(e.currentTarget)", self.html)
 

    def test_recommended_permissions_follow_minimum_access_by_role(self):
        self.assertIn("function smeRecommendedPermissions(area,jobTitle){", self.html)
        self.assertIn("set(['vehiculos','trabajos'],'view');", self.html)
        self.assertIn("set(['diagnosticos','avisos','asistencias'],'edit');", self.html)
        self.assertIn("if(isReception){", self.html)
        self.assertIn("if(isAdminArea){", self.html)
        self.assertIn("if(isCleaning){", self.html)
        self.assertIn("// Perfiles nuevos o no reconocidos comienzan sin acceso.", self.html)

    def test_task_management_is_not_recommended_for_cleaning_or_regular_mechanics(self):
        self.assertIn("set(['tareas'],'view');", self.html)
        self.assertIn("if(isWorkshopLead){", self.html)
        self.assertIn("if(isCleaning){", self.html)
        self.assertNotIn("set(['tareas'],'edit');", self.html)

    def test_native_alert_confirm_and_prompt_are_centralized_in_sme_dialogs(self):
        self.assertIn("function smeShowMessage(title,message,kind='info')", self.html)
        self.assertIn("window.alert=function(message){void smeShowMessage", self.html)
        self.assertIn("function smeStyledConfirm(title,message)", self.html)
        self.assertIn("function smeStyledPrompt(title,message,initialValue='')", self.html)
        self.assertNotIn("confirm(", self.html)
        self.assertNotIn("prompt(", self.html)
        self.assertIn("await smeStyledPrompt(", self.html)
        self.assertIn("await smeStyledConfirm(", self.html)
        self.assertIn("sme-dialog-backdrop", self.html)
        self.assertIn("sme-dialog-card", self.html)


    def test_notice_selectors_offer_discreet_optional_contextual_help(self):
        self.assertIn("function smeShowChoiceDialog(title,message,choices,selected,helpText='')", self.html)
        self.assertIn("class=\"sme-choice-help\"", self.html)
        self.assertIn("class=\"sme-help-mark\"", self.html)
        self.assertIn("class=\"sme-choice-help-text\" hidden", self.html)
        self.assertIn("data-notice-picker=\"responsableUsuarioId\"", self.html)
        self.assertIn("Es la persona que se encargará de revisar o resolver este aviso. Asignarla no significa que sea culpable.", self.html)
        self.assertIn("Clasificá el aviso según lo ocurrido:", self.html)
        self.assertIn("Si todavía no lo sabés, elegí “No estoy seguro”.", self.html)
        self.assertNotIn('<label>Responsable inicial<select name="responsableUsuarioId">', self.html)


    def test_welcome_is_checked_after_normal_authentication_and_biometric_login(self):
        self.assertIn("function smeShowWelcomeIfNeeded(){", self.html)
        self.assertIn("smeResetIdleTimer();\n   smeShowWelcomeIfNeeded();", self.html)
        self.assertIn("smeResetIdleTimer();smeShowWelcomeIfNeeded();", self.html)
        self.assertIn("sme_welcome_state_v3_", self.html)



    def test_contextual_help_covers_sensitive_and_operational_modules(self):
        start = self.html.index("function smeShowContextHelp()")
        end = self.html.index("function smeShowWelcomeIfNeeded()", start)
        help_function = self.html[start:end]
        for key in (
            "clientes", "vehiculos", "trabajos", "presupuestos", "caja",
            "cuentas", "agenda", "recepciones", "diagnosticos", "terceros",
            "tareas", "avisos", "asistencias", "gastos", "usuarios", "mas"
        ):
            self.assertIn(key + ":[", help_function)
        self.assertIn("permisos", help_function)
        self.assertIn("Solo el administrador principal", help_function)


    def test_hubs_obey_module_permissions_and_backup_restore_permissions(self):
        self.assertIn("if(key==='gestion')return ['presupuestos','tiempos','caja','cuentas','agenda'].some", self.html)
        self.assertIn("if(key==='respaldos')return smeCanBackup(action);", self.html)
        self.assertIn("key==='mas'&&(smeCan('usuarios','view')||smeCanBackup('view'))", self.html)
        self.assertIn("if(restoreDatabaseButton&&!smeCanBackup('edit'))restoreDatabaseButton.hidden=true", self.html)

    def test_backup_types_explain_portable_merge_and_full_restore(self):
        self.assertIn("La importación JSON combina registros nuevos y no reemplaza los existentes.", self.html)
        self.assertIn("restaurar esta copia sustituye la base de datos actual", self.html)
        self.assertIn("Exportar respaldo JSON", self.html)
        self.assertIn("Exportar copia completa SQLite (.db)", self.html)
        self.assertIn("Restaurar copia completa (.db)", self.html)
        self.assertIn("hasta 7 copias diarias y 60 mensuales", self.html)



    def test_session_lock_restores_the_last_section_after_biometric_unlock(self):
        self.assertIn("function smeRememberCurrentPage()", self.html)
        self.assertIn("if(smeAuthenticated&&page)localStorage.setItem(SME_RESUME_PAGE_KEY,page)", self.html)
        self.assertIn("page=smeGetResumePage();smeResetNavigation();smeUpdateSessionBar();render();smeApplyPermissions();", self.html)

    def test_quick_orientative_button_has_resilient_click_handling(self):
        self.assertIn("function smeSetOrientativeBudgetExpanded(toggle)", self.html)
        self.assertIn("event.target?.closest?.('#smeToggleOrientativeBudget')", self.html)
        self.assertIn("toggle.dataset.smeQuickToggleBound==='1'", self.html)
        self.assertIn("toggle.addEventListener('click',()=>smeSetOrientativeBudgetExpanded(toggle))", self.html)
        self.assertIn("try{if(quickForm&&smeCan('tiempos','view'))smeInitQuickLaborEstimate(quickForm)}catch(error)", self.html)

    def test_workshop_tiles_and_dashboard_metrics_use_distinct_icons(self):
        self.assertIn("target==='recepciones'?'carReception'", self.html)
        self.assertIn("target==='trabajos'?'clipboardList'", self.html)
        self.assertIn("carReception:", self.html)
        self.assertIn("stroke-width=\".82\"", self.html)
        self.assertIn("M15.72 4.35", self.html)
        self.assertIn("M1.45 17.3", self.html)
        self.assertIn("M8.08 18.24", self.html)
        self.assertIn("vehiclesAtWork:", self.html)
        self.assertIn("m3.2 12.6", self.html)
        self.assertIn("a3.1 3.1 0 0 0 4.1 4.1l2.4 2.4", self.html)
        self.assertIn("target==='respaldos'?'databaseBackup'", self.html)
        self.assertIn("label.startsWith('Órdenes')?'activeOrders'", self.html)
        self.assertIn("label.startsWith('Vehículos')?'vehiclesAtWork'", self.html)
        self.assertIn("label.startsWith('Presupuestos')?'budgetFollowUp'", self.html)
        self.assertIn("'upcomingAppointment'", self.html)
        for icon_key in ("carReception:", "databaseBackup:", "activeOrders:", "vehiclesAtWork:", "budgetFollowUp:", "upcomingAppointment:"):
            self.assertIn(icon_key, self.html)

    def test_expense_approval_icon_is_not_the_cash_register_icon(self):
        self.assertIn("expenseApproval:'<path", self.html)
        self.assertIn("target==='gastos'?'expenseApproval'", self.html)
        self.assertIn("cashregister:'<rect", self.html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
