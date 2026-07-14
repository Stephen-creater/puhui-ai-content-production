# Pre-taped Masking Film 基准项目

这是参考成片驱动的产品短视频基准项目。v2 是单条质量基线；Phase 2 已在同一参考片上稳定产出 5 条受控变体。每条 35.8 秒、1080×1920、Alex 英文旁白，分别采用清洁成本、施工效率、产品结构、专业推荐和前后对比钩子。

## 阅读顺序

1. `00_input`：客户参考视频与产品结构图。
2. `01_analysis`：参考片抽帧、技术信息、转写与镜头功能拆解。
3. `02_plan`：产品事实、模板 DNA、母版脚本与生产规划。
4. `03_generation`：关键帧、分镜视频、生成清单与真人 CTA 生成工程。
5. `04_postproduction`：旁白、字幕图层、响度处理和 FFmpeg 合成脚本。
6. `05_deliverables`：成片和审片联系表；大视频只保存在本地。
7. `06_reports`：技术、语义与视觉验收报告。
8. `99_tests`：模型能力实验，不属于正式交付。

## 关键入口

- 参考片拆解：`01_analysis/reference-01/reference-breakdown.md`
- 产品事实：`02_plan/product-brief.md`
- 模板 DNA：`02_plan/template-dna.json`
- Phase 2 输入与产品事实：`02_plan/intake.json`、`02_plan/product-brief.json`
- 五种受控变体源内容：`02_plan/phase2/variant-content.json`
- 可执行批次清单：`02_plan/phase2/batch-manifest.json`
- 五条脚本与镜头表：`02_plan/phase2/variants/`
- v2 脚本：`02_plan/master-script-v2.md`
- 后期合成：`04_postproduction/assemble_v2.sh`
- v2 验收：`06_reports/v2-verify-report.json`
- v2 成片：`05_deliverables/v2/pre-taped-film-ad-v2-final.mp4`
- Phase 2 成片：`05_deliverables/phase2/variant-01.mp4` 至 `variant-05.mp4`
- Phase 2 验收：`06_reports/phase2-verify-report.json`
- Phase 2 性能记录：`06_reports/phase2-performance-report.json`
- 无上下文冷启动审计：`06_reports/phase2-cold-start-audit.md`
- 人工/AI 操作手册：`../../90_视频生产工具/video-content-skills/skills/reference-ad-factory/references/operator-runbook.md`

## 边界

- 黄色美纹胶与透明 PE 膜永久连接，不得分离。
- 施工顺序必须为先压黄色胶，再向下展开薄膜。
- 成片不少于 20 秒，通常不超过 60 秒。
- 大视频、音频、PPT 和供应商响应元数据不进入 GitHub。
