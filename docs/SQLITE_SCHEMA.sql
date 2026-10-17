-- Servicios Mecánicos Enzo
-- Esquema SQLite inicial propuesto (v1).
-- Este archivo define el diseño; no altera la app publicada por sí mismo.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at_utc TEXT NOT NULL,
  description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- Cada tabla conserva payload_json íntegro para no perder campos heredados.
-- Las columnas explícitas sirven para búsqueda, relaciones y cálculos.
CREATE TABLE IF NOT EXISTS clientes (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL DEFAULT '',
  documento TEXT,
  telefono TEXT,
  email TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS vehiculos (
  id TEXT PRIMARY KEY,
  cliente_id TEXT,
  patente TEXT,
  marca TEXT,
  modelo TEXT,
  anio TEXT,
  kilometros TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS trabajos (
  id TEXT PRIMARY KEY,
  numero TEXT,
  cliente_id TEXT,
  vehiculo_id TEXT,
  estado TEXT,
  fecha TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS presupuestos (
  id TEXT PRIMARY KEY,
  numero TEXT,
  trabajo_id TEXT,
  cliente_id TEXT,
  vehiculo_id TEXT,
  estado TEXT,
  fecha TEXT,
  mano_obra_centavos INTEGER,
  repuestos_centavos INTEGER,
  importe_centavos INTEGER,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS movimientos (
  id TEXT PRIMARY KEY,
  fecha TEXT,
  hora TEXT,
  tipo TEXT,
  concepto TEXT,
  cliente_id TEXT,
  trabajo_id TEXT,
  cuenta_id TEXT,
  pago_id TEXT,
  importe_centavos INTEGER,
  comision_centavos INTEGER,
  importe_neto_centavos INTEGER,
  medio_pago TEXT,
  acreditacion TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS eventos (
  id TEXT PRIMARY KEY,
  fecha TEXT,
  hora TEXT,
  cliente_id TEXT,
  vehiculo_id TEXT,
  trabajo_id TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS recepciones (
  id TEXT PRIMARY KEY,
  fecha TEXT,
  hora TEXT,
  cliente_id TEXT,
  vehiculo_id TEXT,
  trabajo_id TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS diagnosticos (
  id TEXT PRIMARY KEY,
  fecha TEXT,
  cliente_id TEXT,
  vehiculo_id TEXT,
  trabajo_id TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS cuentas (
  id TEXT PRIMARY KEY,
  tipo TEXT,
  tercero TEXT,
  concepto TEXT,
  cliente_id TEXT,
  trabajo_id TEXT,
  importe_centavos INTEGER,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS asistencias (
 id TEXT PRIMARY KEY, user_id TEXT, fecha TEXT, entrada TEXT, salida TEXT,
 payload_json TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, updated_at_utc TEXT
);
CREATE TABLE IF NOT EXISTS terceros (
 id TEXT PRIMARY KEY, nombre TEXT NOT NULL DEFAULT '', oficio TEXT, telefono TEXT, cuit TEXT,
 payload_json TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, updated_at_utc TEXT
);
CREATE TABLE IF NOT EXISTS trabajos_externos (
 id TEXT PRIMARY KEY, tercero_id TEXT, fecha TEXT, entrada TEXT, salida TEXT, total_centavos INTEGER, estado_pago TEXT,
 payload_json TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, updated_at_utc TEXT
);
CREATE TABLE IF NOT EXISTS config_horarios (
 id TEXT PRIMARY KEY, user_id TEXT, entrada TEXT, salida TEXT,
 payload_json TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, updated_at_utc TEXT
);
CREATE INDEX IF NOT EXISTS idx_asistencias_usuario_fecha ON asistencias(user_id, fecha);
CREATE INDEX IF NOT EXISTS idx_trabajos_externos_fecha ON trabajos_externos(fecha);

-- Los pagos embebidos en cuentas.pagos se extraen aquí, conservando además
-- el objeto original completo en cuentas.payload_json durante la transición.
CREATE TABLE IF NOT EXISTS pagos_cuenta (
  id TEXT PRIMARY KEY,
  cuenta_id TEXT NOT NULL,
  fecha TEXT,
  hora TEXT,
  importe_centavos INTEGER,
  medio_pago TEXT,
  acreditacion TEXT,
  movimiento_id TEXT,
  payload_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at_utc TEXT
);

-- Imágenes y firmas como BLOB, no como largas cadenas base64 en JSON.
-- La copia original dentro de payload_json se conserva hasta verificar hashes.
CREATE TABLE IF NOT EXISTS adjuntos (
  id TEXT PRIMARY KEY,
  entidad_tipo TEXT NOT NULL,
  entidad_id TEXT NOT NULL,
  campo TEXT NOT NULL,
  nombre_archivo TEXT,
  mime_type TEXT NOT NULL,
  datos BLOB NOT NULL,
  sha256_hex TEXT NOT NULL,
  metadata_json TEXT,
  created_at_utc TEXT
);

-- Registro de cambios para paquetes de intercambio incrementales futuros.
-- DELETE se representa con una marca lógica/cambio, no borrando el historial.
CREATE TABLE IF NOT EXISTS cambios_sync (
  change_id TEXT PRIMARY KEY,
  entidad_tipo TEXT NOT NULL,
  entidad_id TEXT NOT NULL,
  operacion TEXT NOT NULL,
  revision_base INTEGER,
  revision INTEGER NOT NULL,
  dispositivo_id TEXT NOT NULL,
  fecha_utc TEXT NOT NULL,
  payload_json TEXT,
  estado TEXT NOT NULL DEFAULT 'pendiente'
);

-- Hace que volver a importar el mismo paquete sea idempotente.
CREATE TABLE IF NOT EXISTS cambios_recibidos (
  change_id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL,
  dispositivo_origen TEXT NOT NULL,
  aplicado_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paquetes_intercambio (
  package_id TEXT PRIMARY KEY,
  dispositivo_origen TEXT NOT NULL,
  creado_at_utc TEXT NOT NULL,
  version_esquema INTEGER NOT NULL,
  tipo TEXT NOT NULL,
  sha256_hex TEXT,
  estado TEXT NOT NULL DEFAULT 'preparado'
);

CREATE TABLE IF NOT EXISTS conflictos_sync (
  conflict_id TEXT PRIMARY KEY,
  entidad_tipo TEXT NOT NULL,
  entidad_id TEXT NOT NULL,
  change_id_entrante TEXT NOT NULL,
  motivo TEXT NOT NULL,
  registro_local_json TEXT,
  registro_entrante_json TEXT,
  detectado_at_utc TEXT NOT NULL,
  resuelto_at_utc TEXT,
  resolucion TEXT
);

CREATE INDEX IF NOT EXISTS idx_vehiculos_cliente ON vehiculos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_vehiculos_patente ON vehiculos(patente);
CREATE INDEX IF NOT EXISTS idx_trabajos_cliente ON trabajos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_trabajos_vehiculo ON trabajos(vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_trabajos_fecha_estado ON trabajos(fecha, estado);
CREATE INDEX IF NOT EXISTS idx_presupuestos_trabajo ON presupuestos(trabajo_id);
CREATE INDEX IF NOT EXISTS idx_presupuestos_cliente ON presupuestos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos(fecha);
CREATE INDEX IF NOT EXISTS idx_movimientos_tipo_fecha ON movimientos(tipo, fecha);
CREATE INDEX IF NOT EXISTS idx_movimientos_cuenta ON movimientos(cuenta_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_pago ON movimientos(pago_id);
CREATE INDEX IF NOT EXISTS idx_eventos_fecha_hora ON eventos(fecha, hora);
CREATE INDEX IF NOT EXISTS idx_recepciones_fecha ON recepciones(fecha);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_cliente_fecha ON diagnosticos(cliente_id, fecha);
CREATE INDEX IF NOT EXISTS idx_cuentas_cliente ON cuentas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pagos_cuenta_cuenta_fecha ON pagos_cuenta(cuenta_id, fecha);
CREATE INDEX IF NOT EXISTS idx_adjuntos_entidad ON adjuntos(entidad_tipo, entidad_id);
CREATE INDEX IF NOT EXISTS idx_cambios_sync_estado ON cambios_sync(estado, fecha_utc);
CREATE INDEX IF NOT EXISTS idx_conflictos_sync_pendientes ON conflictos_sync(resuelto_at_utc);

INSERT OR IGNORE INTO app_metadata(key, value) VALUES
  ('app_name', 'Servicios Mecánicos Enzo'),
  ('currency', 'ARS'),
  ('migration_status', 'schema-only-not-yet-migrated');
INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('schema_version', '2');

INSERT OR IGNORE INTO schema_migrations(version, applied_at_utc, description)
VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), 'Estructura SQLite inicial para la aplicación del taller');
INSERT OR IGNORE INTO schema_migrations(version, applied_at_utc, description)
VALUES (2, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), 'Control horario, configuración de jornada y terceros externos');

PRAGMA user_version = 2;
