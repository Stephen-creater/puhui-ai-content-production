# 浦汇未来 AI 内容生产项目

这是一个以本地 Codex Skills 为核心的 AI 内容与视频生产仓库，包含会议需求、招商内容、参考素材、生成样片、脚本、模型适配器和可复用的批量生产工具。

## 目录地图

| 路径 | 内容 | Git 策略 |
| --- | --- | --- |
| `01_会议与需求` | 原始会议记录和已确认需求 | 小型源文档可跟踪 |
| `02_招商内容` | 招商文档、海报和演示材料 | 源文档按需跟踪，大型 PPT/PDF 默认本地保留 |
| `03_视频项目` | 正式视频项目 | 跟踪脚本、清单、关键帧和验收报告 |
| `90_视频生产工具` | 参考视频分析、广告裂变和批量生产 Skills | 维护中的代码，必须测试和打包 |
| `91_Agent协作工具` | Agent 协作、仓库治理和可复用 Skill | 维护中的代码和规则 |
| `99_研发与临时文件` | 技术调研、第三方参考、沙盒测试和阶段记录 | 只跟踪需要长期保留的证据 |
| `work` | 唯一的本地临时区：缓存、联系表、失败样本和检查点 | 整体 Git 忽略，可重建 |

当前基准项目：[`pre-taped-masking-film`](03_视频项目/pre-taped-masking-film/README.md)。

## 存储与命名规范

- 顶层业务目录使用 `NN_中文类别`；可执行项目、Skill 和脚本目录使用小写 `kebab-case`。
- 新增会议录音建议使用 `YYYY-MM-DD_HH-MM_会议录音.docx`；客户原始文件可保留原名，避免丢失溯源信息。
- 正式视频项目固定使用 `00_input` → `01_analysis` → `02_plan` → `03_generation` → `04_postproduction` → `05_deliverables` → `06_reports`；实验放入 `99_tests`。
- 版本、批次和分镜统一使用 `phase2-v2`、`variant-01`、`scene-01`，不使用 `final2`、`new`、`测试一下` 等不可追溯命名。
- 正式输入、维护中代码、业务交付、本地临时产物和第三方仓库必须分开；禁止新建第二个 `work` 目录。

## 文档与代码同步

- 脚本、JSON 清单和实际产物是当前状态的证据；README 负责导航和规则，`06_reports` 只是特定批次的历史快照。
- 修改路径、入口命令、环境变量或主要能力时，必须在同一次提交中同步对应 README/AGENTS。
- 阶段收尾时使用已安装的 [`neat-freak`](https://github.com/KKKKhazix/khazix-skills/tree/main/neat-freak) Skill；说“整理文档”、“同步一下”、“规范体检”或 `/neat` 即可触发。
- 提交前运行 `python3 91_Agent协作工具/repository-hygiene/check_repository.py`，机械检查顶层目录、重复临时区和 README 本地链接。

## 当前视频生产规范

- 成片时长不少于 20 秒，通常不超过 60 秒，具体由脚本信息量与自然节奏决定。
- 使用 agent-native Skill 和项目清单驱动生产，不依赖可视化拖拽工作流。
- 标准 Skill 链路为 `reference-video-analyzer` → `reference-ad-factory` → `video-batch-producer`。
- 产品演示片采用高密度 B-roll、逐镜自然语速旁白和同源同步字幕；只有明确设计的出镜口播镜头才使用原生对白。
- 优先使用“参考成片 → 模板 DNA → 产品改写 → 受控变体”的生产模式。
- 一体式 Pre-taped Masking Film 必须保持黄色美纹胶与透明 PE 膜永久连接，并严格先贴胶、后拉膜。

## 安全

API Key 不进入仓库。TokenDance 凭证应通过环境变量或 macOS Keychain 提供。

## 许可

本仓库原创代码以 MIT License 开源。客户素材、会议记录、生成媒体、商标及第三方研究材料不因公开存放而自动获得 MIT 授权，其权利归各自权利人所有。
