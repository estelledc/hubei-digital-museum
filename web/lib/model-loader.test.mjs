import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { loadPublicModel } from './model-loader.ts';

// Exercise the browser loader's actual fetch, progress, gzip and parse pipeline.
// Only GPU image decoding is stubbed, as in the existing model tests.
// The method is invoked below with parse.apply(this, args).
// oxlint-disable-next-line typescript/unbound-method
const parse = GLTFLoader.prototype.parseAsync;
GLTFLoader.prototype.parseAsync = function (...args) {
  this.register(() => ({
    name: 'HEADLESS_TEXTURES',
    loadTexture: async () => new THREE.Texture(),
  }));
  return parse.apply(this, args);
};
const prefix = '/hubei-digital-museum/';
const server = createServer((req, res) => {
  try {
    assert.ok(req.url.startsWith(prefix));
    const name = req.url.slice(prefix.length).split('?')[0];
    const data = readFileSync(new URL('../public/' + name, import.meta.url));
    res.writeHead(200, {
      'Content-Length': data.length,
      'Content-Type': 'application/gzip',
    });
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end();
  }
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
try {
  for (const file of [
    'models/museum-architecture.glb',
    'models/interactive/bells-interactive.glb',
  ]) {
    let loaded,
      error,
      progress = 0;
    await loadPublicModel(
      origin + prefix + file + '?v=public',
      (value) => {
        loaded = value;
      },
      (value) => {
        progress = value.loaded;
      },
      (value) => {
        error = value;
      },
      new AbortController().signal,
    );
    assert.equal(error, undefined);
    assert.ok(loaded.scene.children.length > 0);
    assert.ok(progress > 0);
    if (file.includes('bells')) assert.equal(loaded.animations.length, 65);
    console.log('PASS compressed HTTP loader', file);
  }
  let failure;
  await loadPublicModel(
    origin + prefix + 'missing.glb',
    () => assert.fail(),
    () => {},
    (error) => {
      failure = error;
    },
    new AbortController().signal,
  );
  assert.match(failure.message, /404/);
  console.log('PASS missing-model error reaches the UI callback');
} finally {
  GLTFLoader.prototype.parseAsync = parse;
  await new Promise((resolve) => server.close(resolve));
}
