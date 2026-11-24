#!/usr/bin/env python3
"""Genera un expediente de revisión previo a recuperación. Nunca restaura ni modifica la BD."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/path)
    if spec is None or spec.loader is None: raise RuntimeError(f"No se pudo cargar {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()
def build_review(current_db, backup):
    validator=load_module("sme_validator","validate_sme_backup.py")
    previewer=load_module("sme_preview","preview_sme_recovery.py")
    report={"status":"REQUIRES_MANUAL_REVIEW","current_database":None,"backup":None,
            "validation_issues":[],"preview":None,
            "safety_notice":"Este informe no autoriza ni ejecuta restauración. No modifica ni reemplaza la base activa."}
    if not Path(current_db).is_file():
        report["validation_issues"].append("No se encontró la base de datos actual.")
    else:
        report["current_database"]={"path":str(current_db),"sha256":sha256(current_db),"bytes":Path(current_db).stat().st_size}
    if not Path(backup).is_file():
        report["validation_issues"].append("No se encontró el respaldo seleccionado.")
    else:
        report["backup"]={"path":str(backup),"sha256":sha256(backup),"bytes":Path(backup).stat().st_size}
        report["validation_issues"].extend(validator.validate_backup(Path(backup)))
        report["preview"]=previewer.preview_backup(Path(backup))
        report["validation_issues"].extend(report["preview"].get("warnings",[]))
    if report["validation_issues"]: report["status"]="BLOCKED"
    return report
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("current_db",type=Path); parser.add_argument("backup",type=Path)
    parser.add_argument("--report",type=Path,required=True,help="Ruta donde guardar el informe JSON")
    args=parser.parse_args()
    report=build_review(args.current_db,args.backup)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 1 if report["status"]=="BLOCKED" else 0
if __name__=="__main__": raise SystemExit(main())
