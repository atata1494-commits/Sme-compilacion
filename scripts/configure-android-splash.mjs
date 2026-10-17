import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const root = process.cwd();
const res = path.join(root, 'android/app/src/main/res');
const source = path.join(root, 'logo.svg');
const background = '#102F30';
const drawableDir = path.join(res, 'drawable-nodpi');
await fs.mkdir(drawableDir, { recursive: true });

// The approved logo SVG embeds the original WebP artwork as a data URI.
// Extract that actual image instead of rasterizing an SVG with an embedded WebP.
const logoSvg = await fs.readFile(source, 'utf8');
const embedded = logoSvg.match(/href="data:image\/webp;base64,([^"]+)"/);
if (!embedded) throw new Error('No se encontró la imagen WebP incrustada en logo.svg.');
const originalLogo = Buffer.from(embedded[1], 'base64');
const logoPng = await sharp(originalLogo)
  .resize({ width: 360, height: 240, fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
  .png()
  .toBuffer();
const splashPng = await sharp({
  create: { width: 512, height: 512, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } }
})
  .composite([{ input: logoPng, gravity: 'centre' }])
  .png()
  .toBuffer();
const splashMeta = await sharp(splashPng).metadata();
if (splashMeta.width !== 512 || splashMeta.height !== 512) throw new Error('El recurso de splash no tiene el tamaño esperado.');
const alpha = await sharp(splashPng).extractChannel('alpha').stats();
if (alpha.max === 0) throw new Error('El recurso del logo quedó completamente transparente.');
await fs.writeFile(path.join(drawableDir, 'sme_splash_logo.png'), splashPng);
console.log('Logo nativo de arranque generado desde la imagen WebP original.');

const colorsPath = path.join(res, 'values/colors.xml');
await fs.mkdir(path.dirname(colorsPath), { recursive: true });
let colors;
try {
  colors = await fs.readFile(colorsPath, 'utf8');
} catch {
  colors = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n</resources>\n';
}
if (/<color name="splashscreen_background">[\s\S]*?<\/color>/.test(colors)) {
  colors = colors.replace(/<color name="splashscreen_background">[\s\S]*?<\/color>/, '<color name="splashscreen_background">' + background + '</color>');
} else {
  colors = colors.replace('</resources>', '    <color name="splashscreen_background">' + background + '</color>\n</resources>');
}
await fs.writeFile(colorsPath, colors);

const backgroundXml = '<?xml version="1.0" encoding="utf-8"?>\n' +
  '<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n' +
  '    <item android:drawable="@color/splashscreen_background" />\n' +
  '    <item>\n' +
  '        <bitmap android:src="@drawable/sme_splash_logo" android:gravity="center" />\n' +
  '    </item>\n' +
  '</layer-list>\n';
const drawableBackgroundDir = path.join(res, 'drawable');
await fs.mkdir(drawableBackgroundDir, { recursive: true });
await fs.writeFile(path.join(drawableBackgroundDir, 'sme_splash_background.xml'), backgroundXml);

function setItem(style, name, value) {
  const escaped = name.replace(/\./g, '\\.');
  const pattern = new RegExp('<item\\s+name="' + escaped + '"[^>]*>[\\s\\S]*?<\\/item>');
  const replacement = '<item name="' + name + '">' + value + '</item>';
  if (pattern.test(style)) return style.replace(pattern, replacement);
  return style.replace(/(<style name="AppTheme\.NoActionBarLaunch"[^>]*>)/, '$1\n        ' + replacement);
}

const styleFiles = [
  path.join(res, 'values/styles.xml'),
  path.join(res, 'values-v31/styles.xml'),
];
let patched = 0;
for (const file of styleFiles) {
  let xml;
  try {
    xml = await fs.readFile(file, 'utf8');
  } catch {
    continue;
  }
  if (!/<style name="AppTheme\.NoActionBarLaunch"/.test(xml)) continue;
  const start = xml.indexOf('<style name="AppTheme.NoActionBarLaunch"');
  const end = xml.indexOf('</style>', start);
  if (end < 0) throw new Error('El tema de arranque no tiene cierre en ' + file);
  const before = xml.slice(0, start);
  let style = xml.slice(start, end + '</style>'.length);
  const after = xml.slice(end + '</style>'.length);
  style = setItem(style, 'windowSplashScreenBackground', '@color/splashscreen_background');
  style = setItem(style, 'windowSplashScreenAnimatedIcon', '@drawable/sme_splash_logo');
  style = setItem(style, 'windowSplashScreenIconBackgroundColor', '@color/splashscreen_background');
  style = setItem(style, 'postSplashScreenTheme', '@style/AppTheme.NoActionBar');
  style = setItem(style, 'android:windowBackground', '@drawable/sme_splash_background');
  xml = before + style + after;
  await fs.writeFile(file, xml);
  patched++;
}
if (patched === 0) {
  throw new Error('No se encontró AppTheme.NoActionBarLaunch en los recursos Android generados; no se aplicó el tema de arranque.');
}
console.log('Splash SME configurado: fondo azul petróleo y logo ovalado, sin texto adicional. Recursos de tema actualizados: ' + patched);
