# Migración segura a SQLite — Servicios Mecánicos Enzo

## Estado del trabajo

**Integración inicial en rama de prueba.** La app de esta rama incluye un adaptador SQLite para Android y mantiene `localStorage` en la versión web. La aplicación publicada en `main` sigue intacta; no se han cambiado los datos del celular ni se ha publicado esta versión experimental. Todavía no se considera lista para uso diario.

Rama de trabajo: `sqlite-migration-work`.  
La rama `main` y la publicación de Netlify deben permanecer intactas hasta completar pruebas y una revisión explícita.

## Objetivo

Conservar los nueve módulos actuales — clientes, vehículos, trabajos, presupuestos, movimientos, eventos/agenda, recepciones, diagnósticos y cuentas corrientes — y migrarlos a una base SQLite local en la APK Android. Las fotografías y firmas también deben conservarse.

La primera versión de la APK no depende de una cuenta en la nube para operar. Windows y la sincronización automática quedan para etapas posteriores.

## Fuentes actuales

La app guarda un objeto bajo la clave `sme_taller_v1` en `localStorage`. El objeto contiene nueve listas. El archivo generado por Exportar respaldo, `respaldo-servicios-enzo.json`, contiene esas listas. La función Importar respaldo actual reemplaza los datos actuales; **no debe usarse como mecanismo de sincronización**.

Se han probado manualmente en el teléfono la exportación de un respaldo, la consulta de dos saldos existentes, navegación sin conexión y persistencia de un cliente de prueba tras actualizar y reabrir. Estas pruebas no certifican todos los módulos ni sustituyen pruebas automatizadas de migración.

## Diseño de SQLite

El archivo `SQLITE_SCHEMA.sql` define las tablas iniciales. Cada entidad tiene columnas explícitas para los datos de uso frecuente y conserva un `payload_json` completo para no descartar campos actuales que todavía no estén mapeados.

- IDs de SQLite son texto. Los IDs numéricos heredados se convierten a su representación textual en la clave interna; el JSON original se mantiene durante la fase de migración para no alterar valores sin necesidad.
- Los nuevos registros deben recibir un ID estable global (UUID) y no depender solamente de `Date.now()`.
- Las relaciones entre clientes, vehículos, trabajos, presupuestos, movimientos y cuentas se validan antes de activar restricciones estrictas. Los datos heredados no deben ser descartados si aparece una referencia rota.
- Los importes indexables se guardan como enteros de centavos, no como números de punto flotante. La conversión se realiza con el analizador monetario del proyecto y se valida contra el valor mostrado. El importe original permanece en `payload_json` hasta superar la verificación.
- Los pagos embebidos en `cuentas.pagos` se extraen a `pagos_cuenta` con una identidad propia; su información original se mantiene durante la transición.
- La tabla `adjuntos` está preparada para guardar fotografías y firmas como BLOB y verificarlas por SHA-256. **La integración inicial todavía conserva estos datos base64 dentro de `payload_json`; no extrae aún los archivos a BLOB.** Esa etapa queda pendiente y deberá comprobar apertura/impresión antes de eliminar cualquier copia original.
- Los movimientos de caja y los pagos son datos financieros: no se silencian ni se recalculan destructivamente. Las correcciones futuras deben quedar trazadas mediante reversión o asiento correctivo.

## Secuencia de migración

### Fase A — Inventario y copia de seguridad
1. Confirmar que el usuario conserva el JSON de respaldo en Descargas.
2. No borrar el almacenamiento local ni desinstalar la PWA.
3. Usar una copia del JSON como entrada de pruebas; nunca el único archivo de respaldo.
4. Definir un inventario por lista: cantidad de registros, IDs vacíos/duplicados, referencias sin destino, fotos y firmas presentes.

### Fase B — Ensayo de migración
1. Leer y validar el JSON completo sin modificar la base original.
2. Crear una base SQLite temporal en una transacción.
3. Insertar todos los registros de los nueve módulos y preservar el JSON completo de cada registro.
4. Normalizar y copiar fotografías/firmas a `adjuntos`; calcular y comprobar hashes.
5. Extraer pagos de cuentas corrientes de manera idempotente y validar su relación con movimientos de caja.
6. Convertir importes a centavos usando un parser probado; no asumir que una cadena con coma/punto tiene formato conocido.
7. Ejecutar validaciones. Si cualquiera falla, cancelar la transacción y conservar el JSON sin cambios.

### Fase C — Validación antes de activar
La migración solo se acepta si se cumplen todos estos controles:

- Cantidad de registros por cada una de las nueve listas igual a la entrada, salvo que un duplicado o registro inválido sea detectado y presentado para resolver sin descartarlo.
- Ningún ID obligatorio vacío y ningún ID duplicado dentro de la misma entidad sin resolver.
- Referencias cliente/vehículo/trabajo/cuenta comprobadas; toda referencia no resuelta queda reportada y no se elimina silenciosamente.
- Mismo total de pagos y movimientos financieros antes y después, tanto por registro como por suma en centavos.
- Los saldos de prueba conocidos se mantienen: Pablo $6.900 pendiente y Jona $35.250 pendiente en el conjunto de prueba actual.
- Mismo número de fotos y firmas, SHA-256 coincidente y apertura comprobada.
- Se pueden volver a ejecutar las validaciones sin duplicar registros.
- Exportación de un respaldo desde SQLite y comparación con el estado migrado sin pérdida de campos.
- Cierre/reapertura de la APK y operación sin internet comprobados en un dispositivo real.

### Fase D — Activación segura
1. La migración se realiza sobre un archivo SQLite temporal.
2. Mostrar un informe claro: registros leídos, migrados, adjuntos verificados, advertencias y errores.
3. Activar la nueva base solo al tocar Confirmar cuando todos los controles bloqueantes estén aprobados.
4. Mantener la opción de conservar el JSON original. No borrar automáticamente datos o respaldos antiguos.
5. Si la instalación o la validación falla, la app vuelve a mostrar la opción de reintentar/importar; no presenta una migración fallida como exitosa.

## Respaldo completo versus intercambio

Son funciones separadas:

- **Respaldo completo:** fotografía de todos los datos y archivos de ese dispositivo; restaurar reemplaza el conjunto de destino tras una confirmación explícita.
- **Paquete de intercambio:** contiene únicamente cambios desde una versión/paquete anterior, IDs estables, versión del esquema, dispositivo origen, checksum e identificadores de cambio. Importar es aditivo, idempotente y nunca elimina registros no incluidos.
- Un cambio repetido se ignora mediante `cambios_recibidos`.
- Si el mismo registro cambió en los dos dispositivos desde revisiones distintas, se crea un conflicto visible; no gana automáticamente el último archivo ni la última hora.
- Eliminaciones futuras requieren marcas lógicas/tombstones dentro del registro de cambios para evitar que un dispositivo vuelva a crear un registro borrado.

## Pruebas obligatorias

Usar fixtures sintéticos, no publicar datos personales reales del taller.

1. Base vacía: crea el esquema y no falla.
2. JSON válido con los nueve módulos: migra y mantiene el conteo.
3. JSON corrupto o tipo inesperado: error comprensible, sin modificar el archivo original.
4. IDs vacíos o duplicados: informe explícito, no pérdida silenciosa.
5. Relaciones faltantes: informe explícito.
6. Importes argentinos con miles, decimales y valores vacíos: conversión exacta o bloqueo visible.
7. Fotos y firmas: bytes/hash y visualización correctos.
8. Pagos de cuentas corrientes: mismo saldo y mismo total de caja, sin cobro duplicado.
9. Reejecución del mismo paquete incremental: no duplica movimientos.
10. Conflictos simultáneos: informa y deja resolver.
11. Reinicio, modo avión, cierre inesperado y espacio insuficiente: los datos ya confirmados sobreviven.
12. Regresión manual de todos los módulos: alta/consulta/edición, documentos, impresión/PDF y backup.

## Qué falta implementar

- Completar y probar la migración real del JSON de respaldo hacia SQLite temporal con un informe de validación antes de activar.
- Extraer fotografías y firmas desde base64 a `adjuntos` como BLOB, comprobar SHA-256 y validar impresión/PDF.
- Probar la integración nativa de SQLite en una APK real; la configuración y el workflow de compilación están preparados, pero la APK todavía no se ha validado en un teléfono.
- Añadir pruebas automatizadas de lectura/escritura, pagos, reversión ante errores y persistencia tras reiniciar.
- Añadir paquetes incrementales y resolución de conflictos después de estabilizar SQLite local.
- Verificar instalación/actualización Android sin perder la base SQLite.

## Implementación técnica inicial en `sqlite-migration-work`

- `src/storage/sqlite-store.js` inicializa SQLite nativo en Capacitor y conserva `localStorage` para la web.
- Los guardados nativos usan transacciones y comparan registros por ID para escribir solo los cambios detectados. Si una lista contiene IDs faltantes o duplicados, el guardado se bloquea en lugar de descartar esos registros.
- Los IDs nuevos se generan con UUID cuando el entorno lo admite. Los IDs heredados se conservan dentro del JSON de cada registro.
- `netlify.toml` configura la salida compilada de Vite; la publicación deberá probarse antes de fusionar la rama.
- `.github/workflows/build-android-apk.yml` prepara una APK de depuración como artefacto temporal, sujeto a que la compilación automática finalice correctamente.

Estos archivos son una primera integración, no una certificación de integridad. La rama no debe fusionarse hasta que las pruebas de esquema, compilación, restauración y regresión sean satisfactorias.

## Regla de publicación

No fusionar esta rama con `main`, cambiar Netlify, ni reemplazar la versión usada diariamente hasta que la migración y la APK pasen los controles críticos con un respaldo recuperable.
