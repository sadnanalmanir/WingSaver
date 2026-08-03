#!/usr/bin/env node
/**
 * Fail if openapi.json / generated schema.ts are out of date vs the live FastAPI app.
 *
 * 1. Re-export OpenAPI from the API
 * 2. Re-run openapi-typescript
 * 3. git diff --exit-code on packages/openapi tracked artifacts
 */
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const pkgRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(pkgRoot, "../..");

function run(cmd, cwd = repoRoot) {
  console.log(`$ ${cmd}`);
  execSync(cmd, { cwd, stdio: "inherit" });
}

run("uv run python scripts/export_openapi.py", path.join(repoRoot, "apps/api"));
run("pnpm exec openapi-typescript openapi.json -o src/schema.ts", pkgRoot);

const paths =
  "packages/openapi/openapi.json packages/openapi/src/schema.ts";
const porcelain = execSync(`git status --porcelain -- ${paths}`, {
  cwd: repoRoot,
  encoding: "utf8",
}).trim();
const diff = execSync(`git diff -- ${paths}`, {
  cwd: repoRoot,
  encoding: "utf8",
});

if (porcelain || diff) {
  console.error(porcelain || diff);
  console.error(
    "\nOpenAPI drift detected. Run:\n  pnpm openapi:sync\nthen commit packages/openapi/openapi.json and packages/openapi/src/schema.ts\n",
  );
  process.exit(1);
}
console.log("OpenAPI artifacts are up to date.");
