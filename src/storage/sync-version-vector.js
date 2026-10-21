const MAX_COUNTER = Number.MAX_SAFE_INTEGER;

export function normalizeVersionVector(input) {
  if (input == null || typeof input !== 'object' || Array.isArray(input)) {
    throw new TypeError('El vector de versiones debe ser un objeto.');
  }
  const normalized = {};
  for (const deviceId of Object.keys(input).sort()) {
    if (!deviceId.trim()) throw new TypeError('El vector contiene un dispositivo sin identificador.');
    const counter = input[deviceId];
    if (!Number.isSafeInteger(counter) || counter < 0 || counter > MAX_COUNTER) {
      throw new TypeError('El vector contiene un contador inválido.');
    }
    if (counter > 0) normalized[deviceId] = counter;
  }
  return normalized;
}

export function incrementVersionVector(input, deviceId) {
  if (typeof deviceId !== 'string' || !deviceId.trim()) {
    throw new TypeError('Se necesita un identificador de dispositivo válido.');
  }
  const vector = normalizeVersionVector(input);
  const next = (vector[deviceId] || 0) + 1;
  if (!Number.isSafeInteger(next)) throw new RangeError('Se agotó el contador de versiones del dispositivo.');
  vector[deviceId] = next;
  return Object.fromEntries(Object.keys(vector).sort().map(key => [key, vector[key]]));
}

export function compareVersionVectors(leftInput, rightInput) {
  const left = normalizeVersionVector(leftInput);
  const right = normalizeVersionVector(rightInput);
  const devices = new Set([...Object.keys(left), ...Object.keys(right)]);
  let leftGreater = false;
  let rightGreater = false;
  for (const deviceId of devices) {
    const a = left[deviceId] || 0;
    const b = right[deviceId] || 0;
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
  const merged = {};
  for (const deviceId of [...new Set([...Object.keys(left), ...Object.keys(right)])].sort()) {
    const counter = Math.max(left[deviceId] || 0, right[deviceId] || 0);
    if (counter > 0) merged[deviceId] = counter;
  }
  return merged;
}
