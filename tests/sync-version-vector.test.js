import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeVersionVector, incrementVersionVector, compareVersionVectors, mergeVersionVectors } from '../src/storage/sync-version-vector.js';

test('normaliza vectores y ordena las claves para una serialización estable', () => {
  assert.deepEqual(normalizeVersionVector({ 'device-b': 2, 'device-a': 1, unused: 0 }), { 'device-a': 1, 'device-b': 2 });
});

test('incrementa solo el contador del dispositivo local', () => {
  assert.deepEqual(incrementVersionVector({ 'device-a': 2, 'device-b': 4 }, 'device-a'), { 'device-a': 3, 'device-b': 4 });
});

test('distingue versiones causales, iguales y concurrentes', () => {
  assert.equal(compareVersionVectors({ a: 2, b: 1 }, { a: 1, b: 1 }), 'dominates');
  assert.equal(compareVersionVectors({ a: 1 }, { a: 2 }), 'dominated');
  assert.equal(compareVersionVectors({ a: 1 }, { a: 1 }), 'equal');
  assert.equal(compareVersionVectors({ a: 1 }, { b: 1 }), 'concurrent');
});

test('fusiona vectores tomando el máximo por dispositivo', () => {
  assert.deepEqual(mergeVersionVectors({ a: 2, b: 1 }, { a: 1, c: 3 }), { a: 2, b: 1, c: 3 });
});

test('rechaza contadores negativos, fraccionarios y dispositivos vacíos', () => {
  assert.throws(() => normalizeVersionVector({ a: -1 }));
  assert.throws(() => normalizeVersionVector({ a: 1.5 }));
  assert.throws(() => incrementVersionVector({}, '   '));
});
