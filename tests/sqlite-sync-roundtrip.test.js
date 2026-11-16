import test from 'node:test';
import assert from 'node:assert/strict';
import { openSMEStorage } from '../src/storage/sqlite-store.js';
import { databasePaths, cleanupTestDatabases } from './helpers/capacitor-sqlite.mock.mjs';

const emptyDB = () => ({
  clientes: [], vehiculos: [], trabajos: [], presupuestos: [], movimientos: [],
  eventos: [], recepciones: [], diagnosticos: [], cuentas: [], asistencias: [],
  terceros: [], trabajosExternos: [], configHorarios: [], tareas: [], avisos: [],
  solicitudesGasto: []
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
