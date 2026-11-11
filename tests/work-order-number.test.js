import test from 'node:test';
import assert from 'node:assert/strict';
import { nextWorkOrderNumber } from '../src/storage/work-order-number.js';

test('dos dispositivos desconectados generan números distintos', () => {
  const a = nextWorkOrderNumber('A1B2C3D4E5F6', []);
  const b = nextWorkOrderNumber('112233445566', []);
  assert.equal(a, 'OT-A1B2C3D4E5F6-0001');
  assert.equal(b, 'OT-112233445566-0001');
  assert.notEqual(a, b);
});

test('cada dispositivo continúa su propia secuencia sin depender de otros', () => {
  const records = [
    { numero: 'OT-A1B2C3D4E5F6-0001' },
    { numero: 'OT-A1B2C3D4E5F6-0003' },
    { numero: 'OT-112233445566-0001' },
    { numero: 'OT-0009' }
  ];
  assert.equal(nextWorkOrderNumber('A1B2C3D4E5F6', records), 'OT-A1B2C3D4E5F6-0004');
  assert.equal(nextWorkOrderNumber('112233445566', records), 'OT-112233445566-0002');
});

test('conserva los números históricos y no los mezcla con la secuencia nueva', () => {
  const records = [{ numero: 'OT-0099' }, { numero: 'OT-0100' }];
  assert.equal(nextWorkOrderNumber('ABCDEF123456', records), 'OT-ABCDEF123456-0001');
});

test('rechaza identificadores de dispositivo incompletos', () => {
  assert.throws(() => nextWorkOrderNumber('ABC123', []), /identificador del dispositivo/);
});
