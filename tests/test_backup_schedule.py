"""Regresiones mínimas para la política de respaldos automáticos de SME.

Estas pruebas inspeccionan los puntos de integración del código fuente; no
sustituyen las pruebas en Android ni verifican el funcionamiento real del SO.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
SOURCE = HTML.read_text(encoding="utf-8")


class BackupScheduleSourceTests(unittest.TestCase):
    def test_daily_and_monthly_names_are_date_scoped(self):
        self.assertIn("SME_BACKUP_DAILY_PREFIX='SME-automatico-diario-'", SOURCE)
        self.assertIn("SME_BACKUP_MONTHLY_PREFIX='SME-historico-mensual-'", SOURCE)
        self.assertIn("smeBackupDateKey(now)", SOURCE)
        self.assertIn("smeBackupMonthKey(now)", SOURCE)

    def test_retention_policy_matches_requirements(self):
        self.assertIn("SME_BACKUP_RETENTION_DAYS=7", SOURCE)
        self.assertIn("SME_BACKUP_RETENTION_MONTHS=60", SOURCE)
        self.assertIn("smePruneAutomaticBackups(SME_BACKUP_DAILY_PREFIX,SME_BACKUP_RETENTION_DAYS)", SOURCE)
        self.assertIn("smePruneAutomaticBackups(SME_BACKUP_MONTHLY_PREFIX,SME_BACKUP_RETENTION_MONTHS)", SOURCE)

    def test_automatic_backup_runs_only_after_native_storage_is_ready(self):
        self.assertIn("db=await storage.load(emptyDB);", SOURCE)
        self.assertIn("if(storage?.isNative){void smeRunAutomaticBackups()}", SOURCE)
        self.assertIn("const serialized=smeValidateBackupSnapshot(db);", SOURCE)

    def test_backup_is_read_back_and_parsed_after_write(self):
        self.assertIn("await Filesystem.writeFile({path:name,data:serialized,directory:Directory.Documents,encoding:Encoding.UTF8})", SOURCE)
        self.assertIn("await Filesystem.readFile({path:name,directory:Directory.Documents,encoding:Encoding.UTF8})", SOURCE)
        self.assertIn("JSON.parse(typeof readback.data==='string'?readback.data:'')", SOURCE)

    def test_backup_validation_rejects_missing_and_duplicate_ids(self):
        self.assertIn("throw new Error('Registro sin identificador en '+key+'.')", SOURCE)
        self.assertIn("throw new Error('Identificador duplicado '+id+' en '+key+'.')", SOURCE)

    def test_manual_backup_preserves_single_owner_for_reinstallation(self):
        self.assertIn("function smeCreatePortableBackup()", SOURCE)
        self.assertIn("_smeBackupMetadata:{appId:'servicios-mecanicos-enzo',formatVersion:2", SOURCE)
        self.assertIn("ownerId:String(owner?.id||''),users", SOURCE)
        self.assertIn("smeRecoverOwnerButton", SOURCE)
        self.assertIn("Cuenta propietaria recuperada desde el respaldo", SOURCE)
        self.assertIn("debe contener una única cuenta dueña", SOURCE)

    def test_android_file_picker_does_not_lock_session_during_restore(self):
        self.assertIn("smeBeginFilePicker();fileInput.click()", SOURCE)
        self.assertIn("if(smeFilePickerPending)return;", SOURCE)
        self.assertIn("smeFinishFilePicker();if(!smeCanBackup('edit'))", SOURCE)
        self.assertIn("if(!smeAuthenticated||smeFilePickerPending)return;", SOURCE)

    def test_full_sqlite_restore_is_native_validated_and_reversible(self):
        plugin = (ROOT / "scripts/templates/SmeBackupPlugin.java.template").read_text(encoding="utf-8")
        storage = (ROOT / "src/storage/sqlite-store.js").read_text(encoding="utf-8")
        configure = (ROOT / "scripts/configure-android-backups.mjs").read_text(encoding="utf-8")
        self.assertIn("pickAndValidateRestore", plugin)
        self.assertIn("PRAGMA integrity_check", plugin)
        self.assertIn("REQUIRED_TABLES", plugin)
        self.assertIn("PRAGMA user_version", plugin)
        self.assertIn("sha256(bytes)", plugin)
        self.assertIn("SME-pre-restauracion-", plugin)
        self.assertIn("renameTo(database)", plugin)
        self.assertIn("registerPlugin(SmeBackupPlugin.class)", configure)
        self.assertIn("SmeBackupPlugin.java.template", configure)
        self.assertIn("async close()", storage)
        self.assertIn("Restaurar copia completa (.db)", SOURCE)
        self.assertIn("smeStyledConfirm('Restaurar copia completa'", SOURCE)
        self.assertIn("SmeBackup.commitRestore", SOURCE)
        self.assertIn("checkpointDatabase(database)", plugin)
        self.assertIn("PRAGMA wal_checkpoint(TRUNCATE)", plugin)
        self.assertIn('new File(database.getAbsolutePath() + "-wal")', plugin)
        self.assertIn('new File(database.getAbsolutePath() + "-shm")', plugin)
    def test_startup_snapshot_is_supplemented_by_native_background_worker(self):
        # JavaScript startup snapshots alone do not run with the app closed.
        self.assertIn("no sustituye un trabajador nativo Android", SOURCE)
        self.assertIn("if(storage?.isNative){void smeRunAutomaticBackups()}", SOURCE)
        workflow = (ROOT / ".github/workflows/build-android-apk.yml").read_text(encoding="utf-8")
        self.assertIn("node scripts/configure-android-backups.mjs", workflow)
        worker = (ROOT / "scripts/templates/SmeBackupWorker.java.template").read_text(encoding="utf-8")
        self.assertIn("VACUUM INTO", worker)
        self.assertIn("PRAGMA integrity_check", worker)
        self.assertIn("SME-auto-diario-", worker)
        self.assertIn("SME-historico-mensual-", worker)


if __name__ == "__main__":
    unittest.main(verbosity=2)
