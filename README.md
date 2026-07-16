# 浦汇未来 AI 短视频生产系统

一套以本地 Agent Skills 和可审计脚本为核心的短视频生产仓库：把授权参考成片拆成结构化模板，用已确认的产品事实生成受控变体，再经过成本门、断点续跑、后期合成和人工验收输出批量成片。

- GitHub：<https://github.com/Stephen-creater/puhui-ai-content-production>
- 当前基准项目：[`pre-taped-masking-film`](03_视频项目/pre-taped-masking-film/README.md)
- 核心实现：[`video-content-skills`](90_视频生产工具/video-content-skills/README.md)

## 这个仓库解决什么

```text
授权参考成片 + 产品事实 + 产品图 + 成本授权
  → 技术拆解与镜头功能分析
  → template-dna.json
  → 母版脚本与 3～5 个受控变体
  → 分镜关键帧与图生视频
  → 旁白、字幕、后期和技术验证
  → 人工画面复核
  → 20～60 秒成片批次
```

这不是 Dify/n8n 式可视化工作流，也不是一个开箱即用的 SaaS。仓库保存的是可读、可测试、可断点恢复的 Skill、脚本、JSON 清单和验收证据；付费生成和对外发布仍保留明确的人工授权门。

## 当前能力与成熟度

| 能力 | 当前证据 | 状态 |
| --- | --- | --- |
| 参考视频拆解 | 可提取媒体参数、分镜证据、联系表和可复用模板 DNA | **可用**，语义/OCR/镜头功能仍需 Agent 或人工富化 |
| 参考片驱动的广告改写 | 产品事实、禁止表述、模板 DNA 和变体策略分离管理 | **可用** |
| 3～5 条受控变体 | 基准项目已完成 5 条、25 个独立镜头，覆盖清洁成本、效率、产品结构、专业推荐和前后对比 | **已验收基线** |
| 批量生成与断点续跑 | 支持 dry-run、付费任务上限、关键帧先审、缺失资产续跑和定点重试 | **可用**，付费生成必须显式授权 |
| 技术验证与后期 | 支持 ffprobe 结构检查、分镜旁白/字幕合成、时长和资产唯一性报告 | **可用**，不替代人工画面验收 |
| 抖音发布 | 一个测试账号已完成登录、Cookie 检查、短信验证、单条公开发布和作品回查 | **有人值守 PoC**，非生产级多账号系统 |
| 小红书 3 账号 | 隔离环境、单次提交安全补丁和测试已就绪 | **已暂停**，未登录、未发布 |
| 多平台多账号无人值守 | 尚无多日、多账号、页面改版后的稳定性证据 | **未实现 / 未证明** |

基准项目的具体结果见 [`Phase 2 v2 最终验收`](03_视频项目/pre-taped-masking-film/06_reports/phase2-v2-zero-api-final-report.md)；发布能力边界见 [`抖音单账号 PoC`](99_研发与临时文件/技术调研/douyin-single-account-poc.md) 和 [`小红书三账号 PoC`](99_研发与临时文件/技术调研/xiaohongshu-three-account-poc.md)。

## 5 分钟上手

### 1. 准备环境

- Python 3.11+
- FFmpeg 和 ffprobe
- 能读取项目 `SKILL.md` 的 Codex/Agent
- 只有执行付费生成时才需要 `TOKENDANCE_API_KEY`

```bash
git clone https://github.com/Stephen-creater/puhui-ai-content-production.git
cd puhui-ai-content-production
python3 --version
ffmpeg -version
ffprobe -version
```

### 2. 读取基准和生产手册

1. [`基准项目 README`](03_视频项目/pre-taped-masking-film/README.md)
2. [`Skill 调用顺序`](90_视频生产工具/video-content-skills/README.md)
3. [`无上下文操作手册`](90_视频生产工具/video-content-skills/skills/reference-ad-factory/references/operator-runbook.md)
4. [`验收门`](90_视频生产工具/video-content-skills/skills/reference-ad-factory/references/quality-gates.md)

### 3. 先跑零成本预览

下面的命令只读取已有清单，不调用付费 API：

```bash
python3 90_视频生产工具/video-content-skills/skills/video-batch-producer/scripts/run_pipeline.py \
  --project 03_视频项目/pre-taped-masking-film/03_generation/phase2-v2-unique
```

预览应明确显示模型、分辨率、复用资产、待生成任务数、付费秒数和重试上限。没有 `--execute --cost-authorized` 和三类数值上限时，执行器不会进入付费生成。

## 核心 Skill 链路

| Skill | 职责 | 主要产物 |
| --- | --- | --- |
| [`reference-video-analyzer`](90_视频生产工具/video-content-skills/skills/reference-video-analyzer/SKILL.md) | 对授权参考片做确定性拆解，再由 Agent 完成语义富化 | `reference-analysis.json`、联系表、`template-dna.json` |
| [`reference-ad-factory`](90_视频生产工具/video-content-skills/skills/reference-ad-factory/SKILL.md) | 组合模板 DNA、产品事实、变体策略、成本门和验收门 | 产品简报、生产计划、变体脚本、批次清单 |
| [`video-batch-producer`](90_视频生产工具/video-content-skills/skills/video-batch-producer/SKILL.md) | 生成关键帧和镜头、恢复缺失任务、定点重试并用 ffprobe 验证 | `project.json`、`status.json`、关键帧、镜头、`verify-report.json` |

Skills 的可分发包位于 [`90_视频生产工具/video-content-skills/dist`](90_视频生产工具/video-content-skills/dist/)。

## 仓库目录

| 路径 | 用途 | GitHub 中保留什么 |
| --- | --- | --- |
| `01_会议与需求` | 原始会议和已确认需求 | 必要的小型源文档 |
| `02_招商内容` | 招商文档、海报和方案 | 轻量、可分发文档；大型 PPT/PDF 默认本地保留 |
| `03_视频项目` | 正式视频项目 | 分析、脚本、清单、关键帧、后期脚本和验收报告 |
| `90_视频生产工具` | 参考拆解、广告编排和批量生成 Skills | 维护中的代码、测试、参考文档和 `.skill` 包 |
| `91_Agent协作工具` | Agent 意图控制和仓库治理 | `loop-engineering` 与 `repository-hygiene` |
| `99_研发与临时文件` | 技术调研、第三方参考、沙盒和阶段记录 | 长期有价值的证据、固定提交和安全补丁 |
| `work` | 唯一本地临时区 | 不进 Git；联系表、缓存、失败样本和检查点均可重建 |

项目内的正式视频目录固定为 `00_input` → `01_analysis` → `02_plan` → `03_generation` → `04_postproduction` → `05_deliverables` → `06_reports`；能力实验放入 `99_tests`。

## 大文件与本地资产

GitHub 用于保存可复现的工作流，不是媒体网盘。仓库默认忽略：

- MP4/MOV/MKV 视频；
- WAV/MP3/M4A 音频；
- PPTX 演示文件；
- `work/` 中间产物；
- 可能含签名 URL、请求头或访问标识的供应商响应元数据。

因此 README 中列出的成片路径可能只在完整本地工作区存在；GitHub 会保留脚本、清单、关键帧和验收报告。根目录不在上表的素材盘、成品盘或第三方工具仅是本地资产，不属于仓库公开契约。

## 验证

```bash
# 视频工具单元测试：当前 27 项
python3 -m unittest discover \
  -s 90_视频生产工具/video-content-skills/skills/reference-ad-factory/tests \
  -p 'test_*.py'
python3 -m unittest discover \
  -s 90_视频生产工具/video-content-skills/skills/video-batch-producer/tests \
  -p 'test_*.py'

# Agent 工具与仓库契约
python3 91_Agent协作工具/loop-engineering-skill/tests/test_structure.py
python3 -m unittest discover \
  -s 91_Agent协作工具/repository-hygiene/tests \
  -p 'test_*.py'
python3 91_Agent协作工具/repository-hygiene/check_repository.py
```

## 成本、凭证与对外动作

- API Key、Cookie、短信验证码和真实登录态不进仓库；优先使用环境变量或 macOS Keychain。
- 付费生成必须先 dry-run，并设置图片任务数、视频任务数和付费秒数上限。
- 发布、短信验证和平台风控必须由用户本人授权或接管；结果不明确时先回查，不盲目重发。
- 当前默认生成路由是 TokenDance；模型、协议、分辨率和价格可变，付费前必须查看实时模型目录。

## 许可和内容权利

仓库原创代码以 [MIT License](LICENSE) 开源。客户素材、会议记录、生成媒体、商标及第三方调研材料不因位于本仓库而自动获得 MIT 授权，其权利归原权利人。第三方参考项目保留独立许可证和来源记录，不视为浦汇未来原创代码。
