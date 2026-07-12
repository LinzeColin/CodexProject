import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import ts from "typescript";

const APP_ROOT = path.resolve(import.meta.dirname, "..");
const SRC_ROOT = path.join(APP_ROOT, "src");
const APP_FILE = path.join(SRC_ROOT, "App.tsx");
const SHELL_FILE = path.join(SRC_ROOT, "app", "MemoryAtlasShell.tsx");
const ROUTE_REGISTRY_FILE = path.join(SRC_ROOT, "app", "routeRegistry.tsx");
const MAIN_FILE = path.join(SRC_ROOT, "main.tsx");

const REQUIRED_FEATURES = [
  "overview",
  "actions",
  "assets",
  "topics",
  "search-review",
  "summary-iteration",
  "sync",
  "settings",
];
const REQUIRED_VIEWS = [
  "home",
  "galaxy",
  "notion",
  "roi",
  "obsidian",
  "timeline",
  "contribution",
  "wordcloud",
  "search",
  "summary",
];
const MAX_APP_LINES = 800;
const MAX_SHELL_LINES = 1200;
const MAX_FEATURE_MODULE_LINES = 700;
const SOURCE_EXTENSIONS = [".ts", ".tsx", ".mts", ".mjs", ".js", ".jsx"];

const failures = [];

function fail(message) {
  failures.push(message);
}

function relative(file) {
  return path.relative(APP_ROOT, file).split(path.sep).join("/");
}

function lineCount(file) {
  return fs.readFileSync(file, "utf8").split(/\r?\n/).length;
}

function sourceFile(file) {
  const text = fs.readFileSync(file, "utf8");
  const kind = file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  return ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, kind);
}

function moduleSpecifiers(file) {
  const result = [];
  for (const statement of sourceFile(file).statements) {
    if ((ts.isImportDeclaration(statement) || ts.isExportDeclaration(statement)) && statement.moduleSpecifier) {
      result.push(statement.moduleSpecifier.text);
    }
  }
  return result;
}

function resolveRelativeImport(fromFile, specifier) {
  if (!specifier.startsWith(".")) return null;
  const base = path.resolve(path.dirname(fromFile), specifier);
  const candidates = [
    base,
    ...SOURCE_EXTENSIONS.map((extension) => `${base}${extension}`),
    ...SOURCE_EXTENSIONS.map((extension) => path.join(base, `index${extension}`)),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate) && fs.statSync(candidate).isFile()) ?? null;
}

function productionGraph(entry) {
  const reachable = new Set();
  const queue = [entry];
  while (queue.length) {
    const current = queue.pop();
    if (!current || reachable.has(current) || !current.startsWith(SRC_ROOT)) continue;
    reachable.add(current);
    for (const specifier of moduleSpecifiers(current)) {
      const target = resolveRelativeImport(current, specifier);
      if (target && !reachable.has(target)) queue.push(target);
    }
  }
  return reachable;
}

function allSourceFiles(root) {
  if (!fs.existsSync(root)) return [];
  const result = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const absolute = path.join(root, entry.name);
    if (entry.isDirectory()) result.push(...allSourceFiles(absolute));
    else if (SOURCE_EXTENSIONS.some((extension) => entry.name.endsWith(extension))) result.push(absolute);
  }
  return result;
}

function featureName(file) {
  const relativeToFeatures = path.relative(path.join(SRC_ROOT, "features"), file);
  if (relativeToFeatures.startsWith("..")) return null;
  return relativeToFeatures.split(path.sep)[0] ?? null;
}

function validateThinApp() {
  if (!fs.existsSync(APP_FILE)) {
    fail("src/App.tsx is missing");
    return;
  }
  const lines = lineCount(APP_FILE);
  if (lines > MAX_APP_LINES) fail(`src/App.tsx has ${lines} lines; maximum is ${MAX_APP_LINES}`);

  const source = sourceFile(APP_FILE);
  const nonImports = source.statements.filter((statement) => !ts.isImportDeclaration(statement));
  const appFunctions = nonImports.filter(
    (statement) => ts.isFunctionDeclaration(statement) && statement.name?.text === "App",
  );
  if (appFunctions.length !== 1 || nonImports.length !== 1) {
    fail("src/App.tsx must contain only imports and one exported App function");
  }
  const allowed = new Set(["./app/AppProviders", "./app/FeatureRouter", "./app/MemoryAtlasShell"]);
  const imports = moduleSpecifiers(APP_FILE);
  const unexpected = imports.filter((specifier) => !allowed.has(specifier));
  if (unexpected.length || imports.length !== allowed.size) {
    fail(`src/App.tsx imports must be exactly the three app composition modules; got ${imports.join(", ")}`);
  }
}

function validateShell() {
  if (!fs.existsSync(SHELL_FILE)) {
    fail("src/app/MemoryAtlasShell.tsx is missing");
    return;
  }
  const lines = lineCount(SHELL_FILE);
  if (lines > MAX_SHELL_LINES) fail(`MemoryAtlasShell.tsx has ${lines} lines; maximum is ${MAX_SHELL_LINES}`);
}

function routeKeys() {
  if (!fs.existsSync(ROUTE_REGISTRY_FILE)) {
    fail("src/app/routeRegistry.tsx is missing");
    return [];
  }
  const source = sourceFile(ROUTE_REGISTRY_FILE);
  for (const statement of source.statements) {
    if (!ts.isVariableStatement(statement)) continue;
    for (const declaration of statement.declarationList.declarations) {
      if (!ts.isIdentifier(declaration.name) || declaration.name.text !== "ROUTE_REGISTRY" || !declaration.initializer) continue;
      let initializer = declaration.initializer;
      if (ts.isSatisfiesExpression(initializer) || ts.isAsExpression(initializer)) initializer = initializer.expression;
      if (!ts.isObjectLiteralExpression(initializer)) {
        fail("ROUTE_REGISTRY must be an object literal");
        return [];
      }
      return initializer.properties.flatMap((property) => {
        if (!ts.isPropertyAssignment(property) && !ts.isShorthandPropertyAssignment(property)) return [];
        if (ts.isIdentifier(property.name) || ts.isStringLiteral(property.name)) return [property.name.text];
        return [];
      });
    }
  }
  fail("routeRegistry.tsx does not declare ROUTE_REGISTRY");
  return [];
}

function validateRoutes() {
  const actual = routeKeys();
  const missing = REQUIRED_VIEWS.filter((view) => !actual.includes(view));
  const extra = actual.filter((view) => !REQUIRED_VIEWS.includes(view));
  const duplicates = actual.filter((view, index) => actual.indexOf(view) !== index);
  if (missing.length || extra.length || duplicates.length || actual.length !== REQUIRED_VIEWS.length) {
    fail(`route registry mismatch: missing=${missing.join("|")} extra=${extra.join("|")} duplicates=${duplicates.join("|")}`);
  }
}

function validateFeatures(reachable) {
  for (const feature of REQUIRED_FEATURES) {
    const directory = path.join(SRC_ROOT, "features", feature);
    const indexFile = ["index.ts", "index.tsx"].map((name) => path.join(directory, name)).find(fs.existsSync);
    if (!indexFile) {
      fail(`feature ${feature} is missing a public index`);
      continue;
    }
    const ownedFiles = allSourceFiles(directory).filter((file) => file !== indexFile);
    if (!ownedFiles.length) fail(`feature ${feature} has no owned implementation module`);
    for (const file of ownedFiles) {
      const lines = lineCount(file);
      if (lines > MAX_FEATURE_MODULE_LINES) {
        fail(`${relative(file)} has ${lines} lines; feature module maximum is ${MAX_FEATURE_MODULE_LINES}`);
      }
    }
    if (!moduleSpecifiers(indexFile).length) fail(`feature ${feature} public index exports no mounted implementation`);
    if (!reachable.has(indexFile)) fail(`feature ${feature} public index is not reachable from src/main.tsx`);
  }
}

function validateNoLayerCycles() {
  const layerFiles = ["app", "providers", "features", "shared"]
    .map((name) => path.join(SRC_ROOT, name))
    .flatMap(allSourceFiles);
  const layerSet = new Set(layerFiles);
  const graph = new Map(
    layerFiles.map((file) => [
      file,
      moduleSpecifiers(file)
        .map((specifier) => resolveRelativeImport(file, specifier))
        .filter((target) => target && layerSet.has(target)),
    ]),
  );
  const state = new Map();
  const stack = [];
  const visit = (file) => {
    state.set(file, "visiting");
    stack.push(file);
    for (const target of graph.get(file) ?? []) {
      if (state.get(target) === "done") continue;
      if (state.get(target) === "visiting") {
        const start = stack.indexOf(target);
        fail(`layer import cycle: ${[...stack.slice(start), target].map(relative).join(" -> ")}`);
        continue;
      }
      visit(target);
    }
    stack.pop();
    state.set(file, "done");
  };
  for (const file of layerFiles) {
    if (!state.has(file)) visit(file);
  }
}

function validateDependencyDirections() {
  const roots = ["app", "providers", "features", "shared"].map((name) => path.join(SRC_ROOT, name));
  for (const file of roots.flatMap(allSourceFiles)) {
    const sourceFeature = featureName(file);
    const sourceRelative = relative(file);
    for (const specifier of moduleSpecifiers(file)) {
      const target = resolveRelativeImport(file, specifier);
      if (!target || !target.startsWith(SRC_ROOT)) continue;
      const targetRelative = path.relative(SRC_ROOT, target).split(path.sep).join("/");
      const targetFeature = featureName(target);

      if (sourceFeature && (target === APP_FILE || targetRelative.startsWith("app/"))) {
        fail(`${sourceRelative} imports forbidden app layer ${targetRelative}`);
      }
      if (sourceFeature && targetFeature && sourceFeature !== targetFeature) {
        fail(`${sourceRelative} imports another feature ${targetRelative}`);
      }
      if (sourceRelative.startsWith("src/providers/") && targetRelative.startsWith("features/")) {
        fail(`${sourceRelative} imports forbidden feature ${targetRelative}`);
      }
      if (
        sourceRelative.startsWith("src/shared/") &&
        (
          targetRelative.startsWith("components/") ||
          targetRelative.startsWith("features/") ||
          targetRelative.startsWith("providers/") ||
          targetRelative.startsWith("app/")
        )
      ) {
        fail(`${sourceRelative} imports forbidden upper layer ${targetRelative}`);
      }
    }
  }
}

function main() {
  validateThinApp();
  validateShell();
  validateRoutes();
  const reachable = fs.existsSync(MAIN_FILE) ? productionGraph(MAIN_FILE) : new Set();
  if (!reachable.size) fail("production graph from src/main.tsx is empty");
  validateFeatures(reachable);
  validateDependencyDirections();
  validateNoLayerCycles();

  if (failures.length) {
    console.error("Memory Atlas v1.2.1 S04-P1-T1 structure: FAIL");
    for (const failure of failures) console.error(`- ${failure}`);
    process.exit(1);
  }
  console.log(`Memory Atlas v1.2.1 S04-P1-T1 structure: PASS (${reachable.size} production modules)`);
}

main();
