"""Pruebas estructurales para exportar/importar el catálogo de tiempos SME."""
from pathlib import Path
import unittest

SHELL = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class LaborCatalogTransferTests(unittest.TestCase):
    def test_backup_module_has_separate_catalog_tools(self):
        for text in (
            "Catálogos y datos maestros",
            "laborCatalogExportJsonBtn",
            "laborCatalogExportCsvBtn",
            "laborCatalogImportBtn",
            "laborCatalogImportFile",
        ):
            self.assertIn(text, SHELL)

    def test_export_preserves_catalog_metadata_and_supports_csv(self):
        self.assertIn("format:'SME_LABOR_TIME_CATALOG',schemaVersion:1", SHELL)
        self.assertIn("sourceLinks", SHELL)
        self.assertIn("smeLaborCatalogCsv(items)", SHELL)
        self.assertIn("SME-catalogo-tiempos-v1.json", SHELL)
        self.assertIn("SME-catalogo-tiempos-v1.csv", SHELL)

    def test_import_validates_ids_and_detects_duplicates(self):
        self.assertIn("identificadores duplicados", SHELL)
        self.assertIn("Cada operación debe tener un identificador y un nombre.", SHELL)
        self.assertIn("No se importó ningún cambio.", SHELL)

    def test_import_preview_protects_conflicts_and_never_deletes_missing_items(self):
        self.assertIn("Vista previa de importación", SHELL)
        self.assertIn("Las operaciones ausentes del archivo nunca se eliminan.", SHELL)
        self.assertIn("smeLaborCatalogComparable", SHELL)
        self.assertIn("¿actualizar esas operaciones con los datos del archivo?", SHELL.lower())

    def test_imported_additions_and_overrides_persist_between_sessions(self):
        self.assertIn("sme_labor_catalog_additions_v1", SHELL)
        self.assertIn("smeLoadLaborCatalogAdditions()", SHELL)
        self.assertIn("smePersistLaborCatalogAdditions()", SHELL)
        self.assertIn("SME_LABOR_CATALOG_BASELINE", SHELL)


if __name__ == "__main__":
    unittest.main()
