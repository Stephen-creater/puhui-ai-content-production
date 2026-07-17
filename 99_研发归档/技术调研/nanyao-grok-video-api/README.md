# Nanyao Grok 视频 API 调研归档

本目录保存供应商原始说明与一次端到端验证证据，避免把技术调研散落在
`.work/` 或项目根目录。

## 目录

- `source/nanyaoapi-grok-video-api(2).docx`：供应商更新后的原始 Word 说明。
- `evidence/2026-07-16-fast-direct-link-retest/result.mp4`：Fast 模型直链下载成功样本，本地保留、Git 忽略。
- `evidence/2026-07-16-fast-direct-link-retest/response-meta.json`：原始响应元数据，本地保留、Git 忽略，可能含短期签名 URL。

## 已验证结论

- `grok-imagine-video-1.5-fast` 可完成提交、轮询和直链下载。
- Fast 仅支持 6 秒或 10 秒；当前生产默认 10 秒，最终按分镜窗口裁切。
- 完成后读取响应顶层 `url` 并直接下载，不使用旧的 `/content` 下载接口。
- 一次 6 秒竖屏冒烟测试约 100 秒完成，MP4 为 H.264/AAC、24 fps，完整解码通过。
- 供应商文档标注 Fast 为每次 0.6 元；实际价格以控制台为准。
- API Key 仅保存在环境变量或 macOS Keychain，不得写入本目录或仓库。

生产适配代码位于
`90_视频生产工具/video-content-skills/skills/video-batch-producer/scripts/run_pipeline.py`。
