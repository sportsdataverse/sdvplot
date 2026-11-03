// Writes tests/fixtures/sdvplotjs_bins_bkn_2000.json: sdvplot-js's own bins on its 2000 real Brooklyn shots, the
// expected output tests/test_bins.py holds sdvplot's port to. Node 24+ (type stripping), from the sdvplot root:
//
//   node tools/sdvplotjs_bins_oracle.ts ../sdvplot-js [rev]   # rev defaults to origin/main
//
// It reads sdvplot-js's bins sources and shot fixture at `rev` with `git show` (the checkout's working tree is never
// touched), joins the two bins modules into one file (they import only each other and InputError), and runs them.
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [repo = "../sdvplot-js", rev = "origin/main"] = process.argv.slice(2);
const git = (...args: string[]): string => execFileSync("git", ["-C", repo, ...args], { encoding: "utf8" });
const sha = git("rev-parse", rev).trim();
const show = (path: string): string => git("show", `${sha}:${path}`);
const code = (path: string): string =>
  show(`packages/sdvplot/src/bins/${path}`)
    .split("\n")
    .filter((line) => !line.startsWith("import "))
    .join("\n");
const dir = mkdtempSync(join(tmpdir(), "sdvplotjs-bins-"));
const bins = join(dir, "bins.ts");
writeFileSync(bins, ["class InputError extends Error {}", code("hexbin.ts"), code("squarebin.ts")].join("\n"));
const { binner, cellPath, cellPoints } = await import(pathToFileURL(bins).href);

const SHOTS = "fixtures/shots/nba-2026-bkn-2000-columns.json";
const src = JSON.parse(show(SHOTS));
type P = { i: number; x: number; y: number };
const run = (o: object, pts: P[]) => {
  const b = binner(o);
  const cells = b.bins(pts, { x: (p: P) => p.x, y: (p: P) => p.y });
  return {
    options: o,
    shape: b.shape,
    size: b.size,
    lattice: b.lattice,
    ids: cells.map((c: { x: number; y: number }) => `${c.x},${c.y}`),
    bins: cells.map((c: P[] & { x: number; y: number }) => [c.x, c.y, c.map((p) => p.i)]),
  };
};
const shots: P[] = src.x_legacy.map((x: number, i: number) => ({ i, x, y: src.y_legacy[i] }));
const lattices = [
  { radius: 10 },
  { radius: 15 },
  { shape: "square", side: 10 },
  { shape: "square", side: 15 },
  { shape: "square", radius: 10, equalArea: true },
].map((o) => run(o, shots));
// -0 folding, NaN skipped, halves toward +infinity, a negative half, a point near an edge
const edge = [[0, 0], [-0, -0], [NaN, 1], [5, 91], [-5, -5], [-15, 25], [2.5, NaN], [-25, -35], [14.999999, 7.5]];
const edgePoints: P[] = edge.map(([x, y], i) => ({ i, x, y }));
const results = [{ radius: 10 }, { shape: "square", side: 10 }].map((o) => {
  const { options, ids, bins: b } = run(o, edgePoints);
  return { options, ids, bins: b };
});
const out = {
  source: {
    sdvplot_js: sha,
    fixture: SHOTS,
    generator: "packages/sdvplot/src/bins/{hexbin,squarebin}.ts run by tools/sdvplotjs_bins_oracle.ts",
  },
  x_legacy: src.x_legacy,
  y_legacy: src.y_legacy,
  game_id: src.game_id,
  lattices,
  edge: { points: edge.map((p) => p.map((v) => (Number.isNaN(v) ? null : v))), results },
  cells: {
    hex10: cellPoints("hex", 10),
    square10: cellPoints("square", 10),
    hexPath10: cellPath("hex", 10),
    squarePath10: cellPath("square", 10),
  },
};
writeFileSync("tests/fixtures/sdvplotjs_bins_bkn_2000.json", `${JSON.stringify(out)}\n`);
console.log(`wrote tests/fixtures/sdvplotjs_bins_bkn_2000.json from sdvplot-js ${sha}`);
