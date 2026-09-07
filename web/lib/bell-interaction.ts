import * as THREE from 'three';
import performance from './bell-performance.json' with { type: 'json' };

export type BellState = {
  count: number;
  index: number;
  tier: string;
  playing: boolean;
  hits: number;
  zone: 'front' | 'side';
  amplified: boolean;
  tool: '短木槌' | '长撞棒';
};
type Bell = {
  object: THREE.Object3D;
  action: THREE.AnimationAction;
  rotation: THREE.Quaternion;
  materials: {
    material: THREE.MeshStandardMaterial;
    color: THREE.Color;
    intensity: number;
  }[];
};

/** Interactive demonstration, without claiming measured vibration or original bell sounds. */
export class BellInteraction {
  readonly bells: Bell[] = [];
  readonly mixer: THREE.AnimationMixer;
  readonly effects = new THREE.Group();
  readonly ring: THREE.Mesh<THREE.RingGeometry, THREE.MeshBasicMaterial>;
  readonly mallet = new THREE.Group();
  readonly longRod = new THREE.Group();
  zone: 'front' | 'side' = 'front';
  amplified = false;
  index = 0;
  hits = 0;
  playing = false;
  reducedMotion = false;
  private age = Infinity;
  private next = 0;
  private effectSize = 1;
  private point = new THREE.Vector3();
  private direction = new THREE.Vector3();
  private basis = new THREE.Quaternion();
  private notify: (state: BellState) => void;

  constructor(
    model: THREE.Object3D,
    clips: THREE.AnimationClip[],
    _camera: THREE.Camera,
    scene: THREE.Scene,
    notify: (state: BellState) => void,
  ) {
    this.notify = notify;
    this.mixer = new THREE.AnimationMixer(model);
    const objects: THREE.Object3D[] = [];
    model.traverse((o) => {
      if (/^Bell_\d+$/.test(o.name) && o.userData.bell_id) objects.push(o);
    });
    objects.sort((a, b) => a.userData.bell_id - b.userData.bell_id);
    for (const object of objects) {
      for (const key of [
        'strike_front',
        'strike_side',
        'normal_front',
        'normal_side',
      ])
        if (
          !Array.isArray(object.userData[key]) ||
          object.userData[key].length !== 3
        )
          throw new Error(
            `Missing documented strike point: ${object.name}/${key}`,
          );
      const clip = clips.find(
        (c) =>
          c.name ===
          `Strike_${String(object.userData.bell_id).padStart(2, '0')}`,
      );
      if (!clip) throw new Error(`Missing strike animation for ${object.name}`);
      const materials: Bell['materials'] = [];
      object.traverse((o) => {
        if (!(o instanceof THREE.Mesh)) return;
        const cloned = (
          Array.isArray(o.material) ? o.material : [o.material]
        ).map((m) => m.clone());
        o.material = cloned.length === 1 ? cloned[0] : cloned;
        for (const material of cloned)
          if (material instanceof THREE.MeshStandardMaterial)
            materials.push({
              material,
              color: material.emissive.clone(),
              intensity: material.emissiveIntensity,
            });
      });
      const action = this.mixer.clipAction(clip).setLoop(THREE.LoopOnce, 1);
      action.clampWhenFinished = false;
      this.bells.push({
        object,
        action,
        materials,
        rotation: object.quaternion.clone(),
      });
    }
    if (!this.bells.length)
      throw new Error('No independently animated bells in model');
    this.ring = new THREE.Mesh(
      new THREE.RingGeometry(0.47, 0.5, 48),
      new THREE.MeshBasicMaterial({
        color: 0xd6b77a,
        transparent: true,
        opacity: 0,
        depthWrite: false,
        side: THREE.DoubleSide,
      }),
    );
    this.effects.add(this.ring, this.mallet, this.longRod);
    const wood = new THREE.MeshStandardMaterial({
      color: 0x704523,
      roughness: 0.85,
    });
    const p = performance.mallet;
    const head = new THREE.Mesh(
      new THREE.CylinderGeometry(p.headRadius, p.headRadius, p.headLength, 20),
      wood,
    );
    head.rotation.x = Math.PI / 2;
    head.position.z = p.headLength / 2;
    const handle = new THREE.Mesh(
      new THREE.CylinderGeometry(
        p.handleRadius,
        p.handleRadius,
        p.handleLength,
        16,
      ),
      wood,
    );
    handle.position.set(0, -p.handleLength / 2, p.headLength / 2);
    this.mallet.add(head, handle);
    const rod = new THREE.Mesh(
      new THREE.CylinderGeometry(
        performance.rod.radius,
        performance.rod.radius,
        performance.rod.length,
        24,
      ),
      wood,
    );
    rod.rotation.x = Math.PI / 2;
    rod.position.z = performance.rod.length / 2;
    this.longRod.add(rod);
    this.effects.visible = false;
    scene.add(this.effects);
    this.paint();
  }
  state(): BellState {
    return {
      count: this.bells.length,
      index: this.index,
      tier: this.bells[this.index].object.userData.bell_tier,
      playing: this.playing,
      hits: this.hits,
      zone: this.zone,
      amplified: this.amplified,
      tool:
        this.bells[this.index].object.userData.bell_tier === '下层'
          ? '长撞棒'
          : '短木槌',
    };
  }
  private emit() {
    this.notify(this.state());
  }
  private paint() {
    this.bells.forEach((bell, i) =>
      bell.materials.forEach(({ material, color, intensity }) => {
        material.emissive.copy(color);
        material.emissiveIntensity = intensity;
        if (i === this.index) {
          material.emissive.set(0xd3a751);
          material.emissiveIntensity = 0.06 + 0.38 * Math.exp(-this.age * 4);
        }
      }),
    );
  }
  choose(index: number) {
    this.playing = false;
    this.index = (index + this.bells.length) % this.bells.length;
    this.age = Infinity;
    this.effects.visible = false;
    this.paint();
    this.emit();
  }
  hit(index = this.index) {
    this.playing = false;
    this.strike(index);
  }
  setZone(zone: 'front' | 'side') {
    this.stop(false);
    this.zone = zone;
    this.strike(this.index);
  }
  setAmplified(amplified: boolean) {
    const playing = this.playing;
    this.stop(false);
    this.amplified = amplified;
    if (playing) this.demo();
    else this.strike(this.index);
  }
  private strike(index: number) {
    this.index = index;
    this.hits++;
    this.age = 0;
    const bell = this.bells[index];
    if (!this.reducedMotion)
      bell.action
        .stop()
        .reset()
        .setEffectiveWeight(this.amplified ? 1 : performance.referenceWeight)
        .play();
    const bounds = new THREE.Box3().setFromObject(bell.object);
    const size = bounds.getSize(new THREE.Vector3());
    // The generated drum-area anchor is in the bell's rest coordinates, independent of the viewer.
    this.point
      .fromArray(bell.object.userData[`strike_${this.zone}`])
      .applyQuaternion(bell.rotation)
      .add(bell.object.position);
    bell.object.parent!.localToWorld(this.point);
    this.direction
      .fromArray(bell.object.userData[`normal_${this.zone}`])
      .applyQuaternion(bell.rotation);
    this.direction
      .applyQuaternion(
        bell.object.parent!.getWorldQuaternion(new THREE.Quaternion()),
      )
      .normalize();
    const right = new THREE.Vector3()
      .crossVectors(new THREE.Vector3(0, 1, 0), this.direction)
      .normalize();
    const up = new THREE.Vector3()
      .crossVectors(this.direction, right)
      .normalize();
    this.basis.setFromRotationMatrix(
      new THREE.Matrix4().makeBasis(right, up, this.direction),
    );
    this.effectSize = Math.max(size.x, size.y, size.z);
    this.ring.position.copy(this.point);
    this.ring.quaternion.copy(this.basis);
    this.paint();
    this.emit();
  }
  demo() {
    this.stop(false);
    this.playing = true;
    this.next = 0.65;
    this.strike(this.index);
  }
  stop(emit = true) {
    this.playing = false;
    this.age = Infinity;
    this.mixer.stopAllAction();
    this.bells.forEach((b) => b.object.quaternion.copy(b.rotation));
    this.effects.visible = false;
    this.paint();
    if (emit) this.emit();
  }
  update(delta: number) {
    this.mixer.update(delta);
    this.age += delta;
    if (this.playing) {
      this.next -= delta;
      if (this.next <= 0) {
        this.strike((this.index + 1) % this.bells.length);
        this.next = 0.65;
      }
    }
    this.effects.visible = this.age < 0.85 && !this.reducedMotion;
    if (this.effects.visible) {
      const t = this.age,
        impact = t - performance.contactSeconds;
      this.ring.visible = impact >= 0;
      this.ring.scale.setScalar(
        this.effectSize *
          (this.amplified ? 0.16 + Math.max(0, impact) * 0.7 : 0.14),
      );
      this.ring.material.opacity = Math.max(0, 0.7 * (1 - impact / 0.65));
      const retreat =
        t < performance.contactSeconds
          ? 1 - t / performance.contactSeconds
          : Math.min(
              1,
              impact /
                (performance.recoverSeconds - performance.contactSeconds),
            );
      const isRod = this.bells[this.index].object.userData.bell_tier === '下层';
      this.mallet.visible = !isRod && t < performance.recoverSeconds;
      this.longRod.visible = isRod && t < performance.recoverSeconds;
      const tool = isRod ? this.longRod : this.mallet;
      tool.quaternion.copy(this.basis);
      tool.position
        .copy(this.point)
        .addScaledVector(this.direction, retreat * (isRod ? 0.3 : 0.24));
      if (!isRod) tool.position.y += 0.07 * Math.sin((retreat * Math.PI) / 2);
    }
    if (this.age < 2) this.paint();
  }
  bellAt(object: THREE.Object3D): number {
    for (let p: THREE.Object3D | null = object; p; p = p.parent) {
      if (/^Bell_\d+$/.test(p.name))
        return this.bells.findIndex((b) => b.object === p);
    }
    return -1;
  }
  bounds() {
    return new THREE.Box3().setFromObject(this.bells[this.index].object);
  }
  viewDirection() {
    const bell = this.bells[this.index];
    return new THREE.Vector3()
      .fromArray(bell.object.userData[`normal_${this.zone}`])
      .applyQuaternion(bell.rotation)
      .applyQuaternion(
        bell.object.parent!.getWorldQuaternion(new THREE.Quaternion()),
      )
      .normalize();
  }
  dispose() {
    this.stop(false);
    this.mixer.uncacheRoot(this.mixer.getRoot());
    this.effects.removeFromParent();
    const materials = new Set<THREE.Material>();
    this.effects.traverse((o) => {
      if (o instanceof THREE.Mesh) {
        o.geometry.dispose();
        for (const m of Array.isArray(o.material) ? o.material : [o.material])
          materials.add(m);
      }
    });
    materials.forEach((m) => m.dispose());
  }
}
