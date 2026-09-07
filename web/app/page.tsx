'use client';
import { assetUrl } from '@/lib/asset-url';
import { useState, useCallback, useEffect } from 'react';
import { lazy, Suspense } from 'react';
import {
  ArrowUpRight,
  RotateCcw,
  Rotate3D,
  Scan,
  Layers,
  Compass,
  Landmark,
  Info,
  X,
  ChevronRight,
  Box,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Sidebar, SidebarProvider } from '@/components/ui/sidebar';
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { flushSync } from 'react-dom';
import { artifacts, spaces, sources } from '@/lib/museum';
import experienceCatalog from '@/lib/artifact-experiences.json';
const interactionKind = (id: string) => {
  if (id === 'bells') return '击奏示范';
  const entry = (experienceCatalog as Record<string, { mode: string }>)[id];
  return entry?.mode === 'explode'
    ? '结构展开'
    : entry?.mode === 'strike'
      ? '击奏示范'
      : '细节导览';
};
const Viewer = lazy(() => import('@/components/museum-viewer'));
export default function Home() {
  const [mode, setMode] = useState<'spaces' | 'artifacts'>('spaces'),
    [selected, setSelected] = useState('campus'),
    [reset, setReset] = useState(0),
    [rotate, setRotate] = useState(false),
    [cutaway, setCutaway] = useState(false),
    [showSources, setShowSources] = useState(false),
    [status, setStatus] = useState('正在准备三维视图…');
  const updateStatus = useCallback((s: string) => setStatus(s), []);
  useEffect(() => {
    const ctx = (
      document as Document & {
        modelContext?: {
          registerTool: (
            tool: unknown,
            options: { signal: AbortSignal },
          ) => void | Promise<void>;
        };
      }
    ).modelContext;
    if (!ctx?.registerTool) return;
    const lifecycle = new AbortController();
    const tool = {
      name: 'navigate_museum',
      title: '打开博物馆空间或文物',
      description: '切换可见三维导览，返回该项的来源和精度说明。',
      inputSchema: {
        type: 'object',
        properties: {
          kind: { enum: ['spaces', 'artifacts'] },
          id: { type: 'string' },
        },
        required: ['kind', 'id'],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input: unknown) {
        if (!input || typeof input !== 'object')
          throw new Error('需要 kind 和 id');
        const { kind, id } = input as { kind: string; id: string };
        if (kind !== 'spaces' && kind !== 'artifacts')
          throw new Error('kind 无效');
        const item = (kind === 'spaces' ? spaces : artifacts).find(
          (x) => x.id === id,
        );
        if (!item) throw new Error('未找到该空间或文物');
        flushSync(() => {
          setMode(kind);
          setSelected(id);
          setRotate(false);
        });
        return {
          status: 'navigation_updated',
          id,
          title: item.title,
          description: item.description,
          modelLoad: 'asynchronous',
        };
      },
    };
    try {
      void Promise.resolve(
        ctx.registerTool(tool, { signal: lifecycle.signal }),
      ).catch(() => {});
    } catch {
      /* Optional browser API; ordinary navigation remains available. */
    }
    return () => lifecycle.abort();
  }, []);
  const item =
    mode === 'artifacts'
      ? artifacts.find((a) => a.id === selected) || artifacts[0]
      : spaces.find((s) => s.id === selected) || spaces[0];
  const artifact =
    mode === 'artifacts' ? artifacts.find((a) => a.id === selected) : null;
  return (
    <main className="museum-app">
      <header className="app-header">
        <a className="brand" href={assetUrl('/')} aria-label="返回园区全景">
          <Landmark size={27} />
          <span>
            湖北省博物馆<small>DIGITAL COLLECTION · 数字重建</small>
          </span>
        </a>
        <div className="edition">
          <span className="status-dot" />
          非官方 · 公开展示版
        </div>
        <Button variant="ghost" onClick={() => setShowSources(!showSources)}>
          <Info />
          资料与边界
        </Button>
      </header>
      <SidebarProvider className="workspace">
        <Sidebar collapsible="none" className="catalog">
          <nav className="contents" aria-label="数字馆藏与空间目录">
            <div className="catalog-heading">
              <span>探索荆楚</span>
              <span>01 / 馆藏与空间</span>
            </div>
            <Tabs
              value={mode}
              onValueChange={(v) => {
                const m = v as 'spaces' | 'artifacts';
                setMode(m);
                setSelected(m === 'spaces' ? 'campus' : 'bells');
                setRotate(false);
              }}
            >
              <TabsList className="mode-tabs">
                <TabsTrigger value="spaces">
                  <Compass />
                  空间导览
                </TabsTrigger>
                <TabsTrigger value="artifacts">
                  <Box />
                  文物细看
                </TabsTrigger>
              </TabsList>
            </Tabs>
            <div className="catalog-items">
              {(mode === 'spaces' ? spaces : artifacts).map((s, i) => (
                <Button
                  key={s.id}
                  variant="ghost"
                  className={
                    'catalog-item ' + (selected === s.id ? 'is-selected' : '')
                  }
                  onClick={() => {
                    setSelected(s.id);
                    setRotate(false);
                  }}
                >
                  <span className="catalog-number">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span>
                    <strong>{s.title}</strong>
                    <small>
                      {s.floor}
                      {mode === 'artifacts'
                        ? ` · ${interactionKind(s.id)}`
                        : ''}
                    </small>
                  </span>
                  {selected === s.id && <ChevronRight size={16} />}
                </Button>
              ))}
            </div>
            <div className="catalog-footer">
              <span className="seal">楚</span>
              <p>
                让器物回到空间
                <br />
                <span>公开展示版 0.13 · 2026.09</span>
              </p>
            </div>
          </nav>
        </Sidebar>
        <section
          className="viewport"
          data-mode={mode}
          data-artifact={mode === 'artifacts' ? selected : undefined}
          aria-label={item.title + '三维展示'}
        >
          <Suspense fallback={null}>
            <Viewer
              mode={mode}
              selected={selected}
              reset={reset}
              rotate={rotate}
              cutaway={cutaway}
              onStatus={updateStatus}
            />
          </Suspense>
          <div className="view-caption">
            <p>
              {mode === 'spaces' ? 'ARCHITECTURE / 空间' : 'COLLECTION / 器物'}
            </p>
            <h1>{item.title}</h1>
            <span>{item.floor}</span>
          </div>
          <div className="view-tools">
            <Button
              variant="outline"
              size="icon-lg"
              title="复位视角"
              aria-label="复位视角"
              onClick={() => setReset((n) => n + 1)}
            >
              <RotateCcw />
            </Button>
            <Button
              variant="outline"
              size="icon-lg"
              title="自动旋转"
              aria-label="自动旋转"
              aria-pressed={rotate}
              onClick={() => setRotate(!rotate)}
            >
              <Rotate3D />
            </Button>
            {mode === 'spaces' && (
              <Button
                variant="outline"
                size="icon-lg"
                title="隐藏屋顶与南馆外壳"
                aria-label="隐藏屋顶与南馆外壳"
                aria-pressed={cutaway}
                onClick={() => setCutaway(!cutaway)}
              >
                <Layers />
              </Button>
            )}
            <Button
              variant="outline"
              size="icon-lg"
              title="全屏"
              aria-label="全屏"
              onClick={() => {
                if (document.fullscreenElement) void document.exitFullscreen();
                else
                  void document.querySelector('.viewport')?.requestFullscreen();
              }}
            >
              <Scan />
            </Button>
          </div>
          {status && (
            <output className="load-state" aria-live="polite">
              {status}
              <a
                href={
                  ['campus', 'arrival', 'atrium', 'connection'].includes(
                    selected,
                  ) && mode === 'spaces'
                    ? assetUrl(`/renders/public-12/${selected}.jpg`)
                    : assetUrl('/renders/public-12/campus.jpg')
                }
                target="_blank"
                rel="noreferrer"
              >
                查看 Blender 渲染图 <ArrowUpRight size={14} />
              </a>
            </output>
          )}
          <div className="object-note">
            <details key={mode} open={mode === 'spaces'}>
              <summary>
                <span className="accuracy-label">
                  {artifact?.provenance || '建筑近似重建'}
                </span>
                {artifact && (
                  <span className="note-toggle">文物资料与还原依据</span>
                )}
              </summary>
              <p>{item.description}</p>
              <small>
                非官方近似重建。公开版未收录未授权照片；部分文物纹饰以近似材质展示。
              </small>
              {artifact && (
                <strong className="dimensions">{artifact.dimension}</strong>
              )}
              {artifact?.limit && <small>{artifact.limit}</small>}
              <a
                href={
                  artifact?.url ||
                  spaces.find((s) => s.id === selected)?.url ||
                  sources[0].url
                }
                target="_blank"
                rel="noreferrer"
              >
                查看依据 <ArrowUpRight size={14} />
              </a>
              {mode === 'spaces' &&
                (spaces.find((s) => s.id === selected)?.artifacts || []).map(
                  (id) => (
                    <Button
                      key={id}
                      variant="outline"
                      onClick={() => {
                        setMode('artifacts');
                        setSelected(id);
                        setRotate(false);
                      }}
                    >
                      {id === 'bells'
                        ? '互动敲钟'
                        : `细看${artifacts.find((a) => a.id === id)?.title}`}
                      <ChevronRight />
                    </Button>
                  ),
                )}
              {mode === 'artifacts' && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setMode('spaces');
                    setSelected(
                      spaces.find((s) => s.artifacts.includes(selected))?.id ||
                        'campus',
                    );
                    setRotate(false);
                  }}
                >
                  返回所属展厅 <ChevronRight />
                </Button>
              )}
            </details>
          </div>
          <div className="view-footer">
            <span>拖动旋转 · 滚轮缩放 · 聚焦后方向键平移</span>
            <span>3D / 可编辑 Blender 来源</span>
          </div>
          <div className="north-marker" aria-hidden="true">
            <span>N</span>
            <i />
          </div>
        </section>
      </SidebarProvider>
      <Sheet open={showSources} onOpenChange={setShowSources}>
        <SheetContent showCloseButton={false} className="sources-panel">
          <div className="sources-title">
            <SheetTitle>每一处重建，都有边界。</SheetTitle>
            <Button
              variant="ghost"
              size="icon"
              aria-label="关闭资料"
              onClick={() => setShowSources(false)}
            >
              <X />
            </Button>
          </div>
          <SheetDescription>
            这是依据公开资料制作的数字研究版，不是馆方发布的测绘模型。原存档、公开资料和近似补建分别保留来源。
          </SheetDescription>
          <ul>
            {sources.map((s) => (
              <li key={s.url}>
                <a href={assetUrl(s.url)} target="_blank" rel="noreferrer">
                  {s.title}
                  <ArrowUpRight size={15} />
                </a>
                <small>{s.note}</small>
              </li>
            ))}
          </ul>
          <p className="sources-limits">
            11 个常设展区均建立独立场景，共含 16
            组代表文物与展陈模型，另有入口、中庭、连接廊、演奏厅和观景平台。
            建筑与陈列坐标未测绘；部分器物仅有浅浮雕轮廓，背面和厚度近似。未授权照片已从公开版移除，不包含全部在展藏品。
          </p>
          <a
            href={assetUrl('/research/README.md')}
            target="_blank"
            rel="noreferrer"
          >
            打开资源与缺口说明 <ArrowUpRight size={14} />
          </a>
          <p>
            <a
              href="https://github.com/estelledc/hubei-digital-museum"
              target="_blank"
              rel="noreferrer"
            >
              GitHub 项目
            </a>{' '}
            ·{' '}
            <a
              href="https://github.com/estelledc/hubei-digital-museum/releases/latest"
              target="_blank"
              rel="noreferrer"
            >
              下载 Blender 工程
            </a>
          </p>
        </SheetContent>
      </Sheet>
    </main>
  );
}
