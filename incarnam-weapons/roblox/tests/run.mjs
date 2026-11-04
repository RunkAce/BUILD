// Runs the Luau spec files in this folder with the real Luau VM (WebAssembly build).
// Setup once:  npm install --prefix /opt/luau @luau-rs/luau@0.739.0
// Run:         node incarnam-weapons/roblox/tests/run.mjs
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, '..', 'src');
const pkg = join(process.env.LUAU_PREFIX || '/opt/luau', 'node_modules', '@luau-rs', 'luau', 'dist', 'direct-api.js');
const { Lua } = await import(pathToFileURL(pkg).href);

const find = (name) => {
  for (const dir of [here, src]) {
    for (const ext of ['.luau', '.lua']) {
      try { return { name, source: readFileSync(join(dir, name + ext), 'utf8') }; } catch {}
    }
  }
  return null;
};

let failures = 0;
for (const file of readdirSync(here).filter((f) => f.endsWith('.spec.luau'))) {
  const lua = await Lua.create({ sandbox: false, resolveModule: (spec) => find(spec.replace(/^\.\//, '')) });
  lua.addEventListener('print', (e) => console.log(e.text));
  try {
    const out = lua.execute(readFileSync(join(here, file), 'utf8'), { name: file });
    failures += Number(out?.[0] ?? 0);
  } catch (err) {
    console.error(`ERROR in ${file}:`, err?.message ?? err);
    failures += 1;
  }
}
process.exit(failures ? 1 : 0);
