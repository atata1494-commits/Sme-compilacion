#!/usr/bin/env python3
"""Compara inventarios de dos respaldos SQLite SME en solo lectura; nunca modifica archivos."""
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
from urllib.parse import quote

def inspect_db(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"No existe: {path}")
    uri=f"file:{quote(str(path.resolve()), safe='/:')}?mode=ro"
    con=sqlite3.connect(uri, uri=True)
    try:
        integrity=con.execute("PRAGMA integrity_check").fetchall()
        tables={}
        for name, sql in con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            safe=name.replace('"','""')
            count=con.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0]
            tables[name]={"rows":count,"schema_sql":sql or ""}
        schema_blob="\n".join(f"{n}:{t['schema_sql']}" for n,t in tables.items())
        return {"integrity":"ok" if integrity==[("ok",)] else str(integrity),
                "tables":tables,"schema_sha256":hashlib.sha256(schema_blob.encode()).hexdigest()}
    finally:
        con.close()

def compare(old_path: Path, new_path: Path):
    old=inspect_db(old_path); new=inspect_db(new_path)
    old_names=set(old["tables"]); new_names=set(new["tables"])
    missing=sorted(old_names-new_names); added=sorted(new_names-old_names)
    schema_changed=sorted(n for n in old_names & new_names
        if old["tables"][n]["schema_sql"] != new["tables"][n]["schema_sql"])
    row_changes=[]
    for name in sorted(old_names & new_names):
        before=old["tables"][name]["rows"]; after=new["tables"][name]["rows"]
        if before != after:
            row_changes.append({"table":name,"older_rows":before,"newer_rows":after,"delta":after-before})
    issues=[]
    if old["integrity"]!="ok": issues.append(f"Integridad del respaldo anterior: {old['integrity']}")
    if new["integrity"]!="ok": issues.append(f"Integridad del respaldo nuevo: {new['integrity']}")
    if missing: issues.append("Hay tablas que estaban en el respaldo anterior y faltan en el nuevo.")
    if schema_changed: issues.append("Hay cambios de esquema que requieren revisión.")
    return {"status":"REQUIRES_MANUAL_REVIEW","older_backup":str(old_path),"newer_backup":str(new_path),
      "older_integrity":old["integrity"],"newer_integrity":new["integrity"],
      "older_schema_sha256":old["schema_sha256"],"newer_schema_sha256":new["schema_sha256"],
      "tables_missing_in_new":missing,"tables_added_in_new":added,"schema_changed":schema_changed,
      "row_count_changes":row_changes,"warnings":issues,
      "notice":"Comparación de inventario solamente: no compara contenido fila por fila, no determina cuál respaldo es correcto y no modifica/restaura bases."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("older_backup",type=Path); p.add_argument("newer_backup",type=Path)
    p.add_argument("--report",type=Path,help="Opcional: guardar el informe JSON")
    a=p.parse_args()
    try: report=compare(a.older_backup,a.newer_backup)
    except (OSError,sqlite3.Error) as e:
        print(json.dumps({"status":"BLOCKED","error":str(e)},ensure_ascii=False,indent=2)); return 1
    out=json.dumps(report,ensure_ascii=False,indent=2); print(out)
    if a.report: a.report.write_text(out,encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
