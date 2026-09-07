import { gunzipSync } from 'node:zlib';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { spaces, setSpaceCutaway, publicViews } from './museum.ts';

const loader = new GLTFLoader().register(() => ({
  name: 'HEADLESS_TEXTURES',
  loadTexture: async () => new THREE.Texture(),
}));
const results = [];
for (const name of new Set(spaces.map((s) => s.model))) {
  const bytes = gunzipSync(
    readFileSync(
      new URL('../public/models/' + name + '.glb.gz', import.meta.url),
    ),
  );
  const { scene } = await loader.parseAsync(
    bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    '',
  );
  const bounds = new THREE.Box3().setFromObject(scene);
  assert.ok(!bounds.isEmpty());
  let lights = 0,
    meshes = 0;
  const roofs = [];
  scene.traverse((o) => {
    if (o.userData.roof) roofs.push(o);
    if (o instanceof THREE.Mesh) {
      meshes++;
      assert.ok(o.geometry.attributes.position.count > 0);
    }
    if (o instanceof THREE.SpotLight || o instanceof THREE.PointLight) {
      assert.ok(
        Number.isFinite(o.userData.web_intensity) &&
          o.userData.web_intensity > 0,
        name + ' light metadata',
      );
      lights++;
    }
  });
  assert.ok(lights > 0, name + ' real light nodes');
  const publicSlug =
    name === 'museum-architecture' ? 'campus' : name.replace('public/', '');
  const views = publicViews[publicSlug];
  const sightLines = [];
  if (views) {
    scene.updateMatrixWorld(true);
    for (const view of views) {
      const origin = new THREE.Vector3(...view.camera);
      const ray = new THREE.Raycaster(
        origin,
        new THREE.Vector3(...view.target).sub(origin).normalize(),
      );
      const first = ray.intersectObject(scene, true)[0];
      assert.ok(
        first && first.distance > 0.5,
        publicSlug + ' ' + view.label + ' clear initial sight line',
      );
      sightLines.push({ label: view.label, nearestSurface: first.distance });
    }
    if (publicSlug === 'arrival' || publicSlug === 'atrium') {
      let glass = 0;
      scene.traverse((o) => {
        if (!(o instanceof THREE.Mesh)) return;
        for (const material of Array.isArray(o.material)
          ? o.material
          : [o.material]) {
          if (material.name === '12_中庭低反射玻璃') {
            assert.ok(
              material.transmission > 0.85,
              publicSlug + ' exported transparent balustrade',
            );
            glass++;
          }
        }
      });
      assert.ok(glass > 0, publicSlug + ' glass material present');
    }
  }
  if (name.startsWith('galleries/') || name === 'museum-architecture')
    assert.ok(roofs.length > 0, name + ' roof nodes');
  if (name === 'public/arrival') {
    scene.updateMatrixWorld(true);
    const ray = new THREE.Raycaster();
    ray.set(new THREE.Vector3(0, 0.8, 2), new THREE.Vector3(0, -1, 0));
    const lower = ray.intersectObject(scene, true)[0];
    assert.ok(lower && lower.point.y < -6.5, 'Opening reveals the lower hall');
    ray.set(new THREE.Vector3(12, 0.8, 0), new THREE.Vector3(0, -1, 0));
    const floor = ray.intersectObject(scene, true)[0];
    assert.ok(floor && Math.abs(floor.point.y) < 0.05, 'Landing remains solid');
    console.log('PASS arrival opening, landing and three initial sight lines');
  }
  setSpaceCutaway(scene, true);
  for (const roof of roofs) {
    assert.equal(
      roof.visible,
      false,
      name + ' roof hidden, including multi-material groups',
    );
    roof.traverse((child) => {
      if (!(child instanceof THREE.Mesh)) return;
      let visible = true;
      for (let parent = child; parent; parent = parent.parent)
        visible &&= parent.visible;
      assert.equal(visible, false, name + ' no visible child roof mesh');
    });
  }
  setSpaceCutaway(scene, false);
  for (const roof of roofs)
    assert.equal(roof.visible, true, name + ' roof restored');
  results.push({
    model: name,
    lights,
    roofs: roofs.length,
    meshes,
    bounds: bounds.getSize(new THREE.Vector3()).toArray(),
    cutaway_and_restore: 'passed',
    publicSightLines: sightLines,
  });
  console.log('PASS', name, lights, 'lights', roofs.length, 'roof nodes');
}
writeFileSync(
  new URL('../../reports/public-12-runtime.json', import.meta.url),
  JSON.stringify(
    {
      results,
      scope:
        'Real Three.js GLB parsing, bounds, material-group cutaway and calibrated light metadata; textures stubbed, no browser GPU or DOM QA',
    },
    null,
    2,
  ),
);
