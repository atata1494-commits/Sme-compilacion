const MAX_COUNTER = Number.MAX_SAFE_INTEGER;

const hasOwn = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const counterFor = (vector, deviceId) => hasOwn(vector, deviceId) ? vector[deviceId] : 0;

export function normalizeVersionVector(input) {
  if (input == null || typeof input !== 'object' || Array.isArray(input)) {
    throw new TypeError('El vector de versiones debe ser un objeto.');
  }
  const entries = [];
  for (const deviceId of Object.keys(input).sort()) {
    if (!deviceId.trim()) throw new TypeError('El vector contiene un dispositivo sin identificador.');
    const counter = input[deviceId];
    if (!Number.isSafeInteger(counter) || counter < 0 || counter > MAX_COUNTER) {
      throw new TypeError('El vector contiene un contador inválido.');
    }
    if (counter > 0) entries.push([deviceId, counter]);
  }
  // Object.fromEntries safely creates own properties even for "__proto__".
  return Object.fromEntries(entries);
}

export function incrementVersionVector(input, deviceId) {
  if (typeof deviceId !== 'string' || !deviceId.trim()) {
    throw new TypeError('Se necesita un identificador de dispositivo válido.');
  }
  const vector = normalizeVersionVector(input);
  const next = counterFor(vector, deviceId) + 1;
  if (!Number.isSafeInteger(next)) throw new RangeError('Se agotó el contador de versiones del dispositivo.');
  const entries = Object.entries(vector).filter(([key]) => key !== deviceId);
  entries.push([deviceId, next]);
  entries.sort(([a], [b]) => a.localeCompare(b));
  return Object.fromEntries(entries);
}

export function compareVersionVectors(leftInput, rightInput) {
  const left = normalizeVersionVector(leftInput);
  const right = normalizeVersionVector(rightInput);
  const devices = new Set([...Object.keys(left), ...Object.keys(right)]);
  let leftGreater = false;
  let rightGreater = false;
  for (const deviceId of devices) {
    const a = counterFor(left, deviceId);
    const b = counterFor(right, deviceId);
    if (a > b) leftGreater = true;
    if (b > a) rightGreater = true;
  }
  if (!leftGreater && !rightGreater) return 'equal';
  if (leftGreater && !rightGreater) return 'dominates';
  if (!leftGreater && rightGreater) return 'dominated';
  return 'concurrent';
}

export function mergeVersionVectors(leftInput, rightInput) {
  const left = normalizeVersionVector(leftInput);
  const right = normalizeVersionVector(rightInput);
  const entries = [];
  for (const deviceId of [...new Set([...Object.keys(left), ...Object.keys(right)])].sort()) {
    const counter = Math.max(counterFor(left, deviceId), counterFor(right, deviceId));
    if (counter > 0) entries.push([deviceId, counter]);
  }
  return Object.fromEntries(entries);
}
