#!/usr/bin/env python3
"""Auditor de calidad de datos SQLite SME: reporta, no modifica."""
from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path

# severity and recommended manual review order
DUPLICATE_SEVERITY = {
    ("clientes", "documento"): "alta",
    ("vehiculos", "patente"): "alta",
    ("trabajos", "numero"): "media",
    ("presupuestos", "numero"): "media",
}
EMPTY_SEVERITY = "media"

def audit_quality(connection: sqlite3.Connection) -> list[dict]:
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    findings=[]
    checks=(
        ("clientes","documento","duplicate_value","Documento duplicado"),
        ("vehiculos","patente","duplicate_value","Patente duplicada"),
        ("trabajos","numero","duplicate_value","Número de trabajo duplicado"),
        ("presupuestos","numero","duplicate_value","Número de presupuesto duplicado"),
    )
    for table,col,kind,label in checks:
        if table not in tables: continue
        cols={r[1] for r in connection.execute(f"PRAGMA table_info({table})")}
        if col not in cols or "id" not in cols: continue
        rows=connection.execute(
            f"""SELECT TRIM(CAST({col} AS TEXT)), COUNT(*), GROUP_CONCAT(id)
                FROM {table} WHERE {col} IS NOT NULL AND TRIM(CAST({col} AS TEXT))<>''
                GROUP BY UPPER(TRIM(CAST({col} AS TEXT))) HAVING COUNT(*)>1"""
        )
        for value,count,ids in rows:
            severity=DUPLICATE_SEVERITY[(table,col)]
            findings.append({"type":kind,"severity":severity,"label":label,"table":table,
                            "column":col,"value":value,"count":count,"record_ids":ids,
                            "action":"Comparar registros y confirmar si son duplicados reales; no fusionar automáticamente."})
    empties=(
        ("clientes","nombre","Cliente sin nombre"),
        ("vehiculos","patente","Vehículo sin patente"),
        ("trabajos","estado","Trabajo sin estado"),
    )
    for table,col,label in empties:
        if table not in tables: continue
        cols={r[1] for r in connection.execute(f"PRAGMA table_info({table})")}
        if col not in cols or "id" not in cols: continue
        for record_id,value in connection.execute(f"SELECT id,{col} FROM {table} WHERE {col} IS NULL OR TRIM(CAST({col} AS TEXT))=''"):
            findings.append({"type":"missing_value","severity":EMPTY_SEVERITY,"label":label,
                            "table":table,"column":col,"record_ids":str(record_id),
                            "action":"Revisar el registro y completar el dato solo si se confirma."})
    return findings

def print_report(findings: list[dict]) -> None:
    counts={"alta":0,"media":0,"baja":0}
    for f in findings: counts[f.get("severity","baja")]+=1
    print("RESUMEN DE CALIDAD")
    print(f"Total alertas: {len(findings)} | Alta: {counts['alta']} | Media: {counts['media']} | Baja: {counts['baja']}")
    if not findings:
        print("Sin alertas en los campos revisados.")
        return
    order={"alta":0,"media":1,"baja":2}
    for f in sorted(findings,key=lambda x:order.get(x.get("severity","baja"),3)):
        print(f"[{f['severity'].upper()}] {f['label']} | tabla={f['table']} | valor={f.get('value','')} | registros={f.get('record_ids','')}")
        print(f"  Recomendación: {f['action']}")

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database",type=Path,help="Archivo SQLite SME")
    args=parser.parse_args()
    if not args.database.is_file(): parser.error(f"No existe el archivo: {args.database}")
    con=sqlite3.connect(f"file:{args.database.resolve()}?mode=ro",uri=True)
    try: findings=audit_quality(con)
    finally: con.close()
    print_report(findings)
    return 1 if findings else 0
if __name__=="__main__":
    raise SystemExit(main())
