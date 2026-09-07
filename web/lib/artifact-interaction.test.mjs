import { gunzipSync } from 'node:zlib';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { ArtifactInteraction, experiences } from './artifact-interaction.ts';
import { artifacts } from './museum.ts';

// Real GLB geometry, hierarchy, extras and clips. Only image decoding is replaced;
// texture appearance is checked separately in Blender renders.
const loader = new GLTFLoader().register(() => ({
  name: 'HEADLESS_TEXTURES',
  loadTexture: async () => new THREE.Texture(),
}));
const load = async (id) => {
  const b = gunzipSync(
    readFileSync(
      new URL(
        `../public/models/interactive/${id}-interactive.glb.gz`,
        import.meta.url,
      ),
    ),
  );
  return loader.parseAsync(
    b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength),
    '',
  );
};
const tick = (c, seconds) => {
  for (let t = 0; t < seconds; t += 0.02) c.update(0.02);
};
assert.deepEqual(
  Object.keys(experiences).sort(),
  artifacts
    .filter((a) => a.id !== 'bells')
    .map((a) => a.id)
    .sort(),
);
const results = [];
for (const [id, config] of Object.entries(experiences)) {
  const gltf = await load(id),
    scene = new THREE.Scene(),
    camera = new THREE.PerspectiveCamera(43, 1.4, 0.0005, 1000);
  scene.add(gltf.scene);
  camera.position.set(0, 1, 5);
  const center = new THREE.Box3()
    .setFromObject(gltf.scene)
    .getCenter(new THREE.Vector3());
  gltf.scene.position.sub(center);
  scene.updateMatrixWorld(true);
  const materials = new Set();
  gltf.scene.traverse((o) => {
    if (o instanceof THREE.Mesh)
      for (const m of Array.isArray(o.material) ? o.material : [o.material])
        materials.add(m);
  });
  const materialColors = [...materials].map((m) => ({
    material: m,
    color: m.color?.toArray(),
    emissive: m.emissive?.toArray(),
    strength: m.emissiveIntensity,
  }));
  let latest;
  const c = new ArtifactInteraction(
    gltf.scene,
    gltf.animations,
    id,
    camera,
    new THREE.Vector3(),
    (s) => (latest = s),
  );
  const startBounds = c.bounds();
  const poses = c.parts.map((p) => ({
    p: p.object.position.clone(),
    q: p.object.quaternion.clone(),
  }));
  const assertRest = () =>
    c.parts.forEach((p, i) => {
      assert.ok(
        p.object.position.distanceTo(poses[i].p) < 1e-7,
        id + ' position reset',
      );
      assert.ok(
        p.object.quaternion.angleTo(poses[i].q) < 1e-7,
        id + ' rotation reset',
      );
      assert.ok(p.object.visible, id + ' visibility reset');
    });
  assert.ok(c.parts.length > 0);
  c.choose(-1);
  assert.equal(latest.index, c.parts.length - 1);
  c.choose(c.parts.length);
  assert.equal(latest.index, 0);
  if (config.mode === 'explode') {
    assert.ok(
      c.parts.some((p) => p.details.length),
      id + ' has real child detail anchors',
    );
    for (let i = 0; i < c.parts.length; i++) {
      c.choose(i);
      for (let j = 0; j < c.parts[i].details.length; j++) {
        const anchor = c.parts[i].details[j];
        assert.equal(
          anchor.parent,
          c.parts[i].object,
          'detail follows its own part',
        );
        const rest = anchor.getWorldPosition(new THREE.Vector3());
        c.setProgress(1);
        gltf.scene.updateMatrixWorld(true);
        assert.ok(
          anchor
            .getWorldPosition(new THREE.Vector3())
            .distanceTo(rest.clone().add(c.parts[i].offset)) < 1e-6,
          'detail moves with explosion',
        );
        c.focusDetail(j);
        tick(c, 1);
        assert.equal(latest.detailIndex, j);
        const target = anchor.getWorldPosition(new THREE.Vector3());
        assert.ok(
          c.target.distanceTo(target) < 1e-6,
          'macro camera centers actual detail',
        );
        c.camera.aspect = 0.72;
        c.reframe();
        tick(c, 1);
        assert.ok(
          c.target.distanceTo(target) < 1e-6,
          'resize preserves chosen macro view',
        );
        assert.equal(
          c.annotations().find((a) => a.selected).label,
          anchor.userData.label,
        );
        c.setProgress(0);
      }
    }
    c.reset();
    c.camera.aspect = 1.4;
    // Web's continuous slider must agree with the actual Blender-exported expanded pose.
    const mixer = new THREE.AnimationMixer(gltf.scene);
    for (const clip of gltf.animations) mixer.clipAction(clip).play();
    mixer.update(2);
    c.parts.forEach((p, i) =>
      assert.ok(
        p.object.position.distanceTo(poses[i].p.clone().add(p.offset)) < 1e-6,
        id + ' Blender/Web expanded pose',
      ),
    );
    mixer.stopAllAction();
    mixer.uncacheRoot(gltf.scene);
    for (const amount of [1, 0, 0.37, 1, 0]) {
      c.setProgress(amount);
      c.parts.forEach((p, i) =>
        assert.ok(
          p.object.position.distanceTo(
            poses[i].p.clone().addScaledVector(p.offset, amount),
          ) < 1e-7,
        ),
      );
    }
    c.setProgress(1);
    c.choose(c.parts.length - 1);
    c.isolate();
    c.parts.forEach((p, i) => assert.equal(p.object.visible, i === c.index));
    c.reset();
    assertRest();
    c.demo();
    tick(c, 2.3);
    assert.ok(c.progress > 0.98, id + ' opens during loop');
    tick(c, 3.1);
    assert.ok(c.progress < 0.01, id + ' loop reassembles');
    c.stop();
    const frozen = c.progress;
    tick(c, 1);
    assert.equal(c.progress, frozen);
    c.reset();
    assertRest();
    c.reducedMotion = true;
    c.toggleExpand();
    assert.equal(c.progress, 1);
    assert.equal(c.playing, false);
    c.reset();
    assertRest();
  } else if (config.mode === 'strike') {
    if (id === 'chimes') assert.equal(c.parts.length, 32);
    for (let i = 0; i < c.parts.length; i++) {
      c.activate(i);
      c.update(0.2);
      scene.updateMatrixWorld(true);
      const part = c.parts[i],
        tool = gltf.scene.getObjectByName(
          `Tool_${String(i + 1).padStart(2, '0')}`,
        );
      assert.ok(tool, id + ' tool exists');
      const point = new THREE.Vector3()
        .fromArray(part.object.userData.strike_point)
        .applyQuaternion(part.quaternion)
        .add(part.position);
      part.object.parent.localToWorld(point);
      assert.ok(
        tool.getWorldPosition(new THREE.Vector3()).distanceTo(point) < 1e-5,
        `${id} ${i} tool reaches fixed surface point`,
      );
      assert.ok(tool.scale.x > 0.99);
      assert.ok(
        tool instanceof THREE.Mesh,
        'the whole beater is one animated mesh',
      );
      tool.geometry.computeBoundingBox();
      assert.ok(
        Math.abs(tool.geometry.boundingBox.max.y - tool.userData.tool_length) <
          1e-6,
        'head geometry has its full length',
      );
      const headCenter = tool.localToWorld(
        new THREE.Vector3(0, tool.userData.tool_length / 2, 0),
      );
      const axis = headCenter
        .sub(tool.getWorldPosition(new THREE.Vector3()))
        .normalize();
      const normal = new THREE.Vector3().fromArray(
        part.object.userData.strike_normal,
      );
      assert.ok(
        axis.dot(normal) > 0.99,
        `${id} ${i} head points away from contact`,
      );
      c.update(0.1);
      if (id === 'chimes') {
        assert.ok(
          part.object.quaternion.angleTo(part.quaternion) > 0.005,
          'selected chime moves',
        );
        c.parts.forEach((p, j) => {
          if (i !== j)
            assert.ok(
              p.object.quaternion.angleTo(p.quaternion) < 1e-7,
              'others still',
            );
        });
      } else assertRest();
      tick(c, 1.4);
      assert.ok(tool.scale.length() < 1e-6, 'tool retracts and disappears');
      c.stop();
      assertRest();
    }
    c.demo();
    tick(c, 1.1);
    assert.ok(latest.playing && latest.hits > 1);
    c.stop();
    const hits = c.hits;
    tick(c, 2);
    assert.equal(c.hits, hits);
    c.reducedMotion = true;
    c.activate(0);
    tick(c, 0.3);
    assertRest();
  } else {
    const camStart = camera.position.clone();
    c.choose(c.parts.length - 1);
    tick(c, 1);
    assert.ok(
      camera.position.distanceTo(camStart) > 0.01,
      id + ' camera inspection moves',
    );
    assertRest();
    c.demo();
    tick(c, 3.8);
    assert.equal(c.index, 0, 'tour wraps');
    c.cancelTour();
    assert.equal(c.playing, false, 'manual orbit cancels tour');
    c.reducedMotion = true;
    c.choose(1);
    assert.ok(
      c.target.distanceTo(
        c.parts[1].object.getWorldPosition(new THREE.Vector3()),
      ) < 1e-7,
      'reduced motion jumps directly',
    );
  }
  c.reset();
  tick(c, 1);
  assertRest();
  for (const s of materialColors) {
    assert.deepEqual(
      s.material.color?.toArray(),
      s.color,
      'selection preserves source base color',
    );
    assert.deepEqual(
      s.material.emissive?.toArray(),
      s.emissive,
      'selection does not tint the artifact',
    );
    assert.equal(s.material.emissiveIntensity, s.strength);
  }
  const endBounds = c.bounds();
  assert.ok(
    startBounds.min.distanceTo(endBounds.min) < 1e-6 &&
      startBounds.max.distanceTo(endBounds.max) < 1e-6,
    id + ' complete reset',
  );
  c.dispose();
  assert.equal(scene.children.length, 1, 'effects cleaned on model switch');
  results.push({
    id,
    mode: config.mode,
    parts: c.parts.length,
    detail_views: c.parts.reduce((n, p) => n + p.details.length, 0),
    real_glb_behavior: 'passed',
  });
  gltf.scene.traverse((o) => {
    if (o instanceof THREE.Mesh) {
      o.geometry.dispose();
      for (const m of Array.isArray(o.material) ? o.material : [o.material])
        m.dispose();
    }
  });
  console.log('PASS', id, config.mode, c.parts.length);
}
writeFileSync(
  new URL(
    '../../reports/artifact-interaction-runtime-10.json',
    import.meta.url,
  ),
  JSON.stringify(
    {
      coverage: 15,
      results,
      scope:
        'Real GLB geometry, extras, animation clips and Three.js runtime; no browser DOM, GPU texture rendering or touch UI acceptance.',
    },
    null,
    2,
  ),
);
console.log(
  'PASS: all 15 new artifact interactions, exported poses, contact, loop, reset, isolation, reduced motion and disposal.',
);
