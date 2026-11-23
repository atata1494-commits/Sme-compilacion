# Auditoría de relaciones SQLite SME

Herramienta auxiliar de diagnóstico **solo lectura** para identificar referencias huérfanas en tablas SQLite.

## Uso

Desde la raíz del repositorio:

```bash
python scripts/audit_sqlite_relationships.py /ruta/a/sme_tallerSQLite.db
```

La herramienta abre la base en modo SQLite `ro` (read-only). No realiza UPDATE, INSERT ni DELETE.

## Relaciones revisadas
- Vehículos → clientes
- Trabajos → clientes y vehículos
- Presupuestos → trabajos, clientes y vehículos
- Movimientos → trabajos, clientes y cuentas
- Eventos, recepciones y diagnósticos → trabajos, clientes y vehículos
- Cuentas → trabajos y clientes
- Trabajos externos → terceros

Referencias nulas o vacías se consideran opcionales y no se reportan.

## Resultado
- Sin hallazgos: mensaje de auditoría limpia, código de salida 0.
- Con hallazgos: tabla/ID de origen, columna, destino e ID faltante; código de salida 1.

**No repara automáticamente.** Revisar cada hallazgo antes de cualquier corrección.
