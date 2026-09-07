import { gunzipSync } from 'node:zlib';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { BellInteraction } from './bell-interaction.ts';

// Exercise the shipped animation tracks, not a second hand-written animation formula.
const bytes = gunzipSync(
  readFileSync(
    new URL(
      '../public/models/interactive/bells-interactive.glb.gz',
      import.meta.url,
    ),
  ),
);
const length = bytes.readUInt32LE(12),
  doc = JSON.parse(bytes.subarray(20, 20 + length));
const binStart = 20 + length + 8;
function accessor(id) {
  const a = doc.accessors[id],
    view = doc.bufferViews[a.bufferView];
  assert.equal(a.componentType, 5126);
  assert.ok(!view.byteStride);
  const count = a.count * { SCALAR: 1, VEC3: 3, VEC4: 4 }[a.type];
  const offset = binStart + (view.byteOffset || 0) + (a.byteOffset || 0);
  return Float32Array.from({ length: count }, (_, i) =>
    bytes.readFloatLE(offset + i * 4),
  );
}
const pivots = doc.nodes.filter((n) => /^Bell_\d+$/.test(n.name));
assert.equal(pivots.length, 65);
assert.equal(doc.animations.length, 65);
const model = new THREE.Group(),
  scene = new THREE.Scene(),
  camera = new THREE.PerspectiveCamera();
camera.position.set(1, 4, 10);
scene.add(model);
for (const node of pivots) {
  const group = new THREE.Group();
  group.name = node.name;
  group.userData = node.extras;
  group.position.fromArray(node.translation);
  if (node.rotation) group.quaternion.fromArray(node.rotation);
  group.add(
    new THREE.Mesh(
      new THREE.BoxGeometry(0.2, 0.3, 0.2),
      new THREE.MeshStandardMaterial(),
    ),
  );
  model.add(group);
}
const clips = doc.animations.map((animation) => {
  assert.equal(animation.channels.length, 1);
  const channel = animation.channels[0],
    sampler = animation.samplers[channel.sampler],
    name = doc.nodes[channel.target.node].name;
  assert.equal(channel.target.path, 'rotation');
  const times = accessor(sampler.input),
    values = accessor(sampler.output);
  const rest = new THREE.Quaternion().fromArray(values);
  let peakAngle = 0;
  for (let i = 0; i < values.length; i += 4)
    peakAngle = Math.max(
      peakAngle,
      rest.angleTo(new THREE.Quaternion().fromArray(values, i)),
    );
  assert.ok(
    peakAngle > THREE.MathUtils.degToRad(3),
    'swing is visibly larger than the old sub-degree motion',
  );
  assert.ok(
    times.at(-1) - times[0] >= 3 - 1e-6,
    'bell has time to visibly swing back and settle',
  );
  assert.deepEqual(
    Array.from(values.slice(0, 4)),
    Array.from(values.slice(-4)),
    'strike must return to rest',
  );
  return new THREE.AnimationClip(animation.name, -1, [
    new THREE.QuaternionKeyframeTrack(name + '.quaternion', times, values),
  ]);
});
let latest;
const rig = new BellInteraction(
  model,
  clips,
  camera,
  scene,
  (s) => (latest = s),
);
const poses = rig.bells.map((b) => b.object.quaternion.clone());
rig.hit(19);
rig.update(0.2);
const contactFromFront = rig.ring.position.clone();
rig.stop();
camera.position.set(-8, 3, -12);
camera.lookAt(0, 1, 0);
rig.hit(19);
rig.update(0.2);
assert.ok(
  rig.ring.position.distanceTo(contactFromFront) < 1e-6,
  'contact stays on the same bell surface when the camera changes',
);
rig.stop();
rig.hits = 0;
assert.equal(
  rig.state().amplified,
  false,
  'reference demonstration is the default',
);
rig.hit(2);
rig.update(0.35);
assert.equal(latest.index, 2);
assert.equal(latest.hits, 1);
assert.ok(
  rig.bells[2].object.quaternion.angleTo(poses[2]) > 0.003,
  'selected bell moves',
);
const referenceAngle = rig.bells[2].object.quaternion.angleTo(poses[2]);
assert.ok(
  referenceAngle < THREE.MathUtils.degToRad(1),
  'reference view does not exaggerate gross swinging',
);
rig.bells.forEach((b, i) => {
  if (i !== 2)
    assert.ok(
      b.object.quaternion.angleTo(poses[i]) < 1e-7,
      'other bells stay at rest',
    );
});
rig.update(3.5);
assert.ok(rig.bells[2].object.quaternion.angleTo(poses[2]) < 1e-7);
rig.hit(2);
rig.hit(2);
rig.update(0.1);
rig.stop();
assert.ok(!rig.effects.visible);
assert.ok(!rig.playing);
rig.bells.forEach((b, i) =>
  assert.ok(b.object.quaternion.angleTo(poses[i]) < 1e-7),
);
rig.choose(2);
rig.setAmplified(true);
rig.update(0.35);
assert.ok(
  rig.bells[2].object.quaternion.angleTo(poses[2]) > referenceAngle * 10,
  'enlarged observation remains available separately',
);
rig.stop();
rig.setAmplified(false);
rig.stop();
rig.hit(52);
rig.update(1 / 6);
assert.equal(rig.state().tool, '长撞棒');
assert.ok(rig.longRod.visible && !rig.mallet.visible);
assert.ok(
  rig.longRod.position.distanceTo(rig.ring.position) < 1e-6,
  'rod tip reaches the documented bell surface at impact',
);
const frontPoint = rig.ring.position.clone();
rig.setZone('side');
rig.update(1 / 6);
assert.ok(
  rig.ring.position.distanceTo(frontPoint) > 0.005,
  'side drum point differs from front drum point',
);
assert.ok(rig.longRod.position.distanceTo(rig.ring.position) < 1e-6);
rig.stop();
rig.hit(19);
rig.update(1 / 6);
assert.equal(rig.state().tool, '短木槌');
assert.ok(rig.mallet.visible && !rig.longRod.visible);
assert.ok(
  rig.mallet.position.distanceTo(rig.ring.position) < 1e-6,
  'short mallet tip reaches the drum point',
);
rig.setZone('front');
rig.stop();
rig.choose(64);
rig.demo();
const first = rig.hits;
for (let i = 0; i < 4600; i++) rig.update(0.01);
assert.ok(
  rig.hits - first > 65,
  'simulation continues beyond the first 65 bells',
);
assert.equal(rig.playing, true);
assert.equal(
  rig.index,
  (64 + rig.hits - first) % 65,
  'continues in rack order after wrapping',
);
rig.stop();
rig.demo();
rig.update(0.8);
const stoppedHits = rig.hits;
rig.stop();
rig.update(3);
assert.equal(rig.hits, stoppedHits);
rig.reducedMotion = true;
rig.hit(0);
rig.update(0.2);
assert.equal(rig.effects.visible, false);
assert.ok(rig.bells[0].object.quaternion.angleTo(poses[0]) < 1e-7);
rig.dispose();
assert.equal(rig.effects.parent, null);
console.log(
  'PASS: fixed drum points, camera independence, short mallet/long rod contact, reference/enlarged modes, 65 shipped clips, isolated strike, rest/reset, continuous simulation, reduced motion and disposal.',
);
