#!/usr/bin/env python3
"""Auditoría financiera SQLite SME de solo lectura; reporta inconsistencias potenciales."""
from __future__ import annotations
import argparse, sqlite3
from pathlib import Path

def audit_financial(connection: sqlite3.Connection) -> list[dict]:
    tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    findings=[]
    # Structural SQLite checks
    integrity=list(connection.execute("PRAGMA integrity_check"))
    if integrity and integrity[0][0]!="ok":
        findings.append({"severity":"alta","kind":"sqlite_integrity","message":str(integrity)})
    fk=list(connection.execute("PRAGMA foreign_key_check"))
    if fk:
        findings.append({"severity":"alta","kind":"foreign_key","message":str(fk)})
    if "presupuestos" in tables:
        cols={r[1] for r in connection.execute("PRAGMA table_info(presupuestos)")}
        if {"id","mano_obra_centavos","repuestos_centavos","importe_centavos"}<=cols:
            for rid,labor,parts,total in connection.execute(
                "SELECT id,mano_obra_centavos,repuestos_centavos,importe_centavos FROM presupuestos"):
                if labor is not None and parts is not None and total is not None and labor+parts!=total:
                    findings.append({"severity":"media","kind":"budget_total_mismatch","message":f"Presupuesto {rid}: mano de obra + repuestos != total; {labor}+{parts}!={total}"})
            for rid,col,val in connection.execute(
                "SELECT id,'mano_obra_centavos',mano_obra_centavos FROM presupuestos WHERE mano_obra_centavos<0 UNION ALL SELECT id,'repuestos_centavos',repuestos_centavos FROM presupuestos WHERE repuestos_centavos<0 UNION ALL SELECT id,'importe_centavos',importe_centavos FROM presupuestos WHERE importe_centavos<0"):
                findings.append({"severity":"media","kind":"negative_budget_amount","message":f"Presupuesto {rid}: valor negativo en {col} ({val})"})
    if "movimientos" in tables:
        cols={r[1] for r in connection.execute("PRAGMA table_info(movimientos)")}
        if {"id","importe_centavos","comision_centavos","importe_neto_centavos"}<=cols:
            for rid,amount,fee,net in connection.execute("SELECT id,importe_centavos,comision_centavos,importe_neto_centavos FROM movimientos"):
                if amount is not None and fee is not None and net is not None and amount-fee!=net:
                    findings.append({"severity":"media","kind":"movement_net_mismatch","message":f"Movimiento {rid}: importe - comisión != neto ({amount}-{fee}!={net})"})
                if any(v is not None and v<0 for v in (amount,fee,net)):
                    findings.append({"severity":"media","kind":"negative_movement_amount","message":f"Movimiento {rid}: importe, comisión o neto negativo"})
    if "pagos_cuenta" in tables:
        cols={r[1] for r in connection.execute("PRAGMA table_info(pagos_cuenta)")}
        if {"id","importe_centavos"}<=cols:
            for rid,amount in connection.execute("SELECT id,importe_centavos FROM pagos_cuenta WHERE importe_centavos<0"):
                findings.append({"severity":"media","kind":"negative_payment","message":f"Pago {rid}: importe negativo ({amount})"})
    return findings

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("database",type=Path)
    args=ap.parse_args()
    if not args.database.is_file(): ap.error(f"No existe el archivo: {args.database}")
    db=sqlite3.connect(f"file:{args.database.resolve()}?mode=ro",uri=True)
    try: findings=audit_financial(db)
    finally: db.close()
    high=sum(f["severity"]=="alta" for f in findings); medium=sum(f["severity"]=="media" for f in findings)
    print(f"AUDITORÍA FINANCIERA | alertas={len(findings)} | alta={high} | media={medium}")
    for f in findings: print(f"[{f['severity'].upper()}] {f['kind']}: {f['message']}")
    if not findings: print("Sin alertas en las verificaciones realizadas.")
    return 1 if findings else 0
if __name__=="__main__": raise SystemExit(main())
