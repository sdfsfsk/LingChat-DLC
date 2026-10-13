import { build } from 'vite';
import { resolve, join } from 'node:path';
import { mkdir, readFile, cp, writeFile } from 'node:fs/promises';
const root = resolve(import.meta.dirname, '..');
for (const id of ['twilight', 'star-trail']) {
  const source = join(root, 'packages', id), output = join(root, 'dist', id);
  await build({ configFile: false, root: source, base: './',
    resolve: { alias: { '@': join(source, 'src'), '@dlc/sdk': join(root, 'sdk/index.js') } },
    build: { outDir: join(output, 'web'), emptyOutDir: true, target: 'es2022' }, worker: { format: 'es' } });
  await mkdir(output, { recursive: true });
  await cp(join(source, 'manifest.toml'), join(output, 'manifest.toml'));
  await cp(join(root, 'LICENSE'), join(output, 'LICENSE'));
  await cp(join(root, 'docs'), join(output, 'docs'), { recursive: true });
}
console.log('Packages built. Run python scripts/package.py to create verified ZIPs and catalog.json.');
