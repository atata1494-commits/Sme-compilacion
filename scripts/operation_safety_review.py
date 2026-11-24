#!/usr/bin/env python3
"""Genera un checklist de seguridad previo a operaciones sensibles; no ejecuta cambios."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone

OPERATIONS={
 "import":{"risk":"HIGH","checks":["Identificar origen y formato del archivo","Revisar vista previa y registros que se crearán o actualizarán","Confirmar detección de duplicados","Verificar que exista un respaldo reciente y validado"]},
 "overwrite":{"risk":"CRITICAL","checks":["Confirmar exactamente qué archivo/base será reemplazado","Comparar hashes y conservar copia de la versión actual","Validar el archivo entrante antes de reemplazar","Requerir aprobación explícita del administrador"]},
 "delete":{"risk":"HIGH","checks":["Confirmar registro y relaciones vinculadas","Revisar impacto en presupuestos, trabajos, movimientos y clientes","Preferir baja lógica si el sistema la soporta","Requerir respaldo reciente y aprobación explícita"]},
 "restore":{"risk":"CRITICAL","checks":["Validar respaldo (estructura, integridad y hash)","Revisar inventario y vista previa de recuperación","Comparar con la base activa y documentar diferencias","Confirmar destino, conservar base actual y exigir aprobación explícita"]},
}
def build_review(operation, backup_validated=False, preview_done=False, admin_approved=False):
 spec=OPERATIONS[operation]
 checks=[{"item":c,"status":"pending"} for c in spec["checks"]]
 flags={"backup_validated":backup_validated,"preview_done":preview_done,"admin_approved":admin_approved}
 if backup_validated:
  for x in checks:
   if "respaldo" in x["item"].lower() or "conservar copia" in x["item"].lower(): x["status"]="confirmed"
 if preview_done:
  for x in checks:
   if "vista previa" in x["item"].lower() or "inventario" in x["item"].lower(): x["status"]="confirmed"
 if admin_approved:
  for x in checks:
   if "aprobación explícita" in x["item"].lower() or "aprobación" in x["item"].lower(): x["status"]="confirmed"
 return {"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
  "operation":operation,"risk":spec["risk"],"flags":flags,"checks":checks,
  "decision":"REVIEW_ONLY","notice":"Checklist preventivo. No ejecuta ni autoriza importación, eliminación, sobrescritura o restauración."}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("operation",choices=sorted(OPERATIONS))
 p.add_argument("--backup-validated",action="store_true")
 p.add_argument("--preview-done",action="store_true")
 p.add_argument("--admin-approved",action="store_true")
 p.add_argument("--report")
 a=p.parse_args()
 report=build_review(a.operation,a.backup_validated,a.preview_done,a.admin_approved)
 output=json.dumps(report,ensure_ascii=False,indent=2)
 print(output)
 if a.report:
  from pathlib import Path
  Path(a.report).write_text(output+"\n",encoding="utf-8")
 return 0
if __name__=="__main__": raise SystemExit(main())
