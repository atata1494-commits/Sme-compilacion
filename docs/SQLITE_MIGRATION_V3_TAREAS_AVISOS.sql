-- SME SQLite migration v3: tareas, avisos, autorizaciones y auditoría.
-- Se aplica DESPUÉS del esquema base v2 (horarios y terceros).
-- Se aplica DESPUÉS de SQLITE_SCHEMA.sql (v1). No modifica tablas históricas.
-- Los identificadores de usuario son TEXT sin FK porque las cuentas aún viven
-- en el almacenamiento de la app y todavía no existe una tabla de usuarios SQLite.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sme_tareas (
  id TEXT PRIMARY KEY,
  titulo TEXT NOT NULL,
  descripcion TEXT NOT NULL DEFAULT '',
  categoria TEXT NOT NULL DEFAULT 'general',
  creada_por_usuario_id TEXT NOT NULL,
  responsable_usuario_id TEXT,
  equipo_id TEXT,
  estado TEXT NOT NULL DEFAULT 'pendiente_aceptacion'
    CHECK (estado IN ('borrador','pendiente_aceptacion','aceptada','en_curso','bloqueada','pendiente_revision','completada','cancelada','rechazada')),
  prioridad TEXT NOT NULL DEFAULT 'normal'
    CHECK (prioridad IN ('baja','normal','alta','urgente')),
  prioridad_motivo TEXT,
  prioridad_actualizada_por TEXT,
  prioridad_actualizada_at_utc TEXT,
  fecha_inicio_prevista TEXT,
  fecha_limite TEXT,
  fecha_inicio_real_utc TEXT,
  fecha_cierre_utc TEXT,
  requiere_revision INTEGER NOT NULL DEFAULT 0 CHECK (requiere_revision IN (0,1)),
  revisada_por_usuario_id TEXT,
  resultado_revision TEXT,
  referencia_tipo TEXT,
  referencia_id TEXT,
  revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  deleted_at_utc TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS sme_tarea_eventos (
  id TEXT PRIMARY KEY,
  tarea_id TEXT NOT NULL REFERENCES sme_tareas(id),
  usuario_id TEXT NOT NULL,
  accion TEXT NOT NULL,
  estado_anterior TEXT,
  estado_nuevo TEXT,
  motivo TEXT,
  datos_json TEXT,
  created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sme_tarea_dependencias (
  tarea_id TEXT NOT NULL REFERENCES sme_tareas(id),
  depende_de_tarea_id TEXT NOT NULL REFERENCES sme_tareas(id),
  created_at_utc TEXT NOT NULL,
  PRIMARY KEY (tarea_id, depende_de_tarea_id),
  CHECK (tarea_id <> depende_de_tarea_id)
);

CREATE TABLE IF NOT EXISTS sme_avisos (
  id TEXT PRIMARY KEY,
  titulo TEXT NOT NULL,
  detalle TEXT NOT NULL DEFAULT '',
  categoria TEXT NOT NULL CHECK (categoria IN ('faltante','rotura','mantenimiento','seguridad','demora','pedido_de_ayuda','otro')),
  creado_por_usuario_id TEXT NOT NULL,
  sector_origen TEXT,
  requiere_gasto TEXT NOT NULL DEFAULT 'por_determinar'
    CHECK (requiere_gasto IN ('si','no','por_determinar')),
  impacto_operativo TEXT NOT NULL DEFAULT 'normal'
    CHECK (impacto_operativo IN ('bajo','normal','alto','critico')),
  riesgo_seguridad TEXT NOT NULL DEFAULT 'sin_evaluar'
    CHECK (riesgo_seguridad IN ('sin_evaluar','bajo','medio','alto','critico')),
  prioridad TEXT NOT NULL DEFAULT 'normal'
    CHECK (prioridad IN ('baja','normal','alta','urgente')),
  estado TEXT NOT NULL DEFAULT 'abierto'
    CHECK (estado IN ('abierto','asignado','en_gestion','esperando_autorizacion','esperando_repuesto','resuelto','no_resuelto','cerrado')),
  responsable_actual_usuario_id TEXT,
  referencia_tipo TEXT,
  referencia_id TEXT,
  resolucion_propuesta TEXT,
  resolucion_real TEXT,
  resultado TEXT,
  created_at_utc TEXT NOT NULL,
  resolved_at_utc TEXT,
  closed_at_utc TEXT,
  revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
  updated_at_utc TEXT NOT NULL,
  deleted_at_utc TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS sme_aviso_derivaciones (
  id TEXT PRIMARY KEY,
  aviso_id TEXT NOT NULL REFERENCES sme_avisos(id),
  origen_usuario_id TEXT NOT NULL,
  destino_usuario_id TEXT,
  destino_equipo_id TEXT,
  motivo_derivacion TEXT NOT NULL,
  accion_solicitada TEXT,
  plazo_utc TEXT,
  estado TEXT NOT NULL DEFAULT 'enviado'
    CHECK (estado IN ('enviado','recibido','aceptado','devuelto','completado')),
  comentario_respuesta TEXT,
  created_at_utc TEXT NOT NULL,
  received_at_utc TEXT,
  responded_at_utc TEXT,
  CHECK (destino_usuario_id IS NOT NULL OR destino_equipo_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS sme_solicitudes_gasto (
  id TEXT PRIMARY KEY,
  aviso_id TEXT REFERENCES sme_avisos(id),
  tarea_id TEXT REFERENCES sme_tareas(id),
  solicitante_usuario_id TEXT NOT NULL,
  concepto TEXT NOT NULL,
  proveedor TEXT,
  importe_estimado_centavos INTEGER CHECK (importe_estimado_centavos IS NULL OR importe_estimado_centavos >= 0),
  importe_final_centavos INTEGER CHECK (importe_final_centavos IS NULL OR importe_final_centavos >= 0),
  moneda TEXT NOT NULL DEFAULT 'ARS' CHECK (moneda = 'ARS'),
  estado TEXT NOT NULL DEFAULT 'pendiente'
    CHECK (estado IN ('pendiente','aprobada','rechazada','ejecutada','rendida','anulada')),
  autorizador_usuario_id TEXT,
  autorizacion_at_utc TEXT,
  limite_autorizado_centavos INTEGER CHECK (limite_autorizado_centavos IS NULL OR limite_autorizado_centavos >= 0),
  condiciones_autorizacion TEXT,
  ejecutor_usuario_id TEXT,
  ejecutada_at_utc TEXT,
  comprobante_ref TEXT,
  verificador_usuario_id TEXT,
  verificada_at_utc TEXT,
  motivo_decision TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  CHECK (aviso_id IS NOT NULL OR tarea_id IS NOT NULL),
  CHECK (estado NOT IN ('aprobada','ejecutada','rendida') OR (autorizador_usuario_id IS NOT NULL AND autorizacion_at_utc IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS sme_permisos_usuario (
  id TEXT PRIMARY KEY,
  usuario_id TEXT NOT NULL,
  permiso TEXT NOT NULL,
  alcance TEXT NOT NULL DEFAULT 'propio'
    CHECK (alcance IN ('propio','sector','todos')),
  sector_id TEXT,
  permitido INTEGER NOT NULL DEFAULT 1 CHECK (permitido IN (0,1)),
  otorgado_por_usuario_id TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  UNIQUE (usuario_id, permiso, alcance, sector_id)
);

CREATE TABLE IF NOT EXISTS sme_auditoria (
  id TEXT PRIMARY KEY,
  entidad_tipo TEXT NOT NULL,
  entidad_id TEXT NOT NULL,
  accion TEXT NOT NULL,
  usuario_id TEXT NOT NULL,
  dispositivo_id TEXT,
  estado_anterior TEXT,
  estado_nuevo TEXT,
  motivo TEXT,
  datos_json TEXT,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sme_tareas_responsable_estado
  ON sme_tareas(responsable_usuario_id, estado, prioridad);
CREATE INDEX IF NOT EXISTS idx_sme_tareas_fecha_limite
  ON sme_tareas(estado, fecha_limite);
CREATE INDEX IF NOT EXISTS idx_sme_tarea_eventos_tarea_fecha
  ON sme_tarea_eventos(tarea_id, created_at_utc);
CREATE INDEX IF NOT EXISTS idx_sme_avisos_responsable_estado
  ON sme_avisos(responsable_actual_usuario_id, estado, prioridad);
CREATE INDEX IF NOT EXISTS idx_sme_avisos_categoria_fecha
  ON sme_avisos(categoria, created_at_utc);
CREATE INDEX IF NOT EXISTS idx_sme_derivaciones_aviso_fecha
  ON sme_aviso_derivaciones(aviso_id, created_at_utc);
CREATE INDEX IF NOT EXISTS idx_sme_gastos_estado_fecha
  ON sme_solicitudes_gasto(estado, created_at_utc);
CREATE INDEX IF NOT EXISTS idx_sme_permisos_usuario_permiso
  ON sme_permisos_usuario(usuario_id, permiso, permitido);
CREATE INDEX IF NOT EXISTS idx_sme_auditoria_entidad_fecha
  ON sme_auditoria(entidad_tipo, entidad_id, created_at_utc);

-- El historial es de solo agregado desde la app: no se permiten UPDATE/DELETE.
CREATE TRIGGER IF NOT EXISTS trg_sme_auditoria_no_update
BEFORE UPDATE ON sme_auditoria
BEGIN
  SELECT RAISE(ABORT, 'El historial de auditoria no se puede modificar');
END;

CREATE TRIGGER IF NOT EXISTS trg_sme_auditoria_no_delete
BEFORE DELETE ON sme_auditoria
BEGIN
  SELECT RAISE(ABORT, 'El historial de auditoria no se puede eliminar');
END;

INSERT OR IGNORE INTO schema_migrations(version, applied_at_utc, description)
VALUES (3, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), 'Tareas, avisos, permisos por acción, autorizaciones de gasto y auditoría');

UPDATE app_metadata SET value = '3' WHERE key = 'schema_version';
INSERT OR IGNORE INTO app_metadata(key, value) VALUES ('schema_version', '3');
UPDATE app_metadata SET value = 'sqlite-active-v3' WHERE key = 'migration_status';
PRAGMA user_version = 3;
