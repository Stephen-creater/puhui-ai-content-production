# Agent 协作工具

这里只放与业务领域无关、需要长期维护的 Agent 协作与仓库治理工具。视频生产 Skill 继续位于 `../90_视频生产工具/`。

## 内容

- `loop-engineering-skill`：用意图、完成标准、边界和授权驱动长任务闭环。
- `repository-hygiene`：本仓库的机械式结构与 README 链接检查。
- 全局 `neat-freak`：来自 [`KKKKhazix/khazix-skills`](https://github.com/KKKKhazix/khazix-skills/tree/main/neat-freak)，用于里程碑后对齐文档、项目规则和实际代码。该 Skill 安装在用户级 Agent Skills 目录，不复制进本仓库。

## 验证

```bash
python3 91_Agent协作工具/repository-hygiene/check_repository.py
python3 -m unittest discover -s 91_Agent协作工具/repository-hygiene/tests -p 'test_*.py'
```
