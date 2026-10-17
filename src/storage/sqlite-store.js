import { Capacitor } from '@capacitor/core';
import { CapacitorSQLite, SQLiteConnection } from '@capacitor-community/sqlite';
import schemaSQL from '../../docs/SQLITE_SCHEMA.sql?raw';
import migrationV3SQL from '../../docs/SQLITE_MIGRATION_V3_TAREAS_AVISOS.sql?raw';

const DATABASE_NAME = 'sme_taller';
const COLLECTIONS = [
  'clientes', 'vehiculos', 'trabajos', 'presupuestos', 'movimientos',
  'eventos', 'recepciones', 'diagnosticos', 'cuentas', 'asistencias', 'terceros', 'trabajosExternos', 'configHorarios',
  'tareas', 'avisos', 'solicitudesGasto'
];

const TABLES = {
  clientes: {
    table: 'clientes',
    fields: r => ({ nombre: r.nombre ?? '', documento: r.documento ?? null, telefono: r.telefono ?? null, email: r.email ?? null })
  },
  vehiculos: {
    table: 'vehiculos',
    fields: r => ({ cliente_id: ref(r.clienteId), patente: r.patente ?? null, marca: r.marca ?? null, modelo: r.modelo ?? null, anio: r.anio == null ? null : String(r.anio), kilometros: r.kilometros == null ? null : String(r.kilometros) })
  },
  trabajos: {
    table: 'trabajos',
    fields: r => ({ numero: r.numero ?? null, cliente_id: ref(r.clienteId), vehiculo_id: ref(r.vehiculoId), estado: r.estado ?? null, fecha: r.fecha ?? null })
  },
  presupuestos: {
    table: 'presupuestos',
    fields: r => ({ numero: r.numero ?? null, trabajo_id: ref(r.trabajoId), cliente_id: ref(r.clienteId), vehiculo_id: ref(r.vehiculoId), estado: r.estado ?? null, fecha: r.fecha ?? null, mano_obra_centavos: cents(r.manoObra), repuestos_centavos: cents(r.repuestos), importe_centavos: cents(r.importe) })
  },
  movimientos: {
    table: 'movimientos',
    fields: r => ({ fecha: r.fecha ?? null, hora: r.hora ?? null, tipo: r.tipo ?? null, concepto: r.concepto ?? null, cliente_id: ref(r.clienteId), trabajo_id: ref(r.trabajoId), cuenta_id: ref(r.cuentaId), pago_id: ref(r.pagoId), importe_centavos: cents(r.importe), comision_centavos: cents(r.comision), importe_neto_centavos: cents(r.importeNeto), medio_pago: r.medioPago ?? null, acreditacion: r.acreditacion ?? null })
  },
  eventos: {
    table: 'eventos',
    fields: r => ({ fecha: r.fecha ?? null, hora: r.hora ?? null, cliente_id: ref(r.clienteId), vehiculo_id: ref(r.vehiculoId), trabajo_id: ref(r.trabajoId) })
  },
  recepciones: {
    table: 'recepciones',
    fields: r => ({ fecha: r.fecha ?? null, hora: r.hora ?? null, cliente_id: ref(r.clienteId), vehiculo_id: ref(r.vehiculoId), trabajo_id: ref(r.trabajoId) })
  },
  diagnosticos: {
    table: 'diagnosticos',
    fields: r => ({ fecha: r.fecha ?? null, cliente_id: ref(r.clienteId), vehiculo_id: ref(r.vehiculoId), trabajo_id: ref(r.trabajoId) })
  },
  cuentas: {
    table: 'cuentas',
    fields: r => ({ tipo: r.tipo ?? null, tercero: r.tercero ?? null, concepto: r.concepto ?? null, cliente_id: ref(r.clienteId), trabajo_id: ref(r.trabajoId), importe_centavos: cents(r.importe) })
  },
  asistencias: { table: 'asistencias', fields: r => ({ user_id: ref(r.userId), fecha: r.fecha ?? null, entrada: r.entrada ?? null, salida: r.salida ?? null }) },
  terceros: { table: 'terceros', fields: r => ({ nombre: r.nombre ?? '', oficio: r.oficio ?? null, telefono: r.telefono ?? null, cuit: r.cuit ?? null }) },
  trabajosExternos: { table: 'trabajos_externos', fields: r => ({ tercero_id: ref(r.terceroId), fecha: r.fecha ?? null, entrada: r.entrada ?? null, salida: r.salida ?? null, total_centavos: cents(r.total), estado_pago: r.estadoPago ?? null }) },
  configHorarios: { table: 'config_horarios', fields: r => ({ user_id: ref(r.userId), entrada: r.entrada ?? null, salida: r.salida ?? null }) },
  tareas: {
    table: 'sme_tareas',
    fields: r => ({
      titulo: r.titulo ?? 'Tarea sin título', descripcion: r.descripcion ?? '', categoria: r.categoria ?? 'general',
      creada_por_usuario_id: ref(r.creadaPorUsuarioId) ?? 'sme-legacy', responsable_usuario_id: ref(r.responsableUsuarioId),
      equipo_id: ref(r.equipoId), estado: r.estado ?? 'pendiente_aceptacion', prioridad: r.prioridad ?? 'normal',
      prioridad_motivo: r.prioridadMotivo ?? null, prioridad_actualizada_por: ref(r.prioridadActualizadaPor),
      prioridad_actualizada_at_utc: r.prioridadActualizadaAt ?? null, fecha_inicio_prevista: r.fechaInicioPrevista ?? null,
      fecha_limite: r.fechaLimite ?? null, fecha_inicio_real_utc: r.fechaInicioReal ?? null, fecha_cierre_utc: r.fechaCierre ?? null,
      requiere_revision: r.requiereRevision ? 1 : 0, revisada_por_usuario_id: ref(r.revisadaPor),
      resultado_revision: r.resultadoRevision ?? null, referencia_tipo: r.referenciaTipo ?? null, referencia_id: ref(r.referenciaId),
      created_at_utc: r.createdAt ?? new Date().toISOString(), deleted_at_utc: r.deletedAt ?? null
    })
  },
  avisos: {
    table: 'sme_avisos',
    fields: r => ({
      titulo: r.titulo ?? 'Aviso sin título', detalle: r.detalle ?? '', categoria: r.categoria ?? 'otro',
      creado_por_usuario_id: ref(r.creadoPorUsuarioId) ?? 'sme-legacy', sector_origen: r.sectorOrigen ?? null,
      requiere_gasto: r.requiereGasto ?? 'por_determinar', impacto_operativo: r.impactoOperativo ?? 'normal',
      riesgo_seguridad: r.riesgoSeguridad ?? 'sin_evaluar', prioridad: r.prioridad ?? 'normal', estado: r.estado ?? 'abierto',
      responsable_actual_usuario_id: ref(r.responsableActualUsuarioId), referencia_tipo: r.referenciaTipo ?? null,
      referencia_id: ref(r.referenciaId), resolucion_propuesta: r.resolucionPropuesta ?? null,
      resolucion_real: r.resolucionReal ?? null, resultado: r.resultado ?? null, created_at_utc: r.createdAt ?? new Date().toISOString(),
      resolved_at_utc: r.resolvedAt ?? null, closed_at_utc: r.closedAt ?? null, deleted_at_utc: r.deletedAt ?? null
    })
  },
  solicitudesGasto: {
    table: 'sme_solicitudes_gasto',
    fields: r => ({
      aviso_id: ref(r.avisoId), tarea_id: ref(r.tareaId),
      solicitante_usuario_id: ref(r.solicitanteUsuarioId) ?? 'sme-legacy', concepto: r.concepto ?? 'Gasto sin concepto',
      proveedor: r.proveedor ?? null, importe_estimado_centavos: cents(r.importeEstimado),
      importe_final_centavos: cents(r.importeFinal), moneda: 'ARS', estado: r.estado ?? 'pendiente',
      autorizador_usuario_id: ref(r.autorizadorUsuarioId), autorizacion_at_utc: r.autorizacionAt ?? null,
      limite_autorizado_centavos: cents(r.limiteAutorizado), condiciones_autorizacion: r.condicionesAutorizacion ?? null,
      ejecutor_usuario_id: ref(r.ejecutorUsuarioId), ejecutada_at_utc: r.ejecutadaAt ?? null,
      comprobante_ref: r.comprobanteRef ?? null, verificador_usuario_id: ref(r.verificadorUsuarioId),
      verificada_at_utc: r.verificadaAt ?? null, motivo_decision: r.motivoDecision ?? null,
      created_at_utc: r.createdAt ?? new Date().toISOString()
    })
  }
};

function ref(value) {
  return value === undefined || value === null || String(value).trim() === '' ? null : String(value);
}

function cents(value) {
  if (value === undefined || value === null || value === '') return null;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return null;
    return Math.round(value * 100);
  }
  const raw = String(value).trim();
  if (!raw) return null;
  let normalized;
  if (/^-?\d+(\.\d+)?$/.test(raw)) normalized = raw;
  else normalized = raw.replace(/\./g, '').replace(',', '.');
  const number = Number(normalized);
  if (!Number.isFinite(number)) throw new Error('Importe inválido: ' + raw);
  return Math.round(number * 100);
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalizeSnapshot(value, emptyDB) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('La base de datos no tiene un formato válido.');
  const result = { ...emptyDB() };
  for (const key of COLLECTIONS) {
    if (value[key] !== undefined && !Array.isArray(value[key])) {
      throw new Error('La lista ' + key + ' del respaldo no es válida.');
    }
    result[key] = Array.isArray(value[key]) ? value[key] : [];
  }
  return result;
}

function validateSnapshot(snapshot) {
  for (const key of COLLECTIONS) {
    const seen = new Set();
    for (let index = 0; index < snapshot[key].length; index += 1) {
      const record = snapshot[key][index];
      if (!record || typeof record !== 'object' || Array.isArray(record)) {
        throw new Error('Hay un registro inválido en ' + key + ' (posición ' + (index + 1) + ').');
      }
      if (record.id === undefined || record.id === null || String(record.id).trim() === '') {
        throw new Error('Hay un registro sin identificador en ' + key + ' (posición ' + (index + 1) + '). No se modificó la base.');
      }
      const id = String(record.id);
      if (seen.has(id)) {
        throw new Error('Hay un identificador duplicado en ' + key + ': ' + id + '. No se modificó la base.');
      }
      seen.add(id);
      JSON.stringify(record);
    }
  }
}

function sqlError(result, action) {
  if (result?.changes?.changes === -1 && result?.message) {
    throw new Error(action + ': ' + result.message);
  }
}

function cloneEmpty(emptyDB) {
  return normalizeSnapshot(emptyDB(), emptyDB);
}

export async function openSMEStorage(storageKey) {
  const isNative = Capacitor.isNativePlatform();

  if (!isNative) {
    return {
      isNative: false,
      async load(emptyDB) {
        try {
          const raw = localStorage.getItem(storageKey);
          if (!raw) return emptyDB();
          return normalizeSnapshot(JSON.parse(raw), emptyDB);
        } catch (error) {
          console.error('No se pudo leer el almacenamiento web:', error);
          throw new Error('No se pudieron leer los datos guardados en este navegador.');
        }
      },
      async save(snapshot) {
        localStorage.setItem(storageKey, JSON.stringify(snapshot));
      }
    };
  }

  const sqlite = new SQLiteConnection(CapacitorSQLite);
  let connection;
  const consistency = await sqlite.checkConnectionsConsistency();
  const existing = await sqlite.isConnection(DATABASE_NAME, false);

  if (consistency.result && existing.result) {
    connection = await sqlite.retrieveConnection(DATABASE_NAME, false);
  } else {
    if (existing.result) {
      try { await sqlite.closeConnection(DATABASE_NAME, false); } catch (_) {}
    }
    connection = await sqlite.createConnection(DATABASE_NAME, false, 'no-encryption', 1, false);
  }

  const opened = await connection.isDBOpen();
  if (!opened.result) await connection.open();
  const schemaResult = await connection.execute(schemaSQL);
  sqlError(schemaResult, 'No se pudo crear la estructura SQLite');
  const migrationResult = await connection.execute(migrationV3SQL);
  sqlError(migrationResult, 'No se pudo actualizar la estructura SQLite a la versión 3');

  // Compatibilidad defensiva: las tablas nuevas de tareas/avisos/gastos también
  // participan del lector y escritor genérico, que requiere una columna revision.
  // En instalaciones que ya tenían v3, CREATE TABLE IF NOT EXISTS no agrega
  // columnas ausentes; comprobarlas evita bloquear el inicio y conserva payload_json.
  for (const key of COLLECTIONS) {
    const table = TABLES[key].table;
    const info = await connection.query('PRAGMA table_info(' + table + ')');
    const columns = new Set((info.values || []).map(column => String(column.name)));
    if (!columns.has('revision')) {
      const altered = await connection.execute(
        'ALTER TABLE ' + table + ' ADD COLUMN revision INTEGER NOT NULL DEFAULT 1'
      );
      sqlError(altered, 'No se pudo completar la columna revision de ' + table);
    }
  }

  let lastSnapshot = cloneEmpty(() => Object.fromEntries(COLLECTIONS.map(k => [k, []])));
  let revisions = Object.fromEntries(COLLECTIONS.map(k => [k, new Map()]));
  let saveQueue = Promise.resolve();

  async function readSnapshot(emptyDB) {
    const out = emptyDB();
    const nextRevisions = Object.fromEntries(COLLECTIONS.map(k => [k, new Map()]));
    for (const key of COLLECTIONS) {
      const table = TABLES[key].table;
      const result = await connection.query('SELECT id, payload_json, revision FROM ' + table + ' ORDER BY rowid');
      out[key] = (result.values || []).map(row => {
        nextRevisions[key].set(String(row.id), Number(row.revision) || 1);
        return JSON.parse(row.payload_json);
      });
    }
    lastSnapshot = clone(out);
    revisions = nextRevisions;
    return out;
  }

  async function run(statement, values = []) {
    const result = await connection.run(statement, values, false);
    sqlError(result, 'No se pudo guardar la información');
    return result;
  }

  async function upsertRecord(key, record) {
    const config = TABLES[key];
    const explicit = config.fields(record);
    const id = String(record.id);
    const revision = (revisions[key].get(id) || 0) + 1;
    const fields = { id, ...explicit, payload_json: JSON.stringify(record), revision, updated_at_utc: new Date().toISOString() };
    const columns = Object.keys(fields);
    const values = columns.map(name => fields[name]);
    const placeholders = columns.map(() => '?').join(', ');
    const updates = columns.filter(name => name !== 'id').map(name => name + '=excluded.' + name).join(', ');
    await run('INSERT INTO ' + config.table + ' (' + columns.join(', ') + ') VALUES (' + placeholders + ') ON CONFLICT(id) DO UPDATE SET ' + updates, values);
    revisions[key].set(id, revision);
  }

  function historyItems(record) {
    return Array.isArray(record?.historial) ? record.historial : [];
  }

  async function persistAppendOnlyEvents(key, record, previous) {
    const entityTypes = { tareas: 'tarea', avisos: 'aviso', solicitudesGasto: 'gasto' };
    const entityType = entityTypes[key];
    if (!entityType) return;
    const existingEvents = new Set(historyItems(previous).map(item => String(item.id)));
    for (const event of historyItems(record)) {
      const eventId = ref(event?.id);
      if (!eventId || existingEvents.has(eventId)) continue;
      const actor = ref(event.usuarioId) || 'sme-legacy';
      const at = event.fecha || new Date().toISOString();
      const action = String(event.accion || event.tipo || 'actualizacion');
      const before = event.estadoAnterior ?? null;
      const after = event.estadoNuevo ?? record.estado ?? null;
      const reason = event.motivo ?? event.detalle ?? null;
      await run(
        'INSERT OR IGNORE INTO sme_auditoria (id, entidad_tipo, entidad_id, accion, usuario_id, estado_anterior, estado_nuevo, motivo, datos_json, created_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [eventId, entityType, String(record.id), action, actor, before, after, reason, JSON.stringify(event), at]
      );
      if (key === 'tareas') {
        await run(
          'INSERT OR IGNORE INTO sme_tarea_eventos (id, tarea_id, usuario_id, accion, estado_anterior, estado_nuevo, motivo, datos_json, created_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
          [eventId, String(record.id), actor, action, before, after, reason, JSON.stringify(event), at]
        );
      }
    }
    if (key === 'avisos') {
      const oldIds = new Set((Array.isArray(previous?.derivaciones) ? previous.derivaciones : []).map(item => String(item.id)));
      for (const step of (Array.isArray(record.derivaciones) ? record.derivaciones : [])) {
        const stepId = ref(step?.id);
        if (!stepId || oldIds.has(stepId)) continue;
        await run(
          'INSERT OR IGNORE INTO sme_aviso_derivaciones (id, aviso_id, origen_usuario_id, destino_usuario_id, destino_equipo_id, motivo_derivacion, accion_solicitada, plazo_utc, estado, comentario_respuesta, created_at_utc, received_at_utc, responded_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
          [stepId, String(record.id), ref(step.origenUsuarioId) || 'sme-legacy', ref(step.destinoUsuarioId), ref(step.destinoEquipoId), String(step.motivo || 'Derivación'), step.accionSolicitada ?? null, step.plazo ?? null, step.estado || 'enviado', step.comentarioRespuesta ?? null, step.fecha || new Date().toISOString(), step.recibidoAt ?? null, step.respondidoAt ?? null]
        );
      }
    }
  }

  async function rebuildPayments(snapshot) {
    await run('DELETE FROM pagos_cuenta');
    for (const account of snapshot.cuentas) {
      const payments = Array.isArray(account.pagos) ? account.pagos : [];
      for (let index = 0; index < payments.length; index += 1) {
        const payment = payments[index];
        const paymentKey = payment.id === undefined || payment.id === null ? 'legacy-' + index : String(payment.id);
        const id = String(account.id) + '::' + paymentKey + '::' + index;
        const movement = payment.id === undefined || payment.id === null ? null : snapshot.movimientos.find(item => String(item.cuentaId ?? '') === String(account.id) && String(item.pagoId ?? '') === String(payment.id));
        const fields = [
          id, String(account.id), payment.fecha ?? null, payment.hora ?? null,
          cents(payment.importe), payment.medioPago ?? null, payment.acreditacion ?? null,
          movement ? String(movement.id) : null, JSON.stringify(payment), 1, new Date().toISOString()
        ];
        await run(
          'INSERT INTO pagos_cuenta (id, cuenta_id, fecha, hora, importe_centavos, medio_pago, acreditacion, movimiento_id, payload_json, revision, updated_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
          fields
        );
      }
    }
  }

  async function persistSnapshot(snapshot) {
    validateSnapshot(snapshot);
    const changes = new Set();

    await connection.beginTransaction();
    try {
      for (const key of COLLECTIONS) {
        const before = new Map((lastSnapshot[key] || []).map(record => [String(record.id), JSON.stringify(record)]));
        const after = new Map(snapshot[key].map(record => [String(record.id), JSON.stringify(record)]));
        const table = TABLES[key].table;

        for (const id of before.keys()) {
          if (!after.has(id)) {
            await run('DELETE FROM ' + table + ' WHERE id = ?', [id]);
            revisions[key].delete(id);
            changes.add(key);
          }
        }

        for (const record of snapshot[key]) {
          const id = String(record.id);
          if (before.get(id) !== after.get(id)) {
            await upsertRecord(key, record);
            const previous = (lastSnapshot[key] || []).find(item => String(item.id) === id);
            await persistAppendOnlyEvents(key, record, previous);
            changes.add(key);
          }
        }
      }
      if (changes.has('cuentas')) await rebuildPayments(snapshot);
      if (changes.size > 0) {
        await run("INSERT OR REPLACE INTO app_metadata(key,value) VALUES ('migration_status','sqlite-active')");
      }
      await connection.commitTransaction();
      lastSnapshot = clone(snapshot);
    } catch (error) {
      try { await connection.rollbackTransaction(); } catch (_) {}
      // Restore revision bookkeeping because SQLite rolled the transaction back.
      try {
        for (const key of COLLECTIONS) {
          const rows = await connection.query('SELECT id, revision FROM ' + TABLES[key].table);
          revisions[key] = new Map((rows.values || []).map(row => [String(row.id), Number(row.revision) || 1]));
        }
      } catch (_) {}
      throw error;
    }
  }

  return {
    isNative: true,
    async load(emptyDB) {
      const snapshot = await readSnapshot(emptyDB);
      const count = COLLECTIONS.reduce((sum, key) => sum + snapshot[key].length, 0);
      if (count === 0) {
        // Si una futura versión contiene datos heredados en localStorage de esta misma APK,
        // migrarlos una sola vez y mantener el origen como copia de seguridad.
        const marker = await connection.query("SELECT value FROM app_metadata WHERE key = 'legacy_localstorage_checked'");
        if (!marker.values?.length) {
          let legacy = null;
          try {
            const raw = localStorage.getItem(storageKey);
            if (raw) legacy = normalizeSnapshot(JSON.parse(raw), emptyDB);
          } catch (_) {}
          if (legacy && COLLECTIONS.some(key => legacy[key].length > 0)) {
            validateSnapshot(legacy);
            await persistSnapshot(legacy);
            await connection.run("INSERT OR REPLACE INTO app_metadata(key,value) VALUES ('legacy_localstorage_checked','migrated')");
            return clone(legacy);
          }
          await connection.run("INSERT OR REPLACE INTO app_metadata(key,value) VALUES ('legacy_localstorage_checked','checked-empty')");
        }
      }
      return snapshot;
    },
    async save(snapshot) {
      const captured = normalizeSnapshot(clone(snapshot), () => Object.fromEntries(COLLECTIONS.map(k => [k, []])));
      const operation = saveQueue.then(() => persistSnapshot(captured));
      saveQueue = operation.catch(() => {});
      return operation;
    },
    async close() {
      await saveQueue;
      await sqlite.closeConnection(DATABASE_NAME, false);
    }
  };
}
