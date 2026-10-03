// Run every scripts/check_*.mjs and summarise. Exit non-zero if any fail.
// `npm test` runs this. Pass --quiet to hide passing checks' output.
import { readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const quiet = process.argv.includes('--quiet');
const checks = readdirSync(here)
  .filter((f) => /^check_.*\.mjs$/.test(f))
  .sort();
const results = [];
for (const file of checks) {
  const started = Date.now();
  const run = spawnSync(process.execPath, [join(here, file)], { encoding: 'utf8', timeout: 300000 });
  const ok = run.status === 0;
  results.push({ file, ok, seconds: ((Date.now() - started) / 1000).toFixed(1) });
  if (!ok || !quiet) {
    const output = (run.stdout + run.stderr).trim().split('\n');
    // On failure show the assertion message and the first stack frame, not the JSON dumps or Node banner.
    const shown = ok
      ? output.slice(-1)
      : output
          .filter((l) => /Error|assert|Stale|expected|actual|at file:/.test(l) && !/node:internal/.test(l))
          .slice(0, 6);
    console.log(`${ok ? 'PASS' : 'FAIL'} ${file}\n  ${shown.join('\n  ')}`);
  }
}
const failed = results.filter((r) => !r.ok);
console.log(
  `\n${results.length - failed.length}/${results.length} checks passed` +
    (failed.length ? `; failing: ${failed.map((r) => r.file).join(', ')}` : '')
);
process.exit(failed.length ? 1 : 0);
