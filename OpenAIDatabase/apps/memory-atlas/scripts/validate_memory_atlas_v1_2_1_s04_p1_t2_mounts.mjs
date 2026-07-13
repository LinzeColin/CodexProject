import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import ts from "typescript";

const APP_ROOT = path.resolve(import.meta.dirname, "..");
const SRC_ROOT = path.join(APP_ROOT, "src");
const MAIN_FILE = path.join(SRC_ROOT, "main.tsx");
const SOURCE_EXTENSIONS = [".ts", ".tsx", ".mts", ".mjs", ".js", ".jsx"];
const EXPERIMENT_ROOT = path.join(SRC_ROOT, "experiments");
const PROPOSAL_EDITOR_FILE = path.join(SRC_ROOT, "components", "ProposalEditor.tsx");
const PROPOSAL_MOUNTS = new Map([
  ["features/actions/WritebackProposalPanel.tsx", "inspector_writeback_panel"],
  ["features/topics/DataGuideMap.tsx", "data_guide_detail_panel"],
]);

const failures = [];
const sourceFileCache = new Map();

function fail(message) {
  failures.push(message);
}

function relative(file) {
  return path.relative(SRC_ROOT, file).split(path.sep).join("/");
}

function isDeclarationFile(file) {
  return file.endsWith(".d.ts") || file.endsWith(".d.mts");
}

function isExperiment(file) {
  return file === EXPERIMENT_ROOT || file.startsWith(`${EXPERIMENT_ROOT}${path.sep}`);
}

function sourceFile(file) {
  const cached = sourceFileCache.get(file);
  if (cached) return cached;
  const text = fs.readFileSync(file, "utf8");
  const kind = file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const parsed = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, kind);
  sourceFileCache.set(file, parsed);
  return parsed;
}

function allSourceFiles(root) {
  if (!fs.existsSync(root)) return [];
  const files = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const absolute = path.join(root, entry.name);
    if (entry.isDirectory()) files.push(...allSourceFiles(absolute));
    else if (SOURCE_EXTENSIONS.some((extension) => entry.name.endsWith(extension))) files.push(absolute);
  }
  return files;
}

function moduleSpecifiers(file) {
  const specifiers = [];
  const visit = (node) => {
    if (
      (ts.isImportDeclaration(node) || ts.isExportDeclaration(node))
      && node.moduleSpecifier
      && ts.isStringLiteral(node.moduleSpecifier)
    ) {
      specifiers.push(node.moduleSpecifier.text);
    }
    if (
      ts.isCallExpression(node)
      && node.expression.kind === ts.SyntaxKind.ImportKeyword
      && node.arguments.length === 1
      && ts.isStringLiteral(node.arguments[0])
    ) {
      specifiers.push(node.arguments[0].text);
    }
    ts.forEachChild(node, visit);
  };
  visit(sourceFile(file));
  return [...new Set(specifiers)];
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

function componentDeclarations(file) {
  if (!file.endsWith(".tsx")) return [];
  const declarations = [];
  for (const statement of sourceFile(file).statements) {
    if (
      ts.isFunctionDeclaration(statement)
      && statement.name
      && /^[A-Z]/.test(statement.name.text)
    ) {
      declarations.push({ file, name: statement.name.text });
    }
    if (!ts.isVariableStatement(statement)) continue;
    for (const declaration of statement.declarationList.declarations) {
      if (
        ts.isIdentifier(declaration.name)
        && /^[A-Z]/.test(declaration.name.text)
        && declaration.initializer
        && (ts.isArrowFunction(declaration.initializer) || ts.isFunctionExpression(declaration.initializer))
      ) {
        declarations.push({ file, name: declaration.name.text });
      }
    }
  }
  return declarations;
}

function jsxMountUseCounts(files) {
  const counts = new Map();
  for (const file of files) {
    const visit = (node) => {
      const opening = ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node) ? node : null;
      if (opening && ts.isIdentifier(opening.tagName)) {
        counts.set(opening.tagName.text, (counts.get(opening.tagName.text) ?? 0) + 1);
      }
      ts.forEachChild(node, visit);
    };
    visit(sourceFile(file));
  }
  return counts;
}

function jsxMounts(files, componentName) {
  const mounts = [];
  for (const file of files) {
    const visit = (node) => {
      const opening = ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node) ? node : null;
      if (opening && ts.isIdentifier(opening.tagName) && opening.tagName.text === componentName) {
        const sourceSurface = opening.attributes.properties.find(
          (attribute) => ts.isJsxAttribute(attribute) && attribute.name.text === "sourceSurface",
        );
        const sourceSurfaceValue = sourceSurface
          && ts.isJsxAttribute(sourceSurface)
          && sourceSurface.initializer
          && ts.isStringLiteral(sourceSurface.initializer)
          ? sourceSurface.initializer.text
          : null;
        mounts.push({ file, sourceSurface: sourceSurfaceValue });
      }
      ts.forEachChild(node, visit);
    };
    visit(sourceFile(file));
  }
  return mounts;
}

function validateProductionImports(reachable) {
  for (const file of reachable) {
    if (isExperiment(file) || isDeclarationFile(file)) continue;
    for (const specifier of moduleSpecifiers(file)) {
      const target = resolveRelativeImport(file, specifier);
      if (target && isExperiment(target)) {
        fail(`production module ${relative(file)} imports isolated experiment ${relative(target)}`);
      }
    }
  }
}

function validateRuntimeReachability(reachable) {
  const runtimeFiles = allSourceFiles(SRC_ROOT)
    .filter((file) => !isDeclarationFile(file) && !isExperiment(file));
  for (const file of runtimeFiles) {
    if (!reachable.has(file)) fail(`runtime orphan: ${relative(file)}`);
  }
  return runtimeFiles;
}

function validateMountedComponents(reachable) {
  const reachableFiles = [...reachable].filter((file) => !isDeclarationFile(file) && !isExperiment(file));
  const declarations = reachableFiles.flatMap(componentDeclarations);
  const jsxMountUses = jsxMountUseCounts(reachableFiles);
  for (const declaration of declarations) {
    if ((jsxMountUses.get(declaration.name) ?? 0) === 0) {
      fail(`unmounted component: ${declaration.name} in ${relative(declaration.file)}`);
    }
  }
  return declarations;
}

function validateProposalEditor(reachable) {
  const reachableFiles = [...reachable].filter((file) => !isDeclarationFile(file) && !isExperiment(file));
  const declarations = reachableFiles
    .flatMap(componentDeclarations)
    .filter((declaration) => declaration.name === "ProposalEditor");
  if (declarations.length !== 1 || declarations[0]?.file !== PROPOSAL_EDITOR_FILE) {
    fail(`ProposalEditor must have one implementation at components/ProposalEditor.tsx; got ${declarations.map((item) => relative(item.file)).join("|") || "none"}`);
  }

  const mounts = jsxMounts(reachableFiles, "ProposalEditor");
  const actualFiles = mounts.map((mount) => relative(mount.file)).sort();
  const expectedFiles = [...PROPOSAL_MOUNTS.keys()].sort();
  if (JSON.stringify(actualFiles) !== JSON.stringify(expectedFiles)) {
    fail(`ProposalEditor mount files differ: expected=${expectedFiles.join("|")} actual=${actualFiles.join("|")}`);
  }
  for (const mount of mounts) {
    const mountFile = relative(mount.file);
    const expectedSource = PROPOSAL_MOUNTS.get(mountFile);
    if (mount.sourceSurface !== expectedSource) {
      fail(`ProposalEditor sourceSurface mismatch in ${mountFile}: expected=${expectedSource} actual=${mount.sourceSurface}`);
    }
    const resolvesEditor = moduleSpecifiers(mount.file)
      .map((specifier) => resolveRelativeImport(mount.file, specifier))
      .includes(PROPOSAL_EDITOR_FILE);
    if (!resolvesEditor) fail(`ProposalEditor mount in ${mountFile} does not resolve to the canonical implementation`);
  }

  const diffMounts = jsxMounts(reachableFiles, "ProposalDiffPreview").map((mount) => relative(mount.file));
  if (diffMounts.length !== 1 || diffMounts[0] !== "components/ProposalEditor.tsx") {
    fail(`ProposalDiffPreview must mount only inside ProposalEditor; got ${diffMounts.join("|") || "none"}`);
  }
  return mounts.length;
}

function main() {
  if (!fs.existsSync(MAIN_FILE)) fail("src/main.tsx is missing");
  const reachable = fs.existsSync(MAIN_FILE) ? productionGraph(MAIN_FILE) : new Set();
  validateProductionImports(reachable);
  const runtimeFiles = validateRuntimeReachability(reachable);
  const components = validateMountedComponents(reachable);
  const proposalMountCount = validateProposalEditor(reachable);

  if (failures.length) {
    console.error("Memory Atlas v1.2.1 S04-P1-T2 mounted UI: FAIL");
    for (const failure of [...new Set(failures)].sort()) console.error(`- ${failure}`);
    process.exit(1);
  }
  console.log(
    `Memory Atlas v1.2.1 S04-P1-T2 mounted UI: PASS (${reachable.size} reachable modules, ${runtimeFiles.length} runtime sources, ${components.length} mounted components, ${proposalMountCount} ProposalEditor surfaces)`,
  );
}

main();
