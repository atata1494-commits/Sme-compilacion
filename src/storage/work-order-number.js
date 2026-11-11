export function normalizeWorkOrderDeviceCode(value) {
  const code = String(value ?? '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (code.length < 8) throw new Error('El identificador del dispositivo para las órdenes no es válido.');
  return code.slice(0, 12);
}

export function nextWorkOrderNumber(deviceCode, records = []) {
  const code = normalizeWorkOrderDeviceCode(deviceCode);
  const prefix = 'OT-' + code + '-';
  const highest = records.reduce((max, record) => {
    const number = String(record?.numero ?? '');
    if (!number.startsWith(prefix)) return max;
    const suffix = number.slice(prefix.length);
    if (!/^\d{4,}$/.test(suffix)) return max;
    return Math.max(max, Number(suffix) || 0);
  }, 0);
  return prefix + String(highest + 1).padStart(4, '0');
}
