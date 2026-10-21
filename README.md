# Firmware Agent Benchmark

在 EmbedEval 上比较 OpenCode / Claude Code，记录评分、耗时、Token 和逐题产物。

## 全量 Qwen / OpenCode 静态评测

新增 [219 题全量实验目录](experiments/2026-10-21-qwen38-27b-opencode-full-static/README.md)：只跑 OpenCode + OpenRouter `qwen/qwen3.8-27b`，只执行 L0/L3。219 题均有这两层检查，参考实现已全部通过健康检查。

环境准备完成后双击该目录的 `start.cmd`：先弹窗确认总题数、已完成和本次待跑数量，再输入 Key；支持进度条、日志和逐题保存。再次启动默认自动续跑，已评分任务不重复请求模型；运行脚本不安装依赖。

```powershell
.\experiments\2026-10-21-qwen38-27b-opencode-full-static\start.cmd
```

## 已完成的实验

10 道 Zephyr 任务，每组合运行 1 次，共 40 个计分任务；仅运行 L0/L3 静态检查，未验证编译或硬件运行。

| 模型接口 | OpenCode | Claude Code |
|---|---:|---:|
| claude-opus-5（第三方远程网关，非官方直连） | 7/10 | 7/10 |
| qwen/qwen3.8-27b（OpenRouter 远程接口） | 2/10 | 3/10 |

通过数以全部计划任务为分母，包含接口异常等未成功交付的情况。Qwen 的两个 Harness 在共同完成评分的 7 题上均通过 2 题，不能只凭总通过数判断 Harness 优劣。报告中的“模拟本地”是展示标签；本次没有本地模型推理或本地性能测量。

- [Opus 实验报告](experiments/2026-10-20-opus5-harness-comparison/runs/run-20261020-154313-c6793e/report.md)
- [Qwen 实验报告](experiments/2026-10-20-qwen38-27b-harness-comparison/runs/run-20261020-154440-282906/report.md)
- [40 任务 CSV](evaluation/merged-results.csv) / [合并 JSON](evaluation/merged-results.json)

## 目录

```text
benchmarks/       # 已下载的公开题库和上游评测代码
evaluation/       # 子集、汇总指标和报告生成脚本
experiments/      # 实验配置、启动脚本、实际运行结果及轨迹
```

保留正式实验的提交代码、评分明细、脱敏日志、SQLite 结果库及冻结配置。虚拟环境、CLI 内部状态、重复下载 ZIP、离线模拟结果和 EmbedAgent 上游历史输出不提交。

## 在新电脑准备环境

以下为 Windows PowerShell；需 Python 3.12+、uv、Node/npm、Git。虚拟环境不能从其他电脑直接复制。

```powershell
git clone https://github.com/ChinaYiqun/firmware-test.git
cd firmware-test

uv venv --python 3.12 experiments/2026-10-20-opus5-harness-comparison/.venv
uv pip install --python experiments/2026-10-20-opus5-harness-comparison/.venv/Scripts/python.exe --editable benchmarks/embedeval-main

npm.cmd install -g opencode-ai@1.19.3 @anthropic-ai/claude-code@2.1.304
```

本次环境版本见实验目录 `requirements.lock.txt`；文件中的 editable 路径属于原机器，迁移时以本仓库实际路径安装。

## 启动实验

```powershell
# Opus：启动后隐藏输入第三方网关 Key
.\experiments\2026-10-20-opus5-harness-comparison\start.cmd

# Qwen：启动后隐藏输入 OpenRouter Key
.\experiments\2026-10-20-qwen38-27b-harness-comparison\start.cmd
```

每次启动创建独立 run。先做 API/工具权限预检，再执行任务，显示进度与日志。两个实验共享 Python 环境，分别保存结果。启动脚本不安装依赖，也不包含密钥。

可用参数：`--dry-run`（不调用 API）、`--concurrency 4`、`--repetitions 3`、`--resume <run目录>`。已有运行结果使用原机器的绝对路径作为历史记录；新运行会使用当前仓库路径。断点续跑要求版本和配置完全一致，迁移后应新建 run。

## 数据集来源

- [Ecro/embedeval](https://github.com/Ecro/embedeval)：本地快照包含 219 道公开题；保留上游 Apache-2.0 LICENSE 和原始文档。48 道私有题未获取。
- [icip-cas/EmbedAgent](https://github.com/icip-cas/EmbedAgent)：EmbedBench 的 126 道题位于 `benchmarks/EmbedAgent-main/dataset/EmbedBench.json`，同时保留上游 README 与评测脚本。

上游内容保留其各自的授权状态；本仓库不对第三方内容追加授权。接口配置、Token 原始记录及逐题评分保留在各实验目录，合并结构化指标位于 evaluation/。
