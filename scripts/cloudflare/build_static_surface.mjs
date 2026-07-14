#!/usr/bin/env node

import { cp, mkdir, rm, stat } from 'node:fs/promises';
import { resolve } from 'node:path';

function valueAfter(flag) {
  const index = process.argv.indexOf(flag);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

const sourceArg = valueAfter('--source');
const outputArg = valueAfter('--output');

if (!sourceArg || !outputArg) {
  console.error('usage: build_static_surface.mjs --source <dir> --output <dir>');
  process.exit(2);
}

const source = resolve(process.cwd(), sourceArg);
const output = resolve(process.cwd(), outputArg);

if (source === output || source.startsWith(`${output}/`)) {
  console.error('output must not equal or contain source');
  process.exit(2);
}

const sourceStat = await stat(source).catch(() => null);
const indexStat = await stat(resolve(source, 'index.html')).catch(() => null);
if (!sourceStat?.isDirectory() || !indexStat?.isFile()) {
  console.error(`source must contain index.html: ${source}`);
  process.exit(1);
}

await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(source, output, { recursive: true, force: true });
console.log(`PASS: static surface built ${sourceArg} -> ${outputArg}`);
