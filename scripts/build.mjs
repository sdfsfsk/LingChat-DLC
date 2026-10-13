import { build } from 'vite';
import { resolve, join } from 'node:path';
import { mkdir, access, cp, readdir } from 'node:fs/promises';
const root = resolve(import.meta.dirname, '..');
const entries = (await readdir(join(root, 'packages'), { withFileTypes: true })).filter(entry => entry.isDirectory()).sort((a, b) => a.name.localeCompare(b.name));
for (const { name: id } of entries) {
  const source = join(root, 'packages', id), output = join(root, 'dist', id);
  try { await access(join(source, 'manifest.toml')); } catch { continue; }
  const isStory = await access(join(source, 'scripts')).then(() => true, () => false);
  if (isStory) {
    await mkdir(output, { recursive: true });
    for (const name of ['manifest.toml', 'scripts', 'LICENSE', 'README.md', 'docs', 'DESIGN-v2.md'])
      await cp(join(source, name), join(output, name), { recursive: true });
    continue;
  }
  await build({ configFile: false, root: source, base: './',
    resolve: { alias: { '@': join(source, 'src'), '@dlc/sdk': join(root, 'sdk/index.js') } },
    build: { outDir: join(output, 'web'), emptyOutDir: true, target: 'es2022' }, worker: { format: 'es' } });
  await mkdir(output, { recursive: true });
  await cp(join(source, 'manifest.toml'), join(output, 'manifest.toml'));
  await cp(join(root, 'LICENSE'), join(output, 'LICENSE'));
  await cp(join(root, 'docs'), join(output, 'docs'), { recursive: true });
}
console.log('Packages built. Run python scripts/package.py to create ZIPs and export their manifests.');
