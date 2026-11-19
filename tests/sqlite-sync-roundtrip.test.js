import test from 'node:test';
import assert from 'node:assert/strict';
import { openSMEStorage } from '../src/storage/sqlite-store.js';
import { databasePaths, cleanupTestDatabases, reuseDatabasePath, executeSqlOnDatabase } from './helpers/capacitor-sqlite.mock.mjs';
import { normalizeVersionVector, incrementVersionVector, compareVersionVectors, mergeVersionVectors } from '../src/storage/sync-version-vector.js';

const emptyDB = () => ({
  clientes: [], vehiculos: [], trabajos: [], presupuestos: [], movimientos: [],
  eventos: [], recepciones: [], diagnosticos: [], cuentas: [], asistencias: [],
  terceros: [], trabajosExternos: [], configHorarios: [], tareas: [], avisos: [],
  solicitudesGasto: [], pedidosRepuestos: []
});

test('dos bases SQLite independientes intercambian cambios reales de SME en ambos sentidos', async () => {
  let deviceA;
  let deviceB;
  try {
    deviceA = await openSMEStorage('sme-test-a');
    deviceB = await openSMEStorage('sme-test-b');
    const snapshotA = await deviceA.load(emptyDB);
    const snapshotB = await deviceB.load(emptyDB);

    assert.deepEqual(snapshotA.clientes, []);
    assert.deepEqual(snapshotB.clientes, []);
    assert.equal(deviceA.isNative, true);
    assert.equal(deviceB.isNative, true);

    snapshotA.clientes.push({
      id: 'cliente-sync-001',
      nombre: 'Cliente de prueba',
      documento: '30111222',
      telefono: '2974000000'
    });
    await deviceA.save(snapshotA);

    const packageA = await deviceA.prepareSyncPackage();
    assert.equal(packageA.cambios.length, 1);
    const appliedOnB = await deviceB.applySyncPackage(packageA);
    assert.equal(appliedOnB.aplicado, true);
    assert.equal(appliedOnB.cambios_aplicados, 1);

    const receivedOnB = await deviceB.load(emptyDB);
    assert.equal(receivedOnB.clientes[0].nombre, 'Cliente de prueba');

    receivedOnB.clientes[0].telefono = '2974111222';
    await deviceB.save(receivedOnB);
    const packageB = await deviceB.prepareSyncPackage();
    assert.equal(packageB.cambios.length, 1);
    assert.equal(packageB.cambios[0].operacion, 'UPDATE');

    const appliedOnA = await deviceA.applySyncPackage(packageB);
    assert.equal(appliedOnA.aplicado, true);
    assert.equal(appliedOnA.cambios_aplicados, 1);

    const finalA = await deviceA.load(emptyDB);
    const finalB = await deviceB.load(emptyDB);
    assert.deepEqual(finalA.clientes, finalB.clientes);
    assert.equal(finalA.clientes[0].telefono, '2974111222');

    const repeated = await deviceA.applySyncPackage(packageB);
    assert.equal(repeated.repetido, true);
    assert.equal(databasePaths.length, 2);
    assert.notEqual(databasePaths[0], databasePaths[1]);
  } finally {
    if (deviceA) await deviceA.close();
    if (deviceB) await deviceB.close();
    cleanupTestDatabases();
  }
});


test('aplica varios cambios causales consecutivos de una misma entidad en un solo paquete', async () => {
  let deviceA;
  let deviceB;
  try {
    deviceA = await openSMEStorage('sme-sequence-a');
    deviceB = await openSMEStorage('sme-sequence-b');
    const snapshotA = await deviceA.load(emptyDB);
    await deviceB.load(emptyDB);

    snapshotA.clientes.push({ id: 'cliente-secuencia', nombre: 'Primera versión', telefono: '111' });
    await deviceA.save(snapshotA);
    snapshotA.clientes[0].telefono = '222';
    await deviceA.save(snapshotA);
    snapshotA.clientes[0].nombre = 'Versión final';
    await deviceA.save(snapshotA);

    const pkg = await deviceA.prepareSyncPackage();
    assert.equal(pkg.cambios.length, 3);
    const inspection = await deviceB.inspectSyncPackage(pkg);
    assert.equal(inspection.listo_para_aplicar, true);
    assert.equal(inspection.plan.nuevas, 1);
    assert.equal(inspection.plan.actualizables, 2);

    const result = await deviceB.applySyncPackage(pkg);
    assert.equal(result.aplicado, true);
    assert.equal(result.cambios_aplicados, 3);
    const finalB = await deviceB.load(emptyDB);
    assert.equal(finalB.clientes[0].nombre, 'Versión final');
    assert.equal(finalB.clientes[0].telefono, '222');
  } finally {
    if (deviceA) await deviceA.close();
    if (deviceB) await deviceB.close();
    cleanupTestDatabases();
  }
});

test('detecta y permite resolver una modificación concurrente del mismo registro', async () => {
  let deviceA;
  let deviceB;
  try {
    deviceA = await openSMEStorage('sme-conflict-a');
    deviceB = await openSMEStorage('sme-conflict-b');
    const snapshotA = await deviceA.load(emptyDB);
    await deviceB.load(emptyDB);

    snapshotA.clientes.push({ id: 'cliente-conflicto', nombre: 'Base compartida', telefono: '100' });
    await deviceA.save(snapshotA);
    const initialPackage = await deviceA.prepareSyncPackage();
    const initialResult = await deviceB.applySyncPackage(initialPackage);
    assert.equal(initialResult.aplicado, true);

    const localA = await deviceA.load(emptyDB);
    const localB = await deviceB.load(emptyDB);
    localA.clientes[0].telefono = '200';
    localB.clientes[0].telefono = '300';
    await deviceA.save(localA);
    await deviceB.save(localB);

    const packageA = await deviceA.prepareSyncPackage();
    const conflictResult = await deviceB.applySyncPackage(packageA);
    assert.equal(conflictResult.aplicado, false);
    assert.equal(conflictResult.requiere_revision, true);
    assert.equal(conflictResult.conflictos_guardados, 1);

    const conflicts = await deviceB.listSyncConflicts();
    assert.equal(conflicts.length, 1);
    assert.equal(conflicts[0].entidad_id, 'cliente-conflicto');

    const resolution = await deviceB.resolveSyncConflict({
      conflictId: conflicts[0].conflict_id,
      choice: 'incoming',
      resolvedByUserId: 'admin-test'
    });
    assert.equal(resolution.resuelto, true);

    const resolved = await deviceB.load(emptyDB);
    assert.equal(resolved.clientes[0].telefono, '200');
    const remaining = await deviceB.listSyncConflicts();
    assert.equal(remaining.length, 0);
  } finally {
    if (deviceA) await deviceA.close();
    if (deviceB) await deviceB.close();
    cleanupTestDatabases();
  }
});

test('propaga una eliminación y conserva la marca causal del registro borrado', async () => {
  let deviceA;
  let deviceB;
  try {
    deviceA = await openSMEStorage('sme-delete-a');
    deviceB = await openSMEStorage('sme-delete-b');
    const snapshotA = await deviceA.load(emptyDB);
    await deviceB.load(emptyDB);

    snapshotA.clientes.push({ id: 'cliente-eliminar', nombre: 'Para eliminar', telefono: '400' });
    await deviceA.save(snapshotA);
    const insertPackage = await deviceA.prepareSyncPackage();
    await deviceB.applySyncPackage(insertPackage);

    const beforeDelete = await deviceA.load(emptyDB);
    beforeDelete.clientes = [];
    await deviceA.save(beforeDelete);
    const deletePackage = await deviceA.prepareSyncPackage();
    assert.equal(deletePackage.cambios.at(-1).operacion, 'DELETE');

    const deletionResult = await deviceB.applySyncPackage(deletePackage);
    assert.equal(deletionResult.aplicado, true);
    assert.equal(deletionResult.cambios_aplicados, 1);
    const afterDelete = await deviceB.load(emptyDB);
    assert.deepEqual(afterDelete.clientes, []);

    const staleInsert = await deviceB.applySyncPackage(insertPackage);
    assert.equal(staleInsert.repetido, true);
    assert.deepEqual((await deviceB.load(emptyDB)).clientes, []);
  } finally {
    if (deviceA) await deviceA.close();
    if (deviceB) await deviceB.close();
    cleanupTestDatabases();
  }
});


test('conserva datos, identidad del dispositivo y cambios pendientes al cerrar y reabrir SQLite', async () => {
  let device;
  let reopened;
  try {
    device = await openSMEStorage('sme-reopen-persistence');
    const snapshot = await device.load(emptyDB);
    snapshot.clientes.push({
      id: 'cliente-persistencia',
      nombre: 'Persistencia real',
      telefono: '2974555000'
    });
    await device.save(snapshot);

    const beforeClose = await device.prepareSyncPackage();
    assert.equal(beforeClose.cambios.length, 1);
    const originalDeviceId = beforeClose.dispositivo_origen;
    const originalChangeId = beforeClose.cambios[0].change_id;
    const originalPath = databasePaths.at(-1);

    await device.close();
    device = null;
    reuseDatabasePath(originalPath);

    reopened = await openSMEStorage('sme-reopen-persistence');
    const restored = await reopened.load(emptyDB);
    assert.equal(restored.clientes.length, 1);
    assert.equal(restored.clientes[0].nombre, 'Persistencia real');

    const afterReopen = await reopened.prepareSyncPackage();
    assert.equal(afterReopen.dispositivo_origen, originalDeviceId);
    assert.equal(afterReopen.cambios.length, 1);
    assert.equal(afterReopen.cambios[0].change_id, originalChangeId);
    assert.equal(afterReopen.cambios[0].entidad_id, 'cliente-persistencia');
  } finally {
    if (device) await device.close();
    if (reopened) await reopened.close();
    cleanupTestDatabases();
  }
});


test('resuelve conflictos sucesivos de la misma entidad manteniendo la causalidad', async () => {
  let deviceA;
  let deviceB;
  try {
    deviceA = await openSMEStorage('sme-multi-conflict-a');
    deviceB = await openSMEStorage('sme-multi-conflict-b');
    const baseA = await deviceA.load(emptyDB);
    await deviceB.load(emptyDB);

    baseA.clientes.push({ id: 'cliente-multi-conflicto', nombre: 'Base', telefono: '100' });
    await deviceA.save(baseA);
    const basePackage = await deviceA.prepareSyncPackage();
    assert.equal((await deviceB.applySyncPackage(basePackage)).aplicado, true);

    const branchA = await deviceA.load(emptyDB);
    const branchB = await deviceB.load(emptyDB);
    branchA.clientes[0].telefono = '200';
    branchB.clientes[0].telefono = '300';
    await deviceA.save(branchA);
    await deviceB.save(branchB);

    const firstPackage = await deviceA.prepareSyncPackage();
    const firstConflict = await deviceB.applySyncPackage(firstPackage);
    assert.equal(firstConflict.requiere_revision, true);
    let conflicts = await deviceB.listSyncConflicts();
    assert.equal(conflicts.length, 1);

    const firstResolution = await deviceB.resolveSyncConflict({
      conflictId: conflicts[0].conflict_id,
      choice: 'incoming',
      resolvedByUserId: 'admin-test'
    });
    assert.equal(firstResolution.resuelto, true);
    assert.equal((await deviceB.load(emptyDB)).clientes[0].telefono, '200');

    const nextA = await deviceA.load(emptyDB);
    nextA.clientes[0].telefono = '250';
    await deviceA.save(nextA);
    const secondPackage = await deviceA.prepareSyncPackage();
    const secondConflict = await deviceB.applySyncPackage(secondPackage);
    assert.equal(secondConflict.requiere_revision, true);

    conflicts = await deviceB.listSyncConflicts();
    assert.equal(conflicts.length, 1);
    const secondResolution = await deviceB.resolveSyncConflict({
      conflictId: conflicts[0].conflict_id,
      choice: 'incoming',
      resolvedByUserId: 'admin-test'
    });
    assert.equal(secondResolution.resuelto, true);
    assert.equal((await deviceB.load(emptyDB)).clientes[0].telefono, '250');
    assert.equal((await deviceB.listSyncConflicts()).length, 0);
  } finally {
    if (deviceA) await deviceA.close();
    if (deviceB) await deviceB.close();
    cleanupTestDatabases();
  }
});


test('revierte todo el paquete SQLite si falla una escritura intermedia y permite reintentar', async () => {
  let deviceA;
  let deviceB;
  try {
    deviceA = await openSMEStorage('sme-rollback-a');
    deviceB = await openSMEStorage('sme-rollback-b');
    const source = await deviceA.load(emptyDB);
    await deviceB.load(emptyDB);

    source.clientes.push(
      { id: 'cliente-rollback-uno', nombre: 'Primer registro', telefono: '111' },
      { id: 'cliente-rollback-dos', nombre: 'Segundo registro', telefono: '222' }
    );
    await deviceA.save(source);
    const pkg = await deviceA.prepareSyncPackage();
    assert.equal(pkg.cambios.length, 2);

    const secondChangeId = pkg.cambios[1].entidad_id;
    const targetPath = databasePaths.at(-1);
    executeSqlOnDatabase(targetPath,
      "CREATE TRIGGER fail_second_client BEFORE INSERT ON clientes " +
      "WHEN NEW.id = '" + secondChangeId + "' " +
      "BEGIN SELECT RAISE(ABORT, 'fallo SQLite inducido por prueba'); END;"
    );

    await assert.rejects(() => deviceB.applySyncPackage(pkg), /fallo SQLite inducido por prueba/);
    assert.deepEqual((await deviceB.load(emptyDB)).clientes, []);

    const outgoingAfterFailure = await deviceB.prepareSyncPackage();
    assert.equal(outgoingAfterFailure.cambios.length, 0);

    executeSqlOnDatabase(targetPath, 'DROP TRIGGER fail_second_client;');

    // Simula que el receptor pierde la conexión tras el rollback y debe recuperarse.
    await deviceB.close();
    deviceB = null;
    reuseDatabasePath(targetPath);
    deviceB = await openSMEStorage('sme-rollback-b-reconnected');
    assert.deepEqual((await deviceB.load(emptyDB)).clientes, []);
    assert.equal((await deviceB.prepareSyncPackage()).cambios.length, 0);

    const retry = await deviceB.applySyncPackage(pkg);
    assert.equal(retry.aplicado, true);
    assert.equal(retry.cambios_aplicados, 2);
    const restored = await deviceB.load(emptyDB);
    assert.deepEqual(
      restored.clientes.map(record => record.id).sort(),
      ['cliente-rollback-dos', 'cliente-rollback-uno']
    );
  } finally {
    if (deviceA) await deviceA.close();
    if (deviceB) await deviceB.close();
    cleanupTestDatabases();
  }
});


test('guarda y sincroniza pedidos rápidos de repuestos como colección independiente', async () => {
  let deviceA;
  let deviceB;
  try {
    deviceA = await openSMEStorage('sme-parts-order-a');
    deviceB = await openSMEStorage('sme-parts-order-b');
    const source = await deviceA.load(emptyDB);
    await deviceB.load(emptyDB);
    source.pedidosRepuestos.push({
      id: 'pedido-repuestos-001',
      titulo: 'Pedido de repuestos · AB123CD',
      vehiculoId: 'vehiculo-001',
      destinatario: 'Dueño de prueba',
      items: ['Pantógrafo completo con bujes y rótula', 'Bieleta', 'Amortiguador'],
      observaciones: 'Delantero derecho',
      estado: 'pendiente',
      createdAt: '2026-11-18T12:00:00.000Z',
      updatedAt: '2026-11-18T12:00:00.000Z'
    });
    await deviceA.save(source);
    const pkg = await deviceA.prepareSyncPackage();
    assert.equal(pkg.cambios.length, 1);
    assert.equal(pkg.cambios[0].entidad_tipo, 'pedidosRepuestos');
    const result = await deviceB.applySyncPackage(pkg);
    assert.equal(result.aplicado, true);
    const received = await deviceB.load(emptyDB);
    assert.equal(received.pedidosRepuestos.length, 1);
    assert.deepEqual(received.pedidosRepuestos[0].items, source.pedidosRepuestos[0].items);
    assert.equal(received.pedidosRepuestos[0].destinatario, 'Dueño de prueba');
  } finally {
    if (deviceA) await deviceA.close();
    if (deviceB) await deviceB.close();
    cleanupTestDatabases();
  }
});


test('recupera un envío pendiente tras reiniciar el emisor y tolera reenvíos tras reiniciar el receptor', async () => {
  let sender;
  let receiver;
  try {
    sender = await openSMEStorage('sme-restart-sender');
    receiver = await openSMEStorage('sme-restart-receiver');
    const senderSnapshot = await sender.load(emptyDB);
    await receiver.load(emptyDB);

    senderSnapshot.clientes.push({
      id: 'cliente-reinicio-sync',
      nombre: 'Persistencia de sincronización',
      telefono: '2974000000'
    });
    await sender.save(senderSnapshot);
    const preparedBeforeRestart = await sender.prepareSyncPackage();
    assert.equal(preparedBeforeRestart.cambios.length, 1);
    const originalChangeId = preparedBeforeRestart.cambios[0].change_id;
    const senderPath = databasePaths.at(-2);
    const receiverPath = databasePaths.at(-1);

    await sender.close();
    sender = null;
    reuseDatabasePath(senderPath);
    sender = await openSMEStorage('sme-restart-sender');
    const preparedAfterRestart = await sender.prepareSyncPackage();
    assert.equal(preparedAfterRestart.cambios.length, 1);
    assert.equal(preparedAfterRestart.cambios[0].change_id, originalChangeId);

    const firstDelivery = await receiver.applySyncPackage(preparedAfterRestart);
    assert.equal(firstDelivery.aplicado, true);
    assert.equal(firstDelivery.cambios_aplicados, 1);
    assert.equal((await receiver.load(emptyDB)).clientes[0].nombre, 'Persistencia de sincronización');

    const duplicateDelivery = await receiver.applySyncPackage(preparedAfterRestart);
    assert.equal(duplicateDelivery.repetido, true);

    await receiver.close();
    receiver = null;
    reuseDatabasePath(receiverPath);
    receiver = await openSMEStorage('sme-restart-receiver');
    const afterReceiverRestart = await receiver.load(emptyDB);
    assert.equal(afterReceiverRestart.clientes.length, 1);
    assert.equal(afterReceiverRestart.clientes[0].id, 'cliente-reinicio-sync');

    const duplicateAfterRestart = await receiver.applySyncPackage(preparedAfterRestart);
    assert.equal(duplicateAfterRestart.repetido, true);
    assert.equal((await receiver.load(emptyDB)).clientes.length, 1);
    assert.equal((await receiver.prepareSyncPackage()).cambios.length, 0);
  } finally {
    if (sender) await sender.close();
    if (receiver) await receiver.close();
    cleanupTestDatabases();
  }
});


test('tolera la entrega tardía de un paquete parcialmente ya recibido sin duplicar ni revertir datos', async () => {
  let sender;
  let receiver;
  try {
    sender = await openSMEStorage('sme-out-of-order-sender');
    receiver = await openSMEStorage('sme-out-of-order-receiver');
    const source = await sender.load(emptyDB);
    await receiver.load(emptyDB);

    source.clientes.push({ id: 'cliente-orden-paquetes', nombre: 'Base', telefono: '100' });
    await sender.save(source);
    const initial = await sender.prepareSyncPackage();
    assert.equal((await receiver.applySyncPackage(initial)).aplicado, true);

    source.clientes[0].telefono = '200';
    await sender.save(source);
    const olderPackage = await sender.prepareSyncPackage();
    assert.equal(olderPackage.cambios.length, 2);

    source.clientes[0].telefono = '300';
    await sender.save(source);
    const newerPackage = await sender.prepareSyncPackage();
    assert.equal(newerPackage.cambios.length, 3);

    const newestDelivery = await receiver.applySyncPackage(newerPackage);
    assert.equal(newestDelivery.aplicado, true);
    assert.equal((await receiver.load(emptyDB)).clientes[0].telefono, '300');

    const delayedDelivery = await receiver.applySyncPackage(olderPackage);
    assert.equal(delayedDelivery.aplicado, true);
    assert.equal(delayedDelivery.cambios_aplicados, 0);
    assert.equal(delayedDelivery.cambios_omitidos, 2);
    assert.equal(delayedDelivery.plan.ya_recibidos, 2);
    assert.equal((await receiver.load(emptyDB)).clientes[0].telefono, '300');

    const duplicateDelayedDelivery = await receiver.applySyncPackage(olderPackage);
    assert.equal(duplicateDelayedDelivery.aplicado, true);
    assert.equal(duplicateDelayedDelivery.cambios_aplicados, 0);
    assert.equal(duplicateDelayedDelivery.cambios_omitidos, 2);
  } finally {
    if (sender) await sender.close();
    if (receiver) await receiver.close();
    cleanupTestDatabases();
  }
});


test('rechaza paquetes alterados o incompletos antes de modificar SQLite', async () => {
  let sender;
  let receiver;
  try {
    sender = await openSMEStorage('sme-integrity-sender');
    receiver = await openSMEStorage('sme-integrity-receiver');
    const source = await sender.load(emptyDB);
    await receiver.load(emptyDB);

    source.clientes.push({
      id: 'cliente-paquete-integridad',
      nombre: 'Contenido original',
      telefono: '2974000000'
    });
    await sender.save(source);
    const validPackage = await sender.prepareSyncPackage();
    assert.equal(validPackage.cambios.length, 1);

    const tamperedPackage = structuredClone(validPackage);
    tamperedPackage.cambios[0].payload.nombre = 'Contenido modificado';
    await assert.rejects(
      () => receiver.applySyncPackage(tamperedPackage),
      /La huella SHA-256 no coincide/
    );
    assert.deepEqual((await receiver.load(emptyDB)).clientes, []);
    assert.equal((await receiver.prepareSyncPackage()).cambios.length, 0);

    const incompletePackage = structuredClone(validPackage);
    delete incompletePackage.cambios[0].dispositivo_id;
    await assert.rejects(
      () => receiver.applySyncPackage(incompletePackage),
      /Falta dispositivo_id/
    );
    assert.deepEqual((await receiver.load(emptyDB)).clientes, []);
    assert.equal((await receiver.prepareSyncPackage()).cambios.length, 0);

    const invalidOperationPackage = structuredClone(validPackage);
    invalidOperationPackage.cambios[0].operacion = 'DROP';
    await assert.rejects(
      () => receiver.applySyncPackage(invalidOperationPackage),
      /Operación no permitida/
    );

    const mismatchedPayloadPackage = structuredClone(validPackage);
    mismatchedPayloadPackage.cambios[0].payload.id = 'otro-id';
    await assert.rejects(
      () => receiver.applySyncPackage(mismatchedPayloadPackage),
      /El contenido del cambio no coincide/
    );

    assert.deepEqual((await receiver.load(emptyDB)).clientes, []);
    assert.equal((await receiver.prepareSyncPackage()).cambios.length, 0);

    const intactDelivery = await receiver.applySyncPackage(validPackage);
    assert.equal(intactDelivery.aplicado, true);
    assert.equal((await receiver.load(emptyDB)).clientes[0].nombre, 'Contenido original');
  } finally {
    if (sender) await sender.close();
    if (receiver) await receiver.close();
    cleanupTestDatabases();
  }
});


test('valida vectores causales, normaliza orden y rechaza contadores o identificadores inválidos', () => {
  assert.deepEqual(normalizeVersionVector({ 'device-b': 2, 'device-a': 1, zero: 0 }), { 'device-a': 1, 'device-b': 2 });
  assert.deepEqual(incrementVersionVector({ 'device-a': 2 }, 'device-b'), { 'device-a': 2, 'device-b': 1 });
  assert.equal(compareVersionVectors({ a: 2 }, { a: 1 }), 'dominates');
  assert.equal(compareVersionVectors({ a: 1 }, { b: 1 }), 'concurrent');
  assert.deepEqual(mergeVersionVectors({ a: 2, b: 1 }, { a: 1, c: 3 }), { a: 2, b: 1, c: 3 });

  for (const invalid of [null, [], 'vector', { ' ': 1 }, { a: -1 }, { a: 1.5 }, { a: Number.MAX_SAFE_INTEGER + 1 }, { a: '2' }]) {
    assert.throws(() => normalizeVersionVector(invalid), TypeError);
  }
  assert.throws(() => incrementVersionVector({}, ' '), TypeError);
  assert.throws(() => incrementVersionVector({ a: Number.MAX_SAFE_INTEGER }, 'a'), RangeError);
});

test('preserva identificadores especiales de dispositivos en vectores causales', () => {
  const specialVector = JSON.parse('{"__proto__":2,"constructor":1,"toString":3}');
  const normalized = normalizeVersionVector(specialVector);
  assert.equal(Object.prototype.hasOwnProperty.call(normalized, '__proto__'), true);
  assert.equal(normalized['__proto__'], 2);
  assert.equal(normalized.constructor, 1);
  assert.equal(normalized.toString, 3);
  assert.deepEqual(JSON.parse(JSON.stringify(normalized)), JSON.parse('{"__proto__":2,"constructor":1,"toString":3}'));

  const incremented = incrementVersionVector(specialVector, 'constructor');
  assert.equal(Object.prototype.hasOwnProperty.call(incremented, '__proto__'), true);
  assert.equal(incremented.constructor, 2);
  assert.equal(incremented.toString, 3);
  assert.equal(compareVersionVectors(specialVector, JSON.parse('{"__proto__":1,"constructor":1,"toString":2}')), 'dominates');

  const merged = mergeVersionVectors(specialVector, JSON.parse('{"__proto__":1,"constructor":3,"header":4}'));
  assert.deepEqual(JSON.parse(JSON.stringify(merged)), JSON.parse('{"__proto__":2,"constructor":3,"header":4,"toString":3}'));
});
