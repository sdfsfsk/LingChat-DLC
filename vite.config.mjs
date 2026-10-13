import { resolve } from 'node:path';
export default ({ command }) => ({
  base: './',
  resolve: { alias: { '@dlc/sdk': resolve('sdk/index.js'), '@': resolve(process.argv[2] || 'packages/twilight', 'src') } },
  server: { fs: { allow: [resolve('.')] } },
});
