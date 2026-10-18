"""Regresiones críticas de validación y conservación de formularios SME."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "index.html").read_text(encoding="utf-8")


class FormValidationPreservationTests(unittest.TestCase):
    def test_admin_setup_is_reachable_after_validation(self):
        self.assertIn("if(smeUsers.some(u=>u.username===username)){", SOURCE)
        self.assertIn("if(migration){\n     const legacy=JSON.parse(localStorage.getItem(SME_AUTH_KEY)||'null');", SOURCE)
        self.assertIn("localStorage.setItem(SME_USERS_KEY,JSON.stringify([admin]));", SOURCE)
        self.assertNotIn(
            "smeAuthInlineError(form,'Ese usuario ya existe. Elegí otro.','username');return\n    if(migration)",
            SOURCE,
        )

    def test_auth_validation_keeps_inline_feedback_and_values(self):
        self.assertIn("function smeAuthInlineError(form,message,fieldName='',clearFieldName='')", SOURCE)
        self.assertIn("smeAuthInlineError(form,'Ingresá un DNI válido de 7 u 8 números.','dni');return", SOURCE)
        self.assertIn("smeAuthInlineError(form,'Las contraseñas nuevas no coinciden.','password2');return", SOURCE)

    def test_common_record_form_has_inline_error_region(self):
        self.assertIn('<div class="form-error" data-form-error role="alert" aria-live="polite" style="color:#e6a39a;font-weight:600;margin:8px 0"></div>', SOURCE)
        self.assertIn("smeFormError(form,'El cliente seleccionado no coincide con el propietario asociado al vehículo.", SOURCE)

    def test_user_form_validation_is_inline_and_field_specific(self):
        self.assertIn("smeFormError(form,'Ingresá un DNI válido de 7 u 8 números.','dni');return", SOURCE)
        self.assertIn("smeFormError(form,'Las contraseñas no coinciden.','password2');return", SOURCE)
        self.assertIn("smeFormError(form,'Ya existe un usuario con ese nombre.','username');return", SOURCE)

    def test_save_failure_keeps_visible_error_instead_of_rebuilding_form(self):
        self.assertIn("async function save(){try{await storage.save(db);return true}catch(e){console.error('Error guardando datos:',e);alert('No se pudieron guardar los datos.", SOURCE)
        self.assertIn("if(!(await save())){db=JSON.parse(before);return}render()", SOURCE)


    def test_android_keyboard_fix_uses_visual_viewport_offsets(self):
        self.assertIn("const visibleTop=vv?vv.offsetTop:0;", SOURCE)
        self.assertIn("const visibleBottom=vv?vv.offsetTop+vv.height:window.innerHeight;", SOURCE)

    def test_android_keyboard_fix_uses_non_smooth_nearest_scroll(self):
        self.assertIn("active.scrollIntoView({block:'nearest',inline:'nearest',behavior:'auto'});", SOURCE)
        self.assertIn("window.scrollBy({top:scrollDelta,behavior:'auto'});", SOURCE)

    def test_android_keyboard_mode_is_removed_after_keyboard_closes(self):
        self.assertIn("document.body.classList.toggle('sme-keyboard-open',keyboardOpen);", SOURCE)
        self.assertIn("vv?.addEventListener('resize',adjust);vv?.addEventListener('scroll',adjust);", SOURCE)


if __name__ == "__main__":
    unittest.main()
