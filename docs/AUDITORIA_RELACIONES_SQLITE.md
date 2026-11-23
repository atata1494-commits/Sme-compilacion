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
- Movimientos → trabajos, clientes, cuentas y pagos de cuenta
- Eventos, recepciones y diagnósticos → trabajos, clientes y vehículos
- Cuentas → trabajos y clientes
- Pagos de cuenta → cuentas y movimientos
- Pedidos de repuestos → clientes, vehículos y trabajos
- Trabajos externos → terceros

Las relaciones polimórficas de adjuntos y los vínculos de sincronización no se auditan aún. Referencias nulas o vacías se consideran opcionales y no se reportan.

## Resultado
- Sin hallazgos: mensaje de auditoría limpia, código de salida 0.
- Con hallazgos: tabla/ID de origen, columna, destino e ID faltante; código de salida 1.

**No repara automáticamente.** Revisar cada hallazgo antes de cualquier corrección.


## Auditoría de calidad de datos (segunda herramienta)

Ejecutar:
```bash
python scripts/audit_sqlite_data_quality.py /ruta/a/sme_tallerSQLite.db
```

Esta herramienta de solo lectura marca duplicados normalizados en documentos de clientes, patentes, números de trabajo y presupuestos, y campos vacíos de nombre de cliente, patente o estado de trabajo. Son alertas para revisión manual, no errores definitivos ni correcciones automáticas.
