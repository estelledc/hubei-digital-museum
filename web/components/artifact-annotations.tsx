import type { RefObject } from 'react';
import type {
  ArtifactInteraction,
  ArtifactState,
} from '@/lib/artifact-interaction';

export function ArtifactAnnotations({
  layerRef,
  state,
  controller,
}: {
  layerRef: RefObject<HTMLDivElement | null>;
  state: ArtifactState;
  controller: () => ArtifactInteraction | null;
}) {
  const annotations = controller()?.annotations() || [];
  return (
    <div
      className="artifact-annotations"
      ref={layerRef}
      aria-label="模型部件标签"
    >
      <svg aria-hidden="true">
        {annotations.map((a) => (
          <line key={a.index} data-leader={a.index} />
        ))}
      </svg>
      {annotations.map((a) => (
        <button
          key={a.index}
          data-anchor={a.index}
          aria-pressed={state.index === a.index}
          onClick={() => {
            const c = controller();
            if (c?.index !== a.index) c?.choose(a.index);
            if (c?.detailIndex === -1) c?.focusPart();
            else if (c) c.focusDetail(c.detailIndex);
          }}
        >
          <span>{String(a.index + 1).padStart(2, '0')}</span>
          {a.label}
        </button>
      ))}
    </div>
  );
}

// DOM positions follow camera/part transforms without rerendering React at 60 fps.
// Separate left/right columns keep the small set of part labels from overlapping.
export function placeArtifactAnnotations(
  layer: HTMLDivElement,
  controller: ArtifactInteraction,
) {
  const width = layer.clientWidth,
    height = layer.clientHeight;
  const labels = controller
    .annotations()
    .map((a) => ({ ...a, ndc: a.point.clone().project(controller.camera) }));
  for (const side of [-1, 1]) {
    let bottom = 8;
    for (const a of labels
      .filter((a) => (a.ndc.x < 0 ? -1 : 1) === side)
      .sort((a, b) => b.ndc.y - a.ndc.y)) {
      const button = layer.querySelector<HTMLButtonElement>(
        `[data-anchor="${a.index}"]`,
      );
      const line = layer.querySelector<SVGLineElement>(
        `[data-leader="${a.index}"]`,
      );
      if (!button || !line) continue;
      const visible =
        a.ndc.z > -1 &&
        a.ndc.z < 1 &&
        Math.abs(a.ndc.x) < 1.15 &&
        Math.abs(a.ndc.y) < 1.15;
      const y = Math.max(
        bottom,
        Math.min(
          height - button.offsetHeight - 8,
          ((1 - a.ndc.y) / 2) * height - button.offsetHeight / 2,
        ),
      );
      const show = visible && y + button.offsetHeight <= height - 4;
      button.style.visibility = show ? 'visible' : 'hidden';
      line.style.visibility = show ? 'visible' : 'hidden';
      if (!show) continue;
      const x = side < 0 ? 8 : width - button.offsetWidth - 8;
      button.style.transform = `translate(${x}px, ${y}px)`;
      line.setAttribute('x1', String(((a.ndc.x + 1) / 2) * width));
      line.setAttribute('y1', String(((1 - a.ndc.y) / 2) * height));
      line.setAttribute('x2', String(side < 0 ? x + button.offsetWidth : x));
      line.setAttribute('y2', String(y + button.offsetHeight / 2));
      line.classList.toggle('is-selected', a.selected);
      bottom = y + button.offsetHeight + 6;
    }
  }
}
