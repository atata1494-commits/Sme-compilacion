#!/usr/bin/env python3
"""Guarda snapshots históricos de diagnósticos SME, sin alterar la base examinada."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def load_diagnostics():
    spec=importlib.util.spec_from_file_location("sme_diagnose",ROOT/"scripts"/"diagnose_sme.py")
    if spec is None or spec.loader is None: raise RuntimeError("No se pudo cargar diagnose_sme.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def count_findings(report):
    return sum(len(v) for v in report.get("audits",{}).values() if isinstance(v,list))

def history_snapshot(database:Path,history_dir:Path,backup:Path|None=None):
    if not database.is_file(): raise FileNotFoundError(f"No existe la base: {database}")
    report=load_diagnostics().run_diagnostics(database,backup)
    now=datetime.now(timezone.utc)
    snapshot={"schema_version":1,"timestamp_utc":now.isoformat(timespec="seconds"),
              "database_name":database.name,"database_size_bytes":database.stat().st_size,
              "database_sha256":sha256(database),"status":report.get("status"),
              "summary":report.get("summary",{}),"finding_count":count_findings(report),
              "audit_findings":report.get("audits",{}),"warnings":report.get("warnings",[]),
              "backup_validation":report.get("backup_validation"),
              "notice":"Snapshot de diagnóstico. No certifica integridad funcional ni autoriza restauración."}
    history_dir.mkdir(parents=True,exist_ok=True)
    previous=sorted(history_dir.glob(f"{database.stem}_*.json"))
    previous_data=None
    if previous:
        try: previous_data=json.loads(previous[-1].read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): previous_data=None
    snapshot["comparison"]=None
    if previous_data:
        snapshot["comparison"]={"previous_file":previous[-1].name,
            "previous_sha256":previous_data.get("database_sha256"),
            "sha_changed":previous_data.get("database_sha256")!=snapshot["database_sha256"],
            "finding_delta":snapshot["finding_count"]-int(previous_data.get("finding_count",0)),
            "previous_findings":int(previous_data.get("finding_count",0)),
            "current_findings":snapshot["finding_count"],
            "status_changed":previous_data.get("status")!=snapshot["status"]}
    stamp=now.strftime("%Y%m%dT%H%M%SZ")
    output=history_dir/f"{database.stem}_{stamp}.json"
    counter=1
    while output.exists():
        output=history_dir/f"{database.stem}_{stamp}_{counter:02d}.json"; counter+=1
    output.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return snapshot,output

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("database",type=Path)
    ap.add_argument("--history-dir",type=Path,default=Path("sme_audit_history"))
    ap.add_argument("--backup",type=Path)
    args=ap.parse_args()
    try: snapshot,path=history_snapshot(args.database,args.history_dir,args.backup)
    except (OSError,RuntimeError) as exc: ap.error(str(exc))
    print(json.dumps(snapshot,ensure_ascii=False,indent=2))
    print(f"\nSnapshot guardado: {path}")
    return 2 if snapshot["status"]=="BLOCKED" else (1 if snapshot["finding_count"] else 0)
if __name__=="__main__": raise SystemExit(main())
