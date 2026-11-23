#!/usr/bin/env python3
"""Auditor de calidad de datos SQLite SME: reporta, no modifica."""
from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path

def audit_quality(connection: sqlite3.Connection) -> list[dict]:
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    findings=[]
    # Duplicates are checked only for populated values and normalized by trim/case.
    checks=(
        ("clientes","documento","duplicate_value","Documento duplicado"),
        ("vehiculos","patente","duplicate_value","Patente duplicada"),
        ("trabajos","numero","duplicate_value","Número de trabajo duplicado"),
        ("presupuestos","numero","duplicate_value","Número de presupuesto duplicado"),
    )
    for table,col,kind,label in checks:
        if table not in tables: continue
        cols={r[1] for r in connection.execute(f"PRAGMA table_info({table})")}
        if col not in cols: continue
        rows=connection.execute(
            f"""SELECT TRIM(CAST({col} AS TEXT)) AS normalized, COUNT(*), GROUP_CONCAT(id)
                FROM {table} WHERE {col} IS NOT NULL AND TRIM(CAST({col} AS TEXT))<>''
                GROUP BY UPPER(TRIM(CAST({col} AS TEXT))) HAVING COUNT(*)>1"""
        )
        for value,count,ids in rows:
            findings.append({"type":kind,"label":label,"table":table,"column":col,"value":value,"count":count,"record_ids":ids})
    # Required-looking fields are treated as warnings, never as schema violations.
    empties=(
        ("clientes","nombre","Cliente sin nombre"),
        ("vehiculos","patente","Vehículo sin patente"),
        ("trabajos","estado","Trabajo sin estado"),
    )
    for table,col,label in empties:
        if table not in tables: continue
        cols={r[1] for r in connection.execute(f"PRAGMA table_info({table})")}
        if col not in cols: continue
        for record_id,value in connection.execute(f"SELECT id,{col} FROM {table} WHERE {col} IS NULL OR TRIM(CAST({col} AS TEXT))=''"):
            findings.append({"type":"missing_value","label":label,"table":table,"column":col,"record_ids":str(record_id)})
    return findings

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database",type=Path,help="Archivo SQLite SME")
    args=parser.parse_args()
    if not args.database.is_file(): parser.error(f"No existe el archivo: {args.database}")
    con=sqlite3.connect(f"file:{args.database.resolve()}?mode=ro",uri=True)
    try: findings=audit_quality(con)
    finally: con.close()
    if not findings:
        print("Control de calidad finalizado: no se encontraron alertas en los campos revisados.")
        return 0
    print(f"Se encontraron {len(findings)} alertas (solo lectura):")
    for f in findings:
        ids=f.get("record_ids","")
        print(f"- {f['label']}: tabla={f['table']} valor={f.get('value','')} registros={ids}")
    return 1
if __name__=="__main__":
    raise SystemExit(main())
