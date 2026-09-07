import * as THREE from 'three';
import catalog from './artifact-experiences.json' with { type: 'json' };

export type Experience = {
  mode: 'explode' | 'strike' | 'inspect';
  title: string;
  action: string;
  note: string;
};
export const experiences = catalog as Record<string, Experience>;
export type ArtifactState = {
  index: number;
  count: number;
  label: string;
  detail: string;
  progress: number;
  playing: boolean;
  isolated: boolean;
  hits: number;
  detailIndex: number;
  detailNames: string[];
};
type Part = {
  object: THREE.Object3D;
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
  offset: THREE.Vector3;
  details: THREE.Object3D[];
};

/** Presentation transforms only. Static source meshes and photographed surfaces are retained. */
export class ArtifactInteraction {
  model: THREE.Group;
  config: Experience;
  camera: THREE.PerspectiveCamera;
  target: THREE.Vector3;
  notify: (s: ArtifactState) => void;
  parts: Part[] = [];
  mixer: THREE.AnimationMixer;
  clips: THREE.AnimationClip[];
  effects = new THREE.Group();
  guides: THREE.LineSegments;
  ring: THREE.Mesh<THREE.RingGeometry, THREE.MeshBasicMaterial>;
  index = 0;
  progress = 0;
  desiredProgress = 0;
  playing = false;
  isolated = false;
  hits = 0;
  detailIndex = -1;
  reducedMotion = false;
  private elapsed = 0;
  private next = 0;
  private impactAge = Infinity;
  private reportAge = 0;
  private meshes: THREE.Mesh[] = [];
  private currentView: 'all' | 'part' | 'detail' = 'all';
  private flight: {
    from: THREE.Vector3;
    to: THREE.Vector3;
    fromTarget: THREE.Vector3;
    toTarget: THREE.Vector3;
    age: number;
  } | null = null;

  constructor(
    model: THREE.Group,
    clips: THREE.AnimationClip[],
    id: string,
    camera: THREE.PerspectiveCamera,
    target: THREE.Vector3,
    notify: (s: ArtifactState) => void,
  ) {
    this.model = model;
    this.clips = clips;
    this.config = experiences[id];
    this.camera = camera;
    this.target = target;
    this.notify = notify;
    this.mixer = new THREE.AnimationMixer(model);
    const nodes: THREE.Object3D[] = [];
    model.traverse((o) => {
      if (Number.isInteger(o.userData.experience_part)) nodes.push(o);
      if (o instanceof THREE.Mesh && !o.userData.experience_tool_mesh)
        this.meshes.push(o);
    });
    nodes.sort(
      (a, b) => a.userData.experience_part - b.userData.experience_part,
    );
    if (!nodes.length) throw new Error(`No interaction parts in ${id}`);
    for (const object of nodes) {
      const details: THREE.Object3D[] = [];
      object.traverse((o) => {
        if (o.userData.experience_detail) details.push(o);
      });
      this.parts.push({
        object,
        position: object.position.clone(),
        quaternion: object.quaternion.clone(),
        offset: new THREE.Vector3().fromArray(
          object.userData.explode_offset || [0, 0, 0],
        ),
        details,
      });
    }
    this.guides = new THREE.LineSegments(
      new THREE.BufferGeometry().setAttribute(
        'position',
        new THREE.BufferAttribute(new Float32Array(this.parts.length * 6), 3),
      ),
      new THREE.LineDashedMaterial({
        color: 0x8eaaa9,
        transparent: true,
        opacity: 0.45,
        dashSize: 0.018,
        gapSize: 0.012,
        depthWrite: false,
      }),
    );
    this.guides.frustumCulled = false;
    this.ring = new THREE.Mesh(
      new THREE.RingGeometry(0.46, 0.5, 48),
      new THREE.MeshBasicMaterial({
        color: 0xe9c88d,
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    this.ring.visible = false;
    this.effects.add(this.guides, this.ring);
    // A sibling avoids modifying model bounds and keeps guide vertices in world coordinates.
    model.parent?.add(this.effects);
    this.apply();
  }

  state(): ArtifactState {
    const d = this.parts[this.index].object.userData;
    const detail = this.parts[this.index].details[this.detailIndex]?.userData;
    return {
      index: this.index,
      count: this.parts.length,
      label: d.label,
      detail: detail ? `${detail.label} · ${detail.detail}` : d.detail,
      progress: this.progress,
      playing: this.playing,
      isolated: this.isolated,
      hits: this.hits,
      detailIndex: this.detailIndex,
      detailNames: this.parts[this.index].details.map(
        (o) => o.userData.label as string,
      ),
    };
  }
  private emit() {
    this.notify(this.state());
  }
  partAt(object: THREE.Object3D, point?: THREE.Vector3) {
    for (
      let o: THREE.Object3D | null = object;
      o && o !== this.model;
      o = o.parent
    ) {
      const found = this.parts.findIndex((p) => p.object === o);
      if (found >= 0) return found;
    }
    if (this.config.mode !== 'inspect' || !point) return -1;
    let nearest = 0,
      distance = Infinity;
    this.parts.forEach((p, i) => {
      const d = p.object
        .getWorldPosition(new THREE.Vector3())
        .distanceToSquared(point);
      if (d < distance) {
        nearest = i;
        distance = d;
      }
    });
    return nearest;
  }
  choose(index: number) {
    this.playing = false;
    this.flight = null;
    this.index = (index + this.parts.length) % this.parts.length;
    this.detailIndex = -1;
    this.apply();
    if (this.config.mode === 'inspect') this.focusPart();
    this.emit();
  }
  activate(index = this.index) {
    this.choose(index);
    if (this.config.mode === 'strike') this.hit();
  }
  private apply() {
    const positions = this.guides.geometry.getAttribute('position');
    this.parts.forEach((p, i) => {
      if (this.config.mode === 'explode')
        p.object.position
          .copy(p.position)
          .addScaledVector(p.offset, this.progress);
      if (this.config.mode !== 'inspect')
        p.object.visible = !this.isolated || i === this.index;
      const current = p.object.getWorldPosition(new THREE.Vector3());
      const origin = p.object.parent!.localToWorld(p.position.clone());
      positions.setXYZ(i * 2, ...origin.toArray());
      positions.setXYZ(i * 2 + 1, ...current.toArray());
    });
    // Unassigned rack/environment meshes also disappear when a component is isolated.
    for (const mesh of this.meshes) {
      if (this.config.mode !== 'inspect')
        mesh.visible = !this.isolated || this.partAt(mesh) === this.index;
    }
    positions.needsUpdate = true;
    this.guides.computeLineDistances();
    this.guides.visible =
      this.config.mode === 'explode' && this.progress > 0.01 && !this.isolated;
    this.model.updateMatrixWorld(true);
  }
  setProgress(value: number) {
    this.playing = false;
    this.progress = this.desiredProgress = THREE.MathUtils.clamp(value, 0, 1);
    this.apply();
    this.emit();
  }
  toggleExpand() {
    this.playing = false;
    this.desiredProgress = this.desiredProgress > 0.5 ? 0 : 1;
    if (this.reducedMotion) this.progress = this.desiredProgress;
    this.apply();
    this.fitAll(true);
    this.emit();
  }
  isolate() {
    this.isolated = !this.isolated;
    this.apply();
    this.emit();
  }
  hit() {
    this.mixer.stopAllAction();
    this.impactAge = 0;
    this.hits++;
    const part = this.parts[this.index],
      number = String(this.index + 1).padStart(2, '0');
    this.parts.forEach((p) => p.object.quaternion.copy(p.quaternion));
    if (!this.reducedMotion)
      for (const name of [`Strike_${number}`, `ToolStrike_${number}`]) {
        const clip = this.clips.find((c) => c.name === name);
        if (clip)
          this.mixer.clipAction(clip).reset().setLoop(THREE.LoopOnce, 1).play();
      }
    const point = new THREE.Vector3().fromArray(
      part.object.userData.strike_point,
    );
    point.applyQuaternion(part.quaternion).add(part.position);
    part.object.parent!.localToWorld(point);
    const normal = new THREE.Vector3()
      .fromArray(part.object.userData.strike_normal)
      .applyQuaternion(part.quaternion)
      .transformDirection(part.object.parent!.matrixWorld);
    this.ring.position.copy(point).addScaledVector(normal, 0.0005);
    this.ring.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
    this.ring.scale.setScalar(part.object.userData.tool_length * 0.6);
    this.ring.visible = this.reducedMotion;
    this.emit();
  }
  demo() {
    this.stop();
    if (this.reducedMotion) {
      if (this.config.mode === 'explode') this.setProgress(1);
      else if (this.config.mode === 'inspect') this.focusPart();
      else this.hit();
      return;
    }
    this.playing = true;
    this.elapsed = 0;
    this.next = this.config.mode === 'inspect' ? 3.6 : 0.9;
    if (this.config.mode === 'explode') {
      this.isolated = false;
      this.fitAll(true);
    } else if (this.config.mode === 'inspect') this.focusPart();
    else this.hit();
    this.emit();
  }
  stop() {
    this.playing = false;
    this.flight = null;
    this.desiredProgress = this.progress;
    this.mixer.stopAllAction();
    this.parts.forEach((p) => p.object.quaternion.copy(p.quaternion));
    this.impactAge = Infinity;
    this.ring.visible = false;
    this.emit();
  }
  reset() {
    this.stop();
    this.isolated = false;
    this.progress = this.desiredProgress = 0;
    this.index = 0;
    this.detailIndex = -1;
    this.apply();
    this.fitAll();
    this.emit();
  }
  /** Called when the user starts orbiting, so camera tours never fight pointer input. */
  cancelTour() {
    if (this.flight || (this.config.mode === 'inspect' && this.playing))
      this.stop();
  }

  bounds(expanded = false): THREE.Box3 {
    this.model.updateMatrixWorld(true);
    const box = new THREE.Box3();
    for (const mesh of this.meshes) {
      const b = new THREE.Box3().setFromObject(mesh);
      if (expanded && this.config.mode === 'explode') {
        const i = this.partAt(mesh);
        if (i >= 0) {
          const p = this.parts[i];
          const displacement = p.offset
            .clone()
            .multiplyScalar(1 - this.progress)
            .applyQuaternion(
              p.object.parent!.getWorldQuaternion(new THREE.Quaternion()),
            );
          box.union(b.clone().translate(displacement));
        }
      }
      box.union(b);
    }
    return box;
  }
  private fly(box: THREE.Box3, direction: THREE.Vector3) {
    const center = box.getCenter(new THREE.Vector3()),
      size = box.getSize(new THREE.Vector3());
    direction.normalize();
    const right = new THREE.Vector3()
      .crossVectors(this.camera.up, direction)
      .normalize();
    const up = new THREE.Vector3().crossVectors(direction, right).normalize();
    const tangent = Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2));
    let distance = 0;
    for (const x of [-1, 1])
      for (const y of [-1, 1])
        for (const z of [-1, 1]) {
          const c = size
            .clone()
            .multiply(new THREE.Vector3(x, y, z))
            .multiplyScalar(0.5);
          distance = Math.max(
            distance,
            c.dot(direction) +
              Math.max(
                Math.abs(c.dot(up)) / tangent,
                Math.abs(c.dot(right)) / (tangent * this.camera.aspect),
              ),
          );
        }
    const to = center.clone().addScaledVector(direction, distance * 1.18);
    if (this.reducedMotion) {
      this.camera.position.copy(to);
      this.target.copy(center);
      return;
    }
    this.flight = {
      from: this.camera.position.clone(),
      to,
      fromTarget: this.target.clone(),
      toTarget: center,
      age: 0,
    };
  }
  focusPart() {
    this.currentView = 'part';
    this.detailIndex = -1;
    const object = this.parts[this.index].object;
    if (this.config.mode === 'inspect') {
      const span = object.userData.view_span;
      this.fly(
        new THREE.Box3().setFromCenterAndSize(
          object.getWorldPosition(new THREE.Vector3()),
          new THREE.Vector3(span, span, span * 0.02),
        ),
        new THREE.Vector3().fromArray(object.userData.view_direction),
      );
    } else
      this.fly(
        new THREE.Box3().setFromObject(object),
        new THREE.Vector3().fromArray(
          object.userData.view_direction || [0.22, 0.28, 1],
        ),
      );
    this.emit();
  }
  fitAll(expanded = false) {
    this.currentView = 'all';
    this.fly(
      this.bounds(expanded),
      new THREE.Vector3(0.16, this.config.mode === 'explode' ? 0.3 : 0.15, 1),
    );
  }
  focusDetail(index: number) {
    const details = this.parts[this.index].details;
    if (!details.length) return;
    this.playing = false;
    this.desiredProgress = this.progress;
    this.detailIndex = (index + details.length) % details.length;
    this.currentView = 'detail';
    const anchor = details[this.detailIndex],
      span = anchor.userData.view_span;
    this.fly(
      new THREE.Box3().setFromCenterAndSize(
        anchor.getWorldPosition(new THREE.Vector3()),
        new THREE.Vector3(span, span, span * 0.15),
      ),
      new THREE.Vector3().fromArray(anchor.userData.view_direction),
    );
    this.emit();
  }
  reframe() {
    if (this.currentView === 'detail') this.focusDetail(this.detailIndex);
    else if (this.currentView === 'part') this.focusPart();
    else this.fitAll(this.progress > 0);
  }
  /** World anchors for DOM labels. Selection feedback never recolors the artifact. */
  annotations() {
    return this.parts.flatMap((p, index) => {
      if (
        (this.config.mode !== 'explode' || this.isolated) &&
        index !== this.index
      )
        return [];
      const anchor =
        index === this.index && this.detailIndex >= 0
          ? p.details[this.detailIndex]
          : p.object;
      return [
        {
          index,
          label: anchor.userData.label as string,
          point: anchor.getWorldPosition(new THREE.Vector3()),
          selected: index === this.index,
        },
      ];
    });
  }
  update(delta: number) {
    this.mixer.update(delta);
    this.impactAge += delta;
    this.elapsed += delta;
    if (this.flight) {
      const f = this.flight;
      f.age += delta;
      const t = Math.min(1, f.age / 0.7),
        ease = t * t * (3 - 2 * t);
      this.camera.position.lerpVectors(f.from, f.to, ease);
      this.target.lerpVectors(f.fromTarget, f.toTarget, ease);
      if (t === 1) this.flight = null;
    }
    if (this.config.mode === 'explode') {
      const previous = this.progress;
      if (this.playing) {
        const phase = this.elapsed % 6;
        const t =
          phase < 2
            ? phase / 2
            : phase < 3
              ? 1
              : phase < 5
                ? (5 - phase) / 2
                : 0;
        this.progress = t * t * (3 - 2 * t);
        this.desiredProgress = this.progress;
      } else
        this.progress = this.reducedMotion
          ? this.desiredProgress
          : THREE.MathUtils.damp(this.progress, this.desiredProgress, 8, delta);
      if (Math.abs(this.progress - this.desiredProgress) < 0.0001)
        this.progress = this.desiredProgress;
      if (previous !== this.progress) {
        this.apply();
        this.reportAge += delta;
        if (this.reportAge > 0.1) {
          this.reportAge = 0;
          this.emit();
        }
      }
    } else if (this.playing && this.elapsed >= this.next) {
      this.index = (this.index + 1) % this.parts.length;
      this.next = this.elapsed + (this.config.mode === 'inspect' ? 3.6 : 0.9);
      if (this.config.mode === 'strike') this.hit();
      else {
        this.focusPart();
        this.emit();
      }
    }
    if (this.config.mode === 'strike') {
      this.ring.visible = this.reducedMotion
        ? this.impactAge < 0.8
        : this.impactAge >= 0.2 && this.impactAge < 0.8;
      this.ring.material.opacity =
        Math.max(0, (0.8 - this.impactAge) / 0.6) * 0.7;
    }
  }
  dispose() {
    this.stop();
    this.mixer.uncacheRoot(this.model);
    this.effects.removeFromParent();
    this.guides.geometry.dispose();
    (this.guides.material as THREE.Material).dispose();
    this.ring.geometry.dispose();
    this.ring.material.dispose();
  }
}
