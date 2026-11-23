#!/usr/bin/env python3
"""Auditoría de relaciones SQLite SME. Solo lectura; nunca corrige ni elimina datos."""
from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path

RELATIONS = (
    ("vehiculos", "cliente_id", "clientes", "id"),
    ("trabajos", "cliente_id", "clientes", "id"),
    ("trabajos", "vehiculo_id", "vehiculos", "id"),
    ("presupuestos", "trabajo_id", "trabajos", "id"),
    ("presupuestos", "cliente_id", "clientes", "id"),
    ("presupuestos", "vehiculo_id", "vehiculos", "id"),
    ("movimientos", "trabajo_id", "trabajos", "id"),
    ("movimientos", "cliente_id", "clientes", "id"),
    ("movimientos", "cuenta_id", "cuentas", "id"),
    ("movimientos", "pago_id", "pagos_cuenta", "id"),
    ("eventos", "trabajo_id", "trabajos", "id"),
    ("eventos", "cliente_id", "clientes", "id"),
    ("eventos", "vehiculo_id", "vehiculos", "id"),
    ("recepciones", "trabajo_id", "trabajos", "id"),
    ("recepciones", "cliente_id", "clientes", "id"),
    ("recepciones", "vehiculo_id", "vehiculos", "id"),
    ("diagnosticos", "trabajo_id", "trabajos", "id"),
    ("diagnosticos", "cliente_id", "clientes", "id"),
    ("diagnosticos", "vehiculo_id", "vehiculos", "id"),
    ("cuentas", "trabajo_id", "trabajos", "id"),
    ("cuentas", "cliente_id", "clientes", "id"),
    ("pagos_cuenta", "cuenta_id", "cuentas", "id"),
    ("pagos_cuenta", "movimiento_id", "movimientos", "id"),
    ("trabajos_externos", "tercero_id", "terceros", "id"),
)

def audit_connection(connection: sqlite3.Connection) -> list[dict]:
    """Return orphan-link findings, ignoring NULL/empty optional references."""
    tables = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    findings = []
    for source_table, source_col, target_table, target_col in RELATIONS:
        if source_table not in tables or target_table not in tables:
            continue
        source_cols = {row[1] for row in connection.execute(
            f"PRAGMA table_info({source_table})")}
        target_cols = {row[1] for row in connection.execute(
            f"PRAGMA table_info({target_table})")}
        if source_col not in source_cols or target_col not in target_cols:
            continue
        query = f"""SELECT s.id, s.{source_col} FROM {source_table} s
        LEFT JOIN {target_table} t ON t.{target_col}=s.{source_col}
        WHERE s.{source_col} IS NOT NULL AND TRIM(CAST(s.{source_col} AS TEXT))<>''
        AND t.{target_col} IS NULL"""
        for record_id, ref_id in connection.execute(query):
            findings.append({"source_table":source_table,"source_id":record_id,
                            "column":source_col,"missing_target_table":target_table,
                            "missing_target_id":ref_id})
    return findings

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="Archivo SQLite de SME")
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error(f"No existe el archivo: {args.database}")
    connection = sqlite3.connect(f"file:{args.database.resolve()}?mode=ro", uri=True)
    try:
        findings = audit_connection(connection)
    finally:
        connection.close()
    if not findings:
        print("Auditoría finalizada: no se detectaron referencias huérfanas en las relaciones revisadas.")
        return 0
    print(f"Se detectaron {len(findings)} referencias huérfanas (no se modificó nada):")
    for item in findings:
        print(f"- {item['source_table']} id={item['source_id']}: {item['column']}={item['missing_target_id']} (falta en {item['missing_target_table']})")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
