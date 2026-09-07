import type { RefObject } from 'react';
import { ChevronLeft, ChevronRight, Play, Square, Focus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type {
  ArtifactInteraction,
  ArtifactState,
  Experience,
} from '@/lib/artifact-interaction';

export function ArtifactControls({
  panelRef,
  experience,
  state,
  controller,
}: {
  panelRef: RefObject<HTMLElement | null>;
  experience: Experience;
  state: ArtifactState | null;
  controller: () => ArtifactInteraction | null;
}) {
  return (
    <section
      ref={panelRef}
      className="artifact-interaction"
      aria-label={experience.title}
    >
      <div className="artifact-selection">
        <strong>{experience.title}</strong>
        <div className="artifact-picker">
          <Button
            variant="ghost"
            size="icon"
            aria-label="上一处"
            disabled={!state}
            onClick={() => controller()?.choose((state?.index || 0) - 1)}
          >
            <ChevronLeft />
          </Button>
          <select
            aria-label="选择部件或观察位置"
            disabled={!state}
            value={state?.index || 0}
            onChange={(e) => controller()?.choose(Number(e.target.value))}
          >
            {state ? (
              controller()?.parts.map((part, index) => (
                <option key={index} value={index}>
                  {String(index + 1).padStart(2, '0')} ·{' '}
                  {part.object.userData.label}
                </option>
              ))
            ) : (
              <option>准备交互模型…</option>
            )}
          </select>
          <Button
            variant="ghost"
            size="icon"
            aria-label="下一处"
            disabled={!state}
            onClick={() => controller()?.choose((state?.index || 0) + 1)}
          >
            <ChevronRight />
          </Button>
        </div>
        <Button
          variant="ghost"
          disabled={!state}
          onClick={() => controller()?.focusPart()}
        >
          <Focus />
          近看此处
        </Button>
      </div>
      <div className="artifact-actions">
        <Button
          disabled={!state}
          onClick={() => {
            const control = controller();
            if (experience.mode === 'explode') control?.toggleExpand();
            else if (experience.mode === 'strike') control?.activate();
            else control?.choose((state?.index || 0) + 1);
          }}
        >
          {experience.mode === 'explode' && (state?.progress || 0) > 0.5
            ? '合拢结构'
            : experience.mode === 'inspect'
              ? '下一处细节'
              : experience.action}
        </Button>
        {experience.mode === 'explode' && (
          <label className="explode-slider">
            展开
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              aria-label="结构展开程度"
              disabled={!state}
              value={Math.round((state?.progress || 0) * 100)}
              onPointerDown={() => controller()?.fitAll(true)}
              onKeyDown={() => controller()?.fitAll(true)}
              onChange={(e) =>
                controller()?.setProgress(Number(e.target.value) / 100)
              }
            />
            <output>{Math.round((state?.progress || 0) * 100)}%</output>
          </label>
        )}
        <Button
          variant="outline"
          disabled={!state}
          onClick={() => {
            if (state?.playing) controller()?.stop();
            else controller()?.demo();
          }}
        >
          {state?.playing ? <Square /> : <Play />}
          {state?.playing ? '停止展示' : '循环展示'}
        </Button>
        {experience.mode === 'explode' && (
          <Button
            variant="outline"
            disabled={!state}
            aria-pressed={state?.isolated || false}
            onClick={() => controller()?.isolate()}
          >
            {state?.isolated ? '显示全部' : '单独查看'}
          </Button>
        )}
        <Button
          variant="outline"
          disabled={!state}
          onClick={() => controller()?.reset()}
        >
          全部复位
        </Button>
      </div>
      {!!state?.detailNames.length && (
        <div className="artifact-detail-picker">
          <label>
            局部特写
            <select
              aria-label="选择局部特写"
              value={state.detailIndex}
              onChange={(e) => {
                if (Number(e.target.value) < 0) controller()?.focusPart();
                else controller()?.focusDetail(Number(e.target.value));
              }}
            >
              <option value={-1}>当前部件全貌</option>
              {state.detailNames.map((name, index) => (
                <option key={index} value={index}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <Button
            variant="ghost"
            onClick={() => controller()?.focusDetail(state.detailIndex + 1)}
          >
            <Focus />
            下一处特写
          </Button>
        </div>
      )}
      <p
        className="artifact-detail"
        aria-live={state?.playing ? 'off' : 'polite'}
      >
        {state?.detail || '载入后可选择部件与观察位置。'}
        {experience.mode === 'strike' && state
          ? ` 已敲击 ${state.hits} 次。`
          : ''}
      </p>
      <p>{experience.note}</p>
    </section>
  );
}
