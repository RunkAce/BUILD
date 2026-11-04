// Compiles every .luau file with the real Luau compiler (syntax check for code that needs Roblox to run).
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const pkg = join(process.env.LUAU_PREFIX || '/opt/luau', 'node_modules', '@luau-rs', 'luau', 'dist', 'direct-api.js');
const mod = await import(pathToFileURL(pkg).href);
const lua = await mod.Lua.create({ sandbox: false });
const walk = (d) => readdirSync(d).flatMap((f) => { const p = join(d, f); return statSync(p).isDirectory() ? walk(p) : [p]; });
let bad = 0;
for (const f of walk(join(here, '..')).filter((p) => p.endsWith('.luau'))) {
  try { lua.load(readFileSync(f, 'utf8'), { name: f }); console.log('ok   ', f.replace(join(here, '..') + '/', '')); }
  catch (e) { bad++; console.log('FAIL ', f, '\n     ', e?.message ?? e); }
}
process.exit(bad ? 1 : 0);
