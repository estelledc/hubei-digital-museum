# 开发与公开发布分工

本仓用于公开展示与 GitHub Pages。日常开发、完整 Blender 工程、研究素材及未验收试制在独立私有仓库中维护；本地开发目录为相邻的 `hubei-digital-museum`，本目录 `hubei-digital-museum-public` 只承接公开里程碑。

2026-09-08，开发中的鸳鸯盒和交互修改迁入私有项目。原始改动在私有迁移清单中保留，不以公开提交或上线冒充质量验收。这里的 [PLAN.md](PLAN.md) 保存已经确认的路线与验收约定；后续从私有项目的 PLAN 继续。

## 里程碑发布顺序

1. 在私有仓库完成开发、测试与该版本视觉验收，冻结来源提交和本次公开清单。
2. 核对本仓的 origin 与干净状态。私有仓库的 `scripts/sync_public_code.py` 可预览并按指定提交／文件复制网页源码；默认不写入，加 `--apply` 才应用。它不复制模型、目录说明、私有历史或研究资料，也不执行 commit／push。
3. 单独合并文物注册和交互说明，确保它们描述的是实际公开资产。审阅新图像与字体许可，使用本仓现有公开模型／Blender 导出脚本制作可再分发副本；不能仅凭旧替换表认定新增素材已经过审。
4. 在 `web/` 执行相关测试、`npm run typecheck` 与 `MUSEUM_BASE_PATH=/hubei-digital-museum npm run build`，根目录执行 `python3 scripts/stage_pages.py`，再检查实际公开候选网页。
5. 按该里程碑授权逐文件提交、推送，确认 GitHub Pages 部署和线上资源；Blender 文件按既有 Release 方式交付。记录本次来源与公开版本的对应关系。

不要把 private 分支整体 merge、push 或 mirror 到这里；不要用整目录复制替代公开清单。未到里程碑的工作继续留在私有仓库。
