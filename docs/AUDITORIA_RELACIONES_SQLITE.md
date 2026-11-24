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


## Clasificación de alertas de calidad

La auditoría complementaria ordena resultados por gravedad:
- **Alta:** documentos de clientes duplicados y patentes duplicadas (pueden afectar identidad/relaciones).
- **Media:** números de trabajo o presupuesto duplicados y campos vacíos revisados.

Cada alerta incluye una recomendación de revisión manual. La clasificación es orientativa: no significa que el dato esté definitivamente mal ni autoriza cambios automáticos. El reporte muestra primero el resumen de cantidades y luego las alertas ordenadas por gravedad.


## Auditoría financiera (tercera herramienta)

Ejecutar:
```bash
python scripts/audit_sqlite_financial.py /ruta/a/sme_tallerSQLite.db
```

En modo solo lectura revisa integridad SQLite, referencias declaradas, sumas de presupuestos (mano de obra + repuestos frente al total), neto de movimientos (importe menos comisión) y valores negativos. Son alertas aritméticas para revisión; no asume que todo caso especial sea un error y no modifica datos.


## Validación previa de respaldos (cuarta herramienta)

Uso:
```bash
python scripts/validate_sme_backup.py /ruta/al/respaldo.zip
```

Valida JSON, SQLite y ZIP en controles estructurales, CRC, rutas inseguras, JSON/SQLite embebidos y calcula SHA-256. No extrae ni restaura. Un resultado limpio solo confirma las comprobaciones realizadas, no que el backup esté completo o que una restauración real vaya a funcionar.


### Límites preventivos ZIP (actualización)
Antes de leer el contenido de un ZIP, el validador inspecciona sus metadatos y aplica límites: máximo 1000 entradas, 128 MiB por entrada y 256 MiB de tamaño total descomprimido. Si alguno se excede, detiene la inspección del ZIP sin inflarlo. También rechaza rutas de traversal y tipos de archivo especiales (como symlinks). Estos límites reducen riesgos de archivos comprimidos maliciosos o desproporcionados; no reemplazan una revisión del origen del respaldo.


## Vista previa de recuperación (quinta herramienta)

Ejecutar:
```bash
python scripts/preview_sme_recovery.py /ruta/al/respaldo.zip
```

Genera un inventario sin extracción: archivos incluidos, claves/estructura básica de JSON y, cuando Python lo permite, tablas SQLite con cantidad de registros y esquema. Para ZIP usa límites preventivos de entrada/total, rechaza rutas inseguras y tipos especiales, y verifica CRC antes de inspeccionar contenidos. Es una vista previa de diagnóstico; no escribe archivos, no restaura y no se conecta a la base activa. Aún no está integrada al flujo de restauración de Android.



## Expediente previo a recuperación

El script `scripts/recovery_review_gate.py` genera un expediente JSON con SHA-256 y tamaño de la base actual y del respaldo, validación del respaldo y vista previa. Ejemplo:
```bash
python scripts/recovery_review_gate.py base_actual.db respaldo.zip --report revision_previa.json
```

Los estados son `BLOCKED` cuando hay problemas detectados y `REQUIRES_MANUAL_REVIEW` cuando las comprobaciones automáticas no reportan alertas. **Ninguno de los estados autoriza ni ejecuta una restauración.** No reemplaza ni escribe en la base activa. Los tests añadidos aún requieren ejecución en CI o entorno local antes de considerarse aprobados.


## Comparación de inventario entre respaldos (sexta herramienta)

Ejecutar:
```bash
python scripts/compare_sme_backups.py respaldo_anterior.db respaldo_nuevo.db
```

Compara dos SQLite en modo solo lectura: integridad, tablas presentes/ausentes, cambios de esquema y cantidades de filas por tabla. Puede guardar el JSON con `--report informe.json`. No compara los datos fila por fila ni determina cuál copia es la correcta; cualquier diferencia requiere revisión manual. Nunca modifica ni restaura bases.

**Control adicional:** si alguna de las dos bases no supera `PRAGMA integrity_check`, el comparador ahora informa `BLOCKED` y devuelve código de salida 2; no debe considerarse apta para revisión normal hasta resolver el problema de integridad. El resultado `REQUIRES_MANUAL_REVIEW` sigue sin certificar que el respaldo esté completo.

**Alerta específica de tablas vacías:** el comparador ahora lista `tables_empty_in_new` cuando una tabla tenía registros en la copia anterior y aparece con cero registros en la nueva. Es una señal para investigar (no prueba pérdida: puede ser una limpieza legítima).


## Diagnóstico unificado (séptima herramienta)

Para ejecutar en una sola pasada las auditorías de relaciones, calidad de datos y finanzas:

```bash
python scripts/diagnose_sme.py /ruta/a/sme_tallerSQLite.db
```

Opcionalmente, validar también un respaldo:

```bash
python scripts/diagnose_sme.py /ruta/a/sme_tallerSQLite.db --backup /ruta/al/respaldo.zip --report diagnostico.json
```

Consolida resultados y resumen JSON. Es una herramienta de solo lectura; no repara, migra ni restaura. Si falta la base, falla una auditoría o la validación del respaldo informa alertas, el estado general queda `BLOCKED`. Las alertas encontradas se cuentan en el resumen y requieren revisión. Un diagnóstico sin alertas tampoco certifica integridad funcional completa.
