# 湖北数字博物馆：公开发布仓库

本仓 `estelledc/hubei-digital-museum` 保持 PUBLIC，负责已验收里程碑和 GitHub Pages。日常开发在相邻的 `hubei-digital-museum` 私有项目进行；不要在本仓继续实验性建模或积累未验收交互。

- 先读 `DEVELOPMENT.md`；后续实施以私有开发仓库的 PLAN 为准，本仓 PLAN 保存已公开的阶段约定。
- 开始写入前检查工作树；保留既有修改，只按明确里程碑清单导入已接受内容。
- 不接受私有分支整体 merge、mirror push、私有 `.git`、LFS 设置、研究原图或迁移归档。模型必须来自经过许可与材质检查的公开候选。
- `web/lib/museum.ts` 和 `web/lib/artifact-experiences.json` 的公开说明单独维护，不能用保留研究照片的私有版说明直接覆盖。
- 公开版本须运行相关模型测试、类型检查、子路径构建、素材检查及当前候选的实际网页／视觉验收；程序通过不替代用户接受。
- 逐文件提交与推送，沿当前 GitHub Pages 工作流交付并核对结果；不强推，不覆盖用户工作，不重新发布未验收试制。
