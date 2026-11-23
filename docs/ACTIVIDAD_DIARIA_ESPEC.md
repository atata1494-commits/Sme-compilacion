# SME — Criterio del resumen diario de actividad

## Objetivo
El resumen diario es una herramienta de gestión para el administrador principal, no un registro de navegación ni un sistema de vigilancia. La bitácora técnica puede conservar eventos; la pantalla de resumen muestra solo movimientos significativos y pendientes que requieren atención.

## Tres niveles
1. **Registro interno:** conserva eventos relevantes con fecha/hora, usuario, módulo, acción, contexto y, cuando corresponda, estado anterior/nuevo.
2. **Resumen diario:** agrupa movimientos importantes del día, sin repetir acciones de interfaz ni ruido.
3. **Pendiente de atención:** destaca únicamente eventos que necesitan decisión, aprobación, revisión o confirmación.

## Mostrar en el resumen
- Presupuesto creado; aprobación, rechazo o cambio sustancial de estado.
- Orden de trabajo creada y cambios relevantes de estado, asignación o alcance.
- Tarea asignada, urgente, vencida o que requiera confirmación.
- Caja: ingreso/egreso importante o cambio que deba revisarse.
- Solicitud de gasto y autorización/rechazo.
- Pedido o reposición de repuestos, especialmente si necesita autorización.
- Cambios en usuarios, permisos o configuración de seguridad.
- Incidencias de respaldo/sincronización que requieren intervención.

## No mostrar como movimiento
- Navegación entre pantallas, clics o pantallas abiertas.
- Consultas, búsquedas y visualizaciones.
- Guardados genéricos sin identificar qué dato cambió.
- Confirmaciones rutinarias de lectura, salvo que una tarea o aviso siga pendiente.
- Eventos duplicados o ruido de interfaz.

## Reglas de prioridad
- **Atención requerida:** pendiente de decisión, aprobación, confirmación, vencido, error o conflicto.
- **Importante:** movimiento relevante que el administrador debe conocer, sin requerir acción inmediata.
- **Informativo:** conservar en historial; no incluir por defecto en el resumen diario.

## Presentación
- Encabezado con fecha.
- Contadores breves por categoría.
- Lista de movimientos con persona, acción y objeto (por ejemplo, “María creó presupuesto para Ford Ranger”).
- Bloque separado “Pendiente de tu atención”.
- Cada elemento abre su detalle y su historial.
- Filtros de fecha/usuario/módulo; no mostrar controles innecesarios.
- Sin notificaciones repetitivas. El resumen debe poder revisarse al cierre del día o al entrar.

## Integridad y privacidad
- El registro no debe afirmar que un cambio se completó si el guardado falló.
- No registrar navegación ni datos sensibles innecesarios.
- Solo el administrador principal accede a esta pantalla.
- No eliminar historial al resolver una pendiente; cambiar su estado y mantener trazabilidad.

## Estado técnico verificado (rama de pruebas)
- Existe una pantalla “Actividad diaria”, filtro de búsqueda/usuario/acción/fecha y widget de inicio.
- La función `smeBusinessActivity` guarda eventos de negocio separados, con usuario, hora, categoría, prioridad, estado, contexto y opcionalmente estado anterior/nuevo.
- El resumen diario filtra los eventos de negocio del día; no se incluye el guardado genérico ni navegación/clics.
- Se verificaron instrumentaciones de tareas, control horario, gastos y autorizaciones, terceros/trabajos externos, caja, pedidos de repuestos/reposición, registros principales y presupuestos.
- El presupuesto emite el evento únicamente después de guardar correctamente; si falla, revierte el estado anterior.
- Los eventos pendientes se muestran en “Requiere atención” y se mantienen en el historial al resolverse (marcados como resueltos).
- La instrumentación está respaldada por pruebas de regresión en `tests/test_business_activity_summary.py`. Estas pruebas son de inspección de código; aún falta confirmar su ejecución en CI tras el commit de esta actualización.

## Próximo paso
- Validar el resumen en una APK instalada, especialmente que el detalle de evento sea claro y que los pendientes no se dupliquen ni se resuelvan por movimientos ajenos.
