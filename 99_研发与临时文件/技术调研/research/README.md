# 第三方参考仓库

本目录保存技术调研所需的第三方源码快照。它们保持自己的仓库、许可证和版本边界，不属于浦汇未来维护代码。

## 小红书发布 PoC 候选

| 本地路径 | 上游 | 固定提交 | 用途 |
| --- | --- | --- | --- |
| `douyin-account-publishing/social-auto-upload` | `dreammis/social-auto-upload` | `d32280c98b51057915cfb61f5fec139a464b8178` | 小红书三账号有人值守发布 PoC |

该目录在主仓库的 `.git/info/exclude` 中按本地第三方参考处理；上表用于保存可复现的来源和提交。第三方源码本身不随主仓库提交。

更新时只允许快进并重新核验：

```bash
git -C 99_研发与临时文件/技术调研/research/douyin-account-publishing/social-auto-upload pull --ff-only
git -C 99_研发与临时文件/技术调研/research/douyin-account-publishing/social-auto-upload rev-parse HEAD
```

如果提交变化，必须同步更新本文件、对应调研结论和 PoC 手册，不得默默漂移。
