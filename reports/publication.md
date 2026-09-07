# 公开发布验证 · 0.13

2026-09-07。用户授权发布公开 GitHub 仓库并使用 GitHub Pages。

- 发布目录独立于本地研究版；未修改本地原始归档或主工程。
- 32 个实际交付 GLB 以 gzip 无损压缩，资源约 321 MB；没有抽稀几何或删除动画。
- 馆方与 VR 的 18 类未授权参考图像，从公开模型替换为近似色材质。开放纹理保留 CC BY-SA 4.0 署名。
- `npm test`：实际空间、65 个编钟片段和另外 15 组交互通过；新增 HTTP 子路径下载、gzip 解压和缺失模型错误回调通过。
- `npm run typecheck`：通过。修改的前端文件定向 oxlint 检查通过。
- `MUSEUM_BASE_PATH=/hubei-digital-museum npm run build`：Vite 静态构建通过。Three.js 场景包超过 500 kB 的提示不影响构建。
- `python3 scripts/stage_pages.py`：首页存在，子路径引用可定位，静态制品低于 1 GB。
- 首次尝试 vinext 静态导出时首页被标记为 dynamic 而跳过；未发布该空导出。公开版改为 Vite 静态入口，复用原 React 页面与全部交互。

没有执行浏览器 DOM、GPU、移动端视觉验收或实景精度认证。WebMCP 沿用可选的导航接口，未在支持该实验 API 的浏览器验证。

## Blender 下载工件

`prepare_blender_release.py` 输出全馆工程及 16 个文物交互工程。`verify_blender_release.py` 实际重开全部 17 个文件，通过对象、打包图像、受限照片和嵌入字体检查；全馆保留 14,404 个对象。编钟工程含 65 个 Strike 动作和 65 个工具演示动作，网页 GLB 为 65 个组合片段。

发布前解压扫描全部 Blender 文件，未发现本机用户目录或临时目录路径。系统字体已转成标签几何，移除了字体二进制；附加素材与图像的路径统一改为相对路径。
