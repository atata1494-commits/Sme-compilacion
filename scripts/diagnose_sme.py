#!/usr/bin/env python3
"""Diagnóstico unificado SME: reúne auditorías SQLite de solo lectura."""
from __future__ import annotations
import argparse, importlib.util, json, sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULES={
 "relaciones":"audit_sqlite_relationships.py",
 "calidad":"audit_sqlite_data_quality.py",
 "finanzas":"audit_sqlite_financial.py",
}
def load_audit(name, filename):
    spec=importlib.util.spec_from_file_location(name, ROOT/"scripts"/filename)
    if spec is None or spec.loader is None: raise RuntimeError(f"No se pudo cargar {filename}")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def run_diagnostics(database:Path, backup:Path|None=None):
    report={"status":"REQUIRES_MANUAL_REVIEW","database":str(database),"audits":{},"backup_validation":None,"warnings":[]}
    if not database.is_file():
        report["status"]="BLOCKED"; report["warnings"].append("No se encontró la base de datos."); return report
    con=sqlite3.connect(f"file:{database.resolve()}?mode=ro",uri=True)
    try:
        for key,filename in MODULES.items():
            try:
                mod=load_audit("sme_"+key,filename)
                func={"relaciones":"audit_connection","calidad":"audit_quality","finanzas":"audit_financial"}[key]
                report["audits"][key]=mod.__dict__[func](con)
            except Exception as exc:
                report["warnings"].append(f"Auditoría {key} no pudo ejecutarse: {exc}")
    finally: con.close()
    if backup is not None:
        try:
            validator=load_audit("sme_backup_validator","validate_sme_backup.py")
            report["backup_validation"]=validator.validate_backup(backup)
        except Exception as exc:
            report["backup_validation"]=[f"Validación no pudo ejecutarse: {exc}"]
    count=sum(len(v) for v in report["audits"].values() if isinstance(v,list))
    report["summary"]={"findings":count,"audits_run":len(report["audits"]),"audit_failures":len(report["warnings"])}
    if report["warnings"] or report["backup_validation"]:
        report["status"]="BLOCKED"
    report["notice"]="Diagnóstico consolidado, solo lectura. No corrige, borra, migra ni restaura datos. Requiere revisión manual."
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("database",type=Path); ap.add_argument("--backup",type=Path)
    ap.add_argument("--report",type=Path,help="Guardar salida JSON")
    args=ap.parse_args()
    result=run_diagnostics(args.database,args.backup)
    output=json.dumps(result,ensure_ascii=False,indent=2); print(output)
    if args.report: args.report.write_text(output,encoding="utf-8")
    return 2 if result["status"]=="BLOCKED" else (1 if result["summary"]["findings"] else 0)
if __name__=="__main__": raise SystemExit(main())
