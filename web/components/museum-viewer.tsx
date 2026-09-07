'use client';
import { loadPublicModel } from '@/lib/model-loader';
import { assetUrl } from '@/lib/asset-url';
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { spaces, setSpaceCutaway, publicViews } from '@/lib/museum';
import { Button } from '@/components/ui/button';
import {
  ChevronLeft,
  ChevronRight,
  Play,
  Square,
  Focus,
  MousePointer2,
} from 'lucide-react';
import { BellInteraction, type BellState } from '@/lib/bell-interaction';
import {
  ArtifactInteraction,
  experiences,
  type ArtifactState,
} from '@/lib/artifact-interaction';
import { ArtifactControls } from '@/components/artifact-controls';
import {
  ArtifactAnnotations,
  placeArtifactAnnotations,
} from '@/components/artifact-annotations';
type Runtime = {
  scene: THREE.Scene;
  bells: BellInteraction | null;
  artifact: ArtifactInteraction | null;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  model: THREE.Group | null;
  radius: number;
  publicFov: number | null;
  size: THREE.Vector3;
  renderer: THREE.WebGLRenderer;
  key: THREE.DirectionalLight;
  fill: THREE.DirectionalLight;
  hemi: THREE.HemisphereLight;
};
type Props = {
  mode: 'spaces' | 'artifacts';
  selected: string;
  reset: number;
  rotate: boolean;
  cutaway: boolean;
  onStatus: (s: string) => void;
};
function dispose(g: THREE.Group) {
  g.traverse((o) => {
    if (o instanceof THREE.Mesh) {
      o.geometry.dispose();
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        for (const v of Object.values(m))
          if (v instanceof THREE.Texture) v.dispose();
        m.dispose();
      }
    }
  });
}
function publicViewFov(fov: number, aspect: number) {
  return Math.min(
    85,
    THREE.MathUtils.radToDeg(
      2 *
        Math.atan(
          Math.tan(THREE.MathUtils.degToRad(fov / 2)) *
            Math.max(1, 1.5 / aspect),
        ),
    ),
  );
}
function focus(rt: Runtime, mode: string, id: string) {
  const interior = mode === 'spaces' && id !== 'campus';
  const publicView = mode === 'spaces' ? publicViews[id]?.[0] : undefined;
  rt.publicFov = publicView?.fov ?? null;
  // Meter-scale architecture needs more depth precision than the tiny artifact viewer.
  rt.camera.near =
    mode === 'artifacts'
      ? Math.max(0.0001, rt.radius * 0.0001)
      : id === 'campus'
        ? 0.5
        : 0.05;
  rt.camera.far = mode === 'artifacts' ? Math.max(2, rt.radius * 40) : 2000;
  rt.camera.fov = interior
    ? Math.min(
        85,
        THREE.MathUtils.radToDeg(
          2 *
            Math.atan(
              Math.tan(THREE.MathUtils.degToRad(43 / 2)) *
                Math.max(1, 1.4 / rt.camera.aspect),
            ),
        ),
      )
    : 43;
  if (publicView)
    rt.camera.fov = publicViewFov(publicView.fov, rt.camera.aspect);
  rt.camera.updateProjectionMatrix();
  if (mode === 'artifacts') {
    const r = rt.radius;
    const direction = new THREE.Vector3(
      id === 'zun' ? 0.32 : 0.08,
      id === 'zun' ? 0.42 : id === 'bells' || id === 'chimes' ? 0.2 : 0.06,
      1,
    ).normalize();
    const right = new THREE.Vector3()
      .crossVectors(rt.camera.up, direction)
      .normalize();
    const up = new THREE.Vector3().crossVectors(direction, right).normalize();
    const tangent = Math.tan(THREE.MathUtils.degToRad(rt.camera.fov / 2));
    let distance = 0;
    for (const x of [-1, 1])
      for (const y of [-1, 1])
        for (const z of [-1, 1]) {
          const corner = rt.size
            .clone()
            .multiply(new THREE.Vector3(x, y, z))
            .multiplyScalar(0.5);
          distance = Math.max(
            distance,
            corner.dot(direction) +
              Math.max(
                Math.abs(corner.dot(up)) / tangent,
                Math.abs(corner.dot(right)) / (tangent * rt.camera.aspect),
              ),
          );
        }
    rt.controls.target.set(0, 0, 0);
    rt.camera.position.copy(direction.multiplyScalar(distance * 1.12));
    rt.controls.minDistance = rt.artifact
      ? Math.max(0.0002, r * 0.001)
      : r * 0.25;
    rt.controls.maxDistance = distance * 5;
    rt.controls.update();
    return;
  }
  const sp = spaces.find((s) => s.id === id) || spaces[0];
  rt.controls.minDistance = 0.1;
  rt.controls.maxDistance = id === 'campus' ? 550 : 80;
  rt.controls.target.fromArray(sp.target);
  rt.camera.position.fromArray(sp.camera);
  rt.controls.update();
}
export default function MuseumViewer({
  mode,
  selected,
  reset,
  rotate,
  cutaway,
  onStatus,
}: Props) {
  const host = useRef<HTMLDivElement>(null),
    runtime = useRef<Runtime | null>(null);
  const [loaded, setLoaded] = useState(0);
  const [bellState, setBellState] = useState<BellState | null>(null);
  const [artifactState, setArtifactState] = useState<ArtifactState | null>(
    null,
  );
  const interactionPanel = useRef<HTMLElement>(null);
  const annotationLayer = useRef<HTMLDivElement>(null);
  const interactive = mode === 'artifacts' && selected === 'bells';
  const experience = mode === 'artifacts' ? experiences[selected] : undefined;
  const selection = useRef({ mode, selected });
  useEffect(() => {
    selection.current = { mode, selected };
  }, [mode, selected]);
  const src = interactive
    ? '/models/interactive/bells-interactive.glb?v=bell07'
    : mode === 'spaces'
      ? `/models/${(spaces.find((s) => s.id === selected) || spaces[0]).model}.glb?v=public12-final`
      : `/models/interactive/${selected}-interactive.glb?v=artifact10`;
  useEffect(() => {
    if (!host.current) return;
    const el = host.current;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      onStatus('当前浏览器未启用 WebGL，可打开下方渲染图。');
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.AgXToneMapping;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.toneMappingExposure = 1;
    el.appendChild(renderer.domElement);
    renderer.domElement.tabIndex = 0;
    renderer.domElement.setAttribute(
      'aria-label',
      '三维视图：拖动旋转、滚轮缩放、方向键平移',
    );
    const scene = new THREE.Scene(),
      pmrem = new THREE.PMREMGenerator(renderer),
      room = new RoomEnvironment(),
      env = pmrem.fromScene(room, 0.04);
    scene.environment = env.texture;
    room.dispose();
    pmrem.dispose();
    const hemi = new THREE.HemisphereLight(0xffffff, 0x858583, 0.8);
    scene.add(hemi);
    const key = new THREE.DirectionalLight(0xffffff, 3);
    key.position.set(50, 100, 75);
    scene.add(key);
    scene.add(key.target);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.bias = -0.0001;
    const fill = new THREE.DirectionalLight(0xffffff, 0.5);
    fill.position.set(-70, 20, -25);
    scene.add(fill);
    const camera = new THREE.PerspectiveCamera(
      43,
      el.clientWidth / el.clientHeight,
      0.005,
      2000,
    );
    camera.position.set(180, 165, 245);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.target.set(0, 10, -35);
    controls.maxPolarAngle = Math.PI * 0.93;
    runtime.current = {
      scene,
      bells: null,
      artifact: null,
      camera,
      controls,
      model: null,
      radius: 1,
      publicFov: null,
      size: new THREE.Vector3(1, 1, 1),
      renderer,
      key,
      fill,
      hemi,
    };
    const observer = new ResizeObserver(() => {
      camera.aspect = el.clientWidth / el.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(el.clientWidth, el.clientHeight);
      if (runtime.current?.artifact) runtime.current.artifact.reframe();
      else if (runtime.current?.model && runtime.current.publicFov !== null) {
        camera.fov = publicViewFov(runtime.current.publicFov, camera.aspect);
        camera.updateProjectionMatrix();
      } else if (runtime.current?.model)
        focus(
          runtime.current,
          selection.current.mode,
          selection.current.selected,
        );
    });
    observer.observe(el);
    const move = (e: KeyboardEvent) => {
      if (
        (e.key === 'Enter' || e.code === 'Space') &&
        e.target === renderer.domElement &&
        (runtime.current?.bells || runtime.current?.artifact)
      ) {
        e.preventDefault();
        if (!e.repeat) {
          const rt = runtime.current;
          if (rt?.bells) rt.bells.hit();
          else if (rt?.artifact?.config.mode === 'explode')
            rt.artifact.toggleExpand();
          else rt?.artifact?.activate();
        }
        return;
      }
      if (e.key === 'Escape') {
        runtime.current?.bells?.stop();
        runtime.current?.artifact?.stop();
      }
      if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key))
        return;
      e.preventDefault();
      const direction = new THREE.Vector3();
      camera.getWorldDirection(direction);
      direction.y = 0;
      direction.normalize();
      const right = new THREE.Vector3()
          .crossVectors(direction, camera.up)
          .normalize(),
        step = camera.position.distanceTo(controls.target) * 0.035;
      const v = (
        e.key === 'ArrowUp'
          ? direction
          : e.key === 'ArrowDown'
            ? direction.negate()
            : e.key === 'ArrowRight'
              ? right
              : right.negate()
      ).multiplyScalar(step);
      camera.position.add(v);
      controls.target.add(v);
    };
    el.addEventListener('keydown', move);
    const raycaster = new THREE.Raycaster();
    const pointers = new Set<number>();
    let press: { id: number; x: number; y: number; moved: boolean } | null =
      null;
    const down = (e: PointerEvent) => {
      pointers.add(e.pointerId);
      if (pointers.size === 1 && e.button === 0)
        press = { id: e.pointerId, x: e.clientX, y: e.clientY, moved: false };
      else press = null;
    };
    const pointerMove = (e: PointerEvent) => {
      if (press && Math.hypot(e.clientX - press.x, e.clientY - press.y) > 6)
        press.moved = true;
    };
    const up = (e: PointerEvent) => {
      const tap = press;
      pointers.delete(e.pointerId);
      press = null;
      const rt = runtime.current;
      if (
        !tap ||
        tap.id !== e.pointerId ||
        tap.moved ||
        Math.hypot(e.clientX - tap.x, e.clientY - tap.y) > 6 ||
        (!rt?.bells && !rt?.artifact)
      )
        return;
      const rect = renderer.domElement.getBoundingClientRect();
      raycaster.setFromCamera(
        new THREE.Vector2(
          ((e.clientX - rect.left) / rect.width) * 2 - 1,
          1 - ((e.clientY - rect.top) / rect.height) * 2,
        ),
        camera,
      );
      const hit = rt.model
        ? raycaster.intersectObject(rt.model, true)[0]
        : undefined;
      if (hit) {
        if (rt.bells) {
          const index = rt.bells.bellAt(hit.object);
          if (index >= 0) rt.bells.hit(index);
        } else if (rt.artifact) {
          const index = rt.artifact.partAt(hit.object, hit.point);
          if (index >= 0) rt.artifact.activate(index);
        }
      }
    };
    const cancel = (e: PointerEvent) => {
      pointers.delete(e.pointerId);
      press = null;
    };
    const visibility = () => {
      if (document.hidden) {
        runtime.current?.bells?.stop();
        runtime.current?.artifact?.stop();
      }
    };
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const motionChange = () => {
      const bells = runtime.current?.bells;
      if (bells) {
        bells.stop();
        bells.reducedMotion = motion.matches;
      }
      const artifact = runtime.current?.artifact;
      if (artifact) {
        artifact.stop();
        artifact.reducedMotion = motion.matches;
      }
    };
    const orbitStart = () => runtime.current?.artifact?.cancelTour();
    controls.addEventListener('start', orbitStart);
    renderer.domElement.addEventListener('pointerdown', down);
    renderer.domElement.addEventListener('pointermove', pointerMove);
    renderer.domElement.addEventListener('pointerup', up);
    renderer.domElement.addEventListener('pointercancel', cancel);
    document.addEventListener('visibilitychange', visibility);
    motion.addEventListener('change', motionChange);
    let frame = 0,
      previous = 0;
    const animate = (now = performance.now()) => {
      frame = requestAnimationFrame(animate);
      const delta = previous ? Math.min((now - previous) / 1000, 0.1) : 0;
      previous = now;
      runtime.current?.bells?.update(delta);
      runtime.current?.artifact?.update(delta);
      controls.update();
      if (annotationLayer.current && runtime.current?.artifact) {
        if (annotationLayer.current.style.bottom !== el.style.bottom)
          annotationLayer.current.style.bottom = el.style.bottom;
        placeArtifactAnnotations(
          annotationLayer.current,
          runtime.current.artifact,
        );
      }
      renderer.render(scene, camera);
    };
    animate();
    return () => {
      cancelAnimationFrame(frame);
      renderer.domElement.removeEventListener('pointerdown', down);
      renderer.domElement.removeEventListener('pointermove', pointerMove);
      renderer.domElement.removeEventListener('pointerup', up);
      renderer.domElement.removeEventListener('pointercancel', cancel);
      document.removeEventListener('visibilitychange', visibility);
      motion.removeEventListener('change', motionChange);
      runtime.current?.bells?.dispose();
      runtime.current?.artifact?.dispose();
      observer.disconnect();
      el.removeEventListener('keydown', move);
      controls.removeEventListener('start', orbitStart);
      controls.dispose();
      env.dispose();
      if (runtime.current?.model) dispose(runtime.current.model);
      renderer.dispose();
      renderer.domElement.remove();
      runtime.current = null;
    };
  }, [onStatus]);
  useEffect(() => {
    const rt = runtime.current;
    if (!rt) return;
    let cancelled = false;
    const request = new AbortController();
    let model: THREE.Group | null = null;
    let bellController: BellInteraction | null = null;
    let artifactController: ArtifactInteraction | null = null;
    setBellState(null);
    setArtifactState(null);
    onStatus('正在载入三维模型…');
    void loadPublicModel(
      assetUrl(src),
      (gltf) => {
        model = gltf.scene;
        if (cancelled) {
          dispose(model);
          return;
        }
        model.traverse((o) => {
          if (o instanceof THREE.SpotLight || o instanceof THREE.PointLight) {
            // Saved space lights carry the same calibrated preview values as the export report.
            if (typeof o.userData.web_intensity === 'number')
              o.intensity = o.userData.web_intensity;
            else o.intensity *= o.name.includes('展品照明') ? 0.008 : 0.03;
            o.castShadow = Boolean(o.userData.web_shadow);
            o.shadow.mapSize.set(1024, 1024);
            o.shadow.bias = -0.0001;
          }
          if (o instanceof THREE.Mesh) {
            const materials = Array.isArray(o.material)
              ? o.material
              : [o.material];
            o.castShadow = !materials.some(
              (m) =>
                m instanceof THREE.MeshPhysicalMaterial && m.transmission > 0,
            );
            o.receiveShadow = true;
            for (const m of materials) {
              for (const value of Object.values(m))
                if (value instanceof THREE.Texture)
                  value.anisotropy = Math.min(
                    8,
                    rt.renderer.capabilities.getMaxAnisotropy(),
                  );
            }
          }
        });
        rt.model = model;
        rt.scene.add(model);
        if (
          !src.includes('/galleries/') &&
          !src.includes('/public/') &&
          !src.includes('museum-architecture')
        ) {
          const bounds = new THREE.Box3().setFromObject(model),
            center = bounds.getCenter(new THREE.Vector3()),
            size = bounds.getSize(new THREE.Vector3());
          model.position.sub(center);
          rt.radius = Math.max(size.x, size.y, size.z) * 0.72;
          rt.size.copy(size);
        }
        if (src.includes('/interactive/bells-interactive')) {
          bellController = new BellInteraction(
            model,
            gltf.animations,
            rt.camera,
            rt.scene,
            setBellState,
          );
          bellController.reducedMotion = window.matchMedia(
            '(prefers-reduced-motion: reduce)',
          ).matches;
          rt.bells = bellController;
          setBellState(bellController.state());
        } else if (src.includes('/interactive/')) {
          const id = src.split('/').pop()!.split('-interactive.glb')[0];
          artifactController = new ArtifactInteraction(
            model,
            gltf.animations,
            id,
            rt.camera,
            rt.controls.target,
            setArtifactState,
          );
          artifactController.reducedMotion = window.matchMedia(
            '(prefers-reduced-motion: reduce)',
          ).matches;
          rt.artifact = artifactController;
          rt.controls.minDistance = Math.max(0.0002, rt.radius * 0.001);
          setArtifactState(artifactController.state());
        }
        setLoaded((v) => v + 1);
        onStatus('');
      },
      (e) => {
        if (!cancelled)
          onStatus(
            e.total
              ? e.loaded === e.total
                ? '模型已下载，正在准备细节…'
                : `正在载入模型 ${Math.round((e.loaded / e.total) * 100)}%`
              : '正在载入三维模型…',
          );
      },
      (error) => {
        console.error('Museum model load failed:', src, error);
        if (!cancelled)
          onStatus('模型载入失败，请刷新重试，或前往 GitHub 下载工程。');
      },
      request.signal,
    );
    return () => {
      request.abort();
      cancelled = true;
      bellController?.dispose();
      artifactController?.dispose();
      if (rt.bells === bellController) rt.bells = null;
      if (rt.artifact === artifactController) rt.artifact = null;
      if (model) {
        rt.scene.remove(model);
        dispose(model);
      }
      rt.model = null;
    };
  }, [src, onStatus]);
  useEffect(() => {
    const rt = runtime.current;
    if (!rt) return;
    const studio = mode === 'artifacts',
      outside = mode === 'spaces' && ['campus', 'terrace'].includes(selected),
      daylight = ['arrival', 'atrium', 'connection'].includes(selected),
      theatre = selected === 'theatre';
    rt.scene.background = new THREE.Color(
      studio ? 0x191d20 : outside ? 0xc7dbe5 : daylight ? 0xd6dcd9 : 0x202823,
    );
    rt.scene.environmentIntensity = studio
      ? 0.65
      : outside
        ? 0.42
        : daylight
          ? 0.45
          : 0.22;
    rt.renderer.toneMappingExposure = studio
      ? 1
      : outside
        ? 0.92
        : daylight
          ? 0.9
          : 1;
    rt.hemi.intensity = studio
      ? 0.35
      : outside
        ? 0.72
        : daylight
          ? 0.65
          : theatre
            ? 0.18
            : 0.32;
    rt.hemi.color.set(0xffffff);
    rt.hemi.groundColor.set(outside ? 0x687862 : 0x8a8883);
    rt.key.intensity = studio ? 2.5 : outside ? 2.8 : daylight ? 1.25 : 0.25;
    rt.key.castShadow = studio || outside || daylight;
    rt.fill.intensity = studio ? 0.7 : outside ? 0.38 : daylight ? 0.35 : 0.18;
    const r = studio ? rt.radius : outside ? 150 : daylight ? 35 : 12;
    rt.key.position.set(r * 1.1, r * 1.8, r * 1.3);
    rt.fill.position.set(-r * 1.5, r * 0.3, r * 0.8);
    rt.key.target.position.set(0, 0, outside ? -30 : 0);
    const c = rt.key.shadow.camera;
    c.left = -r * 1.3;
    c.right = r * 1.3;
    c.top = r * 1.3;
    c.bottom = -r * 1.3;
    c.near = Math.max(0.01, r * 0.01);
    c.far = r * 6;
    c.updateProjectionMatrix();
    rt.key.shadow.normalBias = studio ? r * 0.001 : outside ? 0.1 : 0.03;
    rt.key.shadow.bias = -0.0001;
  }, [mode, selected, loaded]);
  useEffect(() => {
    const rt = runtime.current;
    if (rt) focus(rt, mode, selected);
  }, [mode, selected, reset, loaded]);
  useEffect(() => {
    const bells = runtime.current?.bells;
    if (bells && !bells.reducedMotion && !document.hidden) bells.demo();
  }, [loaded]);
  useEffect(() => {
    const panel = interactionPanel.current,
      canvas = host.current;
    if (!panel || !canvas) return;
    const observer = new ResizeObserver(() => {
      canvas.style.bottom = `${panel.offsetHeight + parseFloat(getComputedStyle(panel).bottom) + 14}px`;
      if (annotationLayer.current)
        annotationLayer.current.style.bottom = canvas.style.bottom;
    });
    observer.observe(panel);
    return () => {
      observer.disconnect();
      canvas.style.bottom = '';
    };
  }, [selected, mode]);
  useEffect(() => {
    const rt = runtime.current;
    if (!rt?.model || mode !== 'spaces') return;
    setSpaceCutaway(rt.model, cutaway);
  }, [mode, selected, cutaway, loaded]);
  useEffect(() => {
    if (runtime.current) runtime.current.controls.autoRotate = rotate;
  }, [rotate]);
  const focusBell = () => {
    const rt = runtime.current;
    if (!rt?.bells) return;
    const bounds = rt.bells.bounds(),
      center = bounds.getCenter(new THREE.Vector3()),
      size = bounds.getSize(new THREE.Vector3());
    const direction = rt.bells
      .viewDirection()
      .add(new THREE.Vector3(0, 0.2, 0))
      .normalize();
    const distance =
      Math.max(size.x, size.y, size.z) /
      (Math.tan(THREE.MathUtils.degToRad(rt.camera.fov / 2)) *
        Math.min(1, rt.camera.aspect));
    rt.controls.target.copy(center);
    rt.camera.position.copy(center).addScaledVector(direction, distance * 1.25);
    rt.controls.minDistance = 0.03;
    rt.controls.update();
  };
  return (
    <>
      <div ref={host} className="scene-canvas" />
      {mode === 'spaces' && publicViews[selected] && (
        <nav className="public-views" aria-label="空间观察位置">
          {publicViews[selected].map((view) => (
            <Button
              key={view.label}
              variant="outline"
              disabled={loaded === 0}
              onClick={() => {
                const rt = runtime.current;
                if (!rt?.model) return;
                rt.publicFov = view.fov;
                rt.camera.fov = publicViewFov(view.fov, rt.camera.aspect);
                rt.camera.updateProjectionMatrix();
                rt.camera.position.fromArray(view.camera);
                rt.controls.target.fromArray(view.target);
                rt.controls.update();
              }}
            >
              {view.label}
            </Button>
          ))}
        </nav>
      )}
      {experience && artifactState && (
        <ArtifactAnnotations
          layerRef={annotationLayer}
          state={artifactState}
          controller={() => runtime.current?.artifact || null}
        />
      )}
      {experience && (
        <ArtifactControls
          panelRef={interactionPanel}
          experience={experience}
          state={artifactState}
          controller={() => runtime.current?.artifact || null}
        />
      )}
      {interactive && (
        <section className="bell-interaction" aria-label="编钟互动控制">
          <div className="bell-selection">
            <div>
              <MousePointer2 size={15} />
              <strong>编钟演奏示范</strong>
            </div>
            <div className="bell-picker">
              <Button
                variant="ghost"
                size="icon"
                aria-label="上一枚钟"
                disabled={!bellState}
                onClick={() =>
                  runtime.current?.bells?.choose((bellState?.index || 0) - 1)
                }
              >
                <ChevronLeft />
              </Button>
              <span>
                {bellState
                  ? `${bellState.tier} · 第 ${String(bellState.index + 1).padStart(2, '0')} 枚 / ${bellState.count}`
                  : '准备钟体…'}
              </span>
              <Button
                variant="ghost"
                size="icon"
                aria-label="下一枚钟"
                disabled={!bellState}
                onClick={() =>
                  runtime.current?.bells?.choose((bellState?.index || 0) + 1)
                }
              >
                <ChevronRight />
              </Button>
            </div>
            <Button variant="ghost" disabled={!bellState} onClick={focusBell}>
              <Focus />
              近看此钟
            </Button>
          </div>
          <div className="bell-technique">
            <Button
              variant="outline"
              disabled={!bellState}
              aria-pressed={bellState?.amplified || false}
              onClick={() =>
                runtime.current?.bells?.setAmplified(!bellState?.amplified)
              }
            >
              {bellState?.amplified ? '放大观察' : '演奏参考'}
            </Button>
            <Button
              variant="outline"
              disabled={!bellState}
              onClick={() =>
                runtime.current?.bells?.setZone(
                  bellState?.zone === 'side' ? 'front' : 'side',
                )
              }
            >
              {bellState?.zone === 'side' ? '侧鼓示意' : '正鼓示意'} · 切换
            </Button>
            <span>{bellState?.tool || '准备工具'} · 进击 / 接触 / 回收</span>
          </div>
          <div className="bell-actions">
            <Button
              disabled={!bellState}
              onClick={() => runtime.current?.bells?.hit()}
            >
              敲击一次
            </Button>
            <Button
              variant="outline"
              disabled={!bellState}
              onClick={() => {
                if (bellState?.playing) runtime.current?.bells?.stop();
                else runtime.current?.bells?.demo();
              }}
            >
              {bellState?.playing ? <Square /> : <Play />}
              {bellState?.playing ? '停止模拟' : '播放模拟'}
            </Button>
            <Button
              variant="outline"
              disabled={!bellState}
              onClick={() => {
                runtime.current?.bells?.stop();
                if (runtime.current) focus(runtime.current, mode, selected);
              }}
            >
              停止并复位
            </Button>
            <output aria-live={bellState?.playing ? 'off' : 'polite'}>
              {bellState?.playing
                ? '正在循环演示'
                : bellState?.hits
                  ? `已敲击 ${bellState.hits} 次`
                  : '点击任一钟体'}
            </output>
          </div>
          <p>
            {bellState?.amplified
              ? '钟体摆幅已放大。'
              : '按现场方式示范短槌与长棒。'}
            击点与回振为近似，无声音；逐枚展示技法，不对应曲谱。 参考：
            <a
              href="https://www.bilibili.com/video/BV1H3NZzfEBa/"
              target="_blank"
              rel="noreferrer"
            >
              2025 现场
            </a>{' '}
            ·{' '}
            <a
              href="https://www.bilibili.com/video/BV1bJ4m1K7xE/"
              target="_blank"
              rel="noreferrer"
            >
              2024 现场
            </a>{' '}
            ·{' '}
            <a
              href="https://www.hbww.org.cn/zgzb/p/4695.html"
              target="_blank"
              rel="noreferrer"
            >
              馆方说明
            </a>
          </p>
        </section>
      )}
    </>
  );
}
