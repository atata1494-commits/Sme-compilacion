import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const source = path.resolve('icon.svg');
const androidRes = path.resolve('android/app/src/main/res');
const densities = [
  ['mipmap-mdpi', 48],
  ['mipmap-hdpi', 72],
  ['mipmap-xhdpi', 96],
  ['mipmap-xxhdpi', 144],
  ['mipmap-xxxhdpi', 192],
];

// Render the square, petrol-blue and aged-ivory emblem directly for the Android launcher.
// Keeping the full square canvas avoids empty/transparent output on Samsung launchers.
for (const [folder, size] of densities) {
  const dir = path.join(androidRes, folder);
  await fs.mkdir(dir, { recursive: true });
  const png = await sharp(source, { density: 384 })
    .resize(size, size, { fit: 'fill' })
    .png()
    .toBuffer();
  await fs.writeFile(path.join(dir, 'ic_launcher.png'), png);
  await fs.writeFile(path.join(dir, 'ic_launcher_round.png'), png);
  await fs.writeFile(path.join(dir, 'ic_launcher_foreground.png'), png);
}

// Remove generated adaptive-icon XMLs so Android uses the same approved
// launcher artwork on modern and older devices instead of Capacitor defaults.
await fs.rm(path.join(androidRes, 'mipmap-anydpi-v26'), { recursive: true, force: true });
console.log('Generated SME launcher icons from the square petrol-and-ivory icon.svg.');
