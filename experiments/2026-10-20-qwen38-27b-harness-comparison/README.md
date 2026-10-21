# Qwen 3.8 27B：OpenCode / Claude Code 对比

日期：2026-10-20（Asia/Shanghai）。本组与 Opus 实验分开记录，共享已安装的只读题库及 Python 依赖环境。

- 模型 ID：`qwen/qwen3.8-27b`。
- 网关：`https://openrouter.ai/api`，两侧使用 Anthropic Messages 入口 `/api/v1/messages`。
- 同一 10 题：`subsets/pilot-10.json`；简单 3、中等 4、困难 3。
- OpenCode 1.19.3 / Claude Code 2.1.304，每组合 1 次，共 20 个计分任务。
- 并发 2，同 Harness 最多 1；每任务 600 秒。评分仅 L0/L3，不验证编译或运行。
- 两组同时运行时，配置的全局任务并发上限合计为 4；实际受各 Harness 队列约束。

## 接口预检与兼容性调整

OpenRouter 公开模型列表能找到精确模型 ID，支持 `tools`、`tool_choice`；提供的密钥认证检查成功。真实后端由 OpenRouter 路由决定，模型 ID 不表示固定供应商。

首次预检中，OpenCode 成功；Claude Code 收到 HTTP 400，原因是延迟加载工具的 `defer_loading` 字段缺少可发现工具入口。该次只有预检，没有计分结果，原日志保留。

第二次运行设置 `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1`、`ENABLE_TOOL_SEARCH=false`，去除不兼容字段；两个 Harness 均通过正常文件写入和越界读取拒绝探针，随后开始计分任务。此调整仅适用于本组 Claude Code，属于与 Opus 配置的明确差异。未使用本地协议代理。

官方依据：[OpenRouter Claude Code 接入](https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration)、[Claude Code 环境变量](https://code.claude.com/docs/en/env-vars)。OpenRouter 不保证所有非 Anthropic 模型与 Claude Code 的完整兼容性；本次预检通过仅验证用到的协议与文件工具路径。

## 查看进度与结果

- `launch.log`：启动与实时进度日志。
- `runs/run-*/run.log`：正式任务日志。
- `runs/run-*/tasks/`：每次尝试的代码、评分、原始脱敏轨迹。
- `runs/run-*/report.md`、`summary.json`、`tasks.csv`、`results.sqlite`：运行完成后汇总。
- `runs/run-*/config.json`、`frozen-runner.py`：实际配置及运行器快照。

```powershell
Get-Content .\launch.log -Tail 20 -Wait
```

密钥只注入进程环境，没有写入本目录的配置。重新双击 `start.cmd` 会启动新的实验并要求隐藏输入密钥，不能在现有实验仍运行时误当作“查看进度”使用。断点续跑需传原 run 目录并保持源码、版本和配置一致；源码已变化时使用该 run 的 frozen-runner.py。

总体方案参见相邻 Opus 目录的 PLAN.md / README.md。各 Harness 默认推理策略未对齐；结果属于静态小样本对比，不是完整固件能力排名。
