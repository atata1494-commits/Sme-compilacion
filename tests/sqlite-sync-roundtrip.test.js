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
