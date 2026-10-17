import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const mainJavaRoot = path.join(root, 'android/app/src/main/java');
const appGradle = path.join(root, 'android/app/build.gradle');
const templateRoot = path.join(root, 'scripts/templates');

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const out = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...await walk(full));
    else if (entry.isFile() && entry.name === 'MainActivity.java') out.push(full);
  }
  return out;
}

const activities = await walk(mainJavaRoot);
if (activities.length !== 1) throw new Error('Se esperaba una única MainActivity.java; se encontraron ' + activities.length);
const activityPath = activities[0];
let activity = await fs.readFile(activityPath, 'utf8');
const packageMatch = activity.match(/^\s*package\s+([A-Za-z0-9_.]+)\s*;/m);
if (!packageMatch) throw new Error('No se pudo determinar el paquete Android desde MainActivity.java.');
const packageName = packageMatch[1];
const packageDir = path.join(mainJavaRoot, ...packageName.split('.'));
await fs.mkdir(packageDir, { recursive: true });

for (const [templateName, targetName] of [
  ['SmeBackupWorker.java.template', 'SmeBackupWorker.java'],
  ['SmeBackupScheduler.java.template', 'SmeBackupScheduler.java'],
  ['SmeBackupPlugin.java.template', 'SmeBackupPlugin.java']
]) {
  const template = await fs.readFile(path.join(templateRoot, templateName), 'utf8');
  await fs.writeFile(path.join(packageDir, targetName), template.replaceAll('__PACKAGE__', packageName));
}

const packageEnd = activity.indexOf(';', activity.indexOf('package ')) + 1;
if (packageEnd <= 0 || !activity.includes('class MainActivity')) throw new Error('No se pudo reconocer MainActivity.java.');
const importBlock = activity.slice(0, activity.indexOf('class MainActivity'));
if (!importBlock.includes('import android.os.Bundle;')) {
  activity = activity.slice(0, packageEnd) + '\n\nimport android.os.Bundle;' + activity.slice(packageEnd);
}
if (!activity.includes('import ' + packageName + '.SmeBackupPlugin;')) {
  const refreshedPackageEnd = activity.indexOf(';', activity.indexOf('package ')) + 1;
  activity = activity.slice(0, refreshedPackageEnd) + '\n\nimport ' + packageName + '.SmeBackupPlugin;' + activity.slice(refreshedPackageEnd);
}
if (!activity.includes('SmeBackupScheduler.schedule')) {
  const closing = activity.lastIndexOf('}');
  if (closing < 0) throw new Error('No se pudo modificar MainActivity.java.');
  const method = '\n\n    @Override\n    public void onCreate(Bundle savedInstanceState) {\n        registerPlugin(SmeBackupPlugin.class);\n        super.onCreate(savedInstanceState);\n        SmeBackupScheduler.schedule(getApplicationContext());\n    }\n';
  activity = activity.slice(0, closing) + method + activity.slice(closing);
} else if (!activity.includes('registerPlugin(SmeBackupPlugin.class)')) {
  activity = activity.replace('super.onCreate(savedInstanceState);', 'registerPlugin(SmeBackupPlugin.class);\n        super.onCreate(savedInstanceState);');
}
await fs.writeFile(activityPath, activity);

let gradle = await fs.readFile(appGradle, 'utf8');
if (!gradle.includes('androidx.work:work-runtime')) {
  const dependencyBlock = gradle.match(/dependencies\s*\{/);
  if (!dependencyBlock) throw new Error('No se encontró el bloque dependencies en android/app/build.gradle.');
  const insertAt = dependencyBlock.index + dependencyBlock[0].length;
  gradle = gradle.slice(0, insertAt) + '\n    implementation "androidx.work:work-runtime:2.10.0"' + gradle.slice(insertAt);
  await fs.writeFile(appGradle, gradle);
}
console.log('Configuración de respaldo SQLite nativo generada.');
