# AI 视频生产 Skills

这里保存 Codex 可直接调用的本地 Skills。生产不依赖 Dify、n8n 或可视化拖拽工作流。

## 调用顺序

1. [`reference-video-analyzer`](skills/reference-video-analyzer/SKILL.md)：把参考成片转为技术证据、镜头结构和模板 DNA。
2. [`reference-ad-factory`](skills/reference-ad-factory/SKILL.md)：组合参考模板、产品事实、变体策略、质量门和完整 SOP。
3. [`video-batch-producer`](skills/video-batch-producer/SKILL.md)：通过 TokenDance 生成关键帧、通过 nanyao Grok 生成视频，再执行断点续跑、拼接与技术验证；确定性口播继续在后期完成。

```text
参考成片
  → reference-video-analyzer
  → template-dna.json + product brief
  → reference-ad-factory
  → production-plan.json + variant scripts
  → video-batch-producer
  → 旁白 / 字幕 / 后期 / 验收
  → 成片批次
```

## 关键文件

- `skills/*/SKILL.md`：Codex 触发条件和执行规则。
- `skills/*/scripts`：可重复执行的确定性工具。
- `skills/*/references`：按需读取的 SOP、模型说明、数据结构和验收标准。
- `dist/*.skill`：可分发、安装的 Skill 压缩包。

## Git 与本地素材

GitHub 保存代码、脚本、分析、清单、关键帧和验收报告。视频、音频、PPT、凭证和供应商响应元数据只保存在本地。
