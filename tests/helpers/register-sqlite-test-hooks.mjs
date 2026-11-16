import { registerHooks } from 'node:module';
import { pathToFileURL } from 'node:url';

const coreMock = new URL('./capacitor-core.mock.mjs', import.meta.url).href;
const sqliteMock = new URL('./capacitor-sqlite.mock.mjs', import.meta.url).href;

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === '@capacitor/core') return { url: coreMock, shortCircuit: true };
    if (specifier === '@capacitor-community/sqlite') return { url: sqliteMock, shortCircuit: true };
    if (specifier.endsWith('?raw')) {
      const resolved = nextResolve(specifier.slice(0, -4), context);
      return { ...resolved, url: resolved.url + '?raw', shortCircuit: true };
    }
    return nextResolve(specifier, context);
  },
  load(url, context, nextLoad) {
    if (url.endsWith('?raw')) {
      const original = url.slice(0, -4);
      const loaded = nextLoad(original, { ...context, format: 'module' });
      const source = typeof loaded.source === 'string' ? loaded.source : Buffer.from(loaded.source).toString('utf8');
      return { format: 'module', source: `export default ${JSON.stringify(source)};`, shortCircuit: true };
    }
    return nextLoad(url, context);
  }
});
