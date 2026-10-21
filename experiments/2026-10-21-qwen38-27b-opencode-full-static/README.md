# 全量公开 EmbedEval：Qwen 27B / OpenCode / L0+L3

本目录独立于之前的 10 题双 Harness 实验。只使用 **OpenCode**，请求 OpenRouter 的 **`qwen/qwen3.8-27b`**，每题 1 次，仅做 **L0 和 L3 静态评分**。不会启动 Claude Code，不会编译、运行、仿真或安装 SDK。

## 本次有多少题

已检查本地公开快照：**219 道题全部具备 prompt、L0 static.py 和 L3 behavior.py，参考实现 219/219 通过这两层健康检查**。因此候选集合为全部 219 题，不再抽样。清单见 [cases.json](cases.json)，参考检查见 [environment-check.json](environment-check.json)。

覆盖 Zephyr、Embedded Linux、ESP-IDF、STM32 HAL、FreeRTOS，包含 C 代码以及设备树、Kconfig、BitBake 等文本任务。统一收集到 `submission/answer.txt`，其内容仍按各题要求生成，不强行转换成 C。

L0 失败后不执行 L3；未执行不等于通过。本轮保留原有静态规则与其局限，不改变原始评分器。219 题不包含上游的 48 道私有保留题。此前的 10 题是按覆盖面人工选取，并非随机抽样。

## 一键开始 / 续跑

**双击 `start.cmd`。** 不需要修改脚本或填写上一次 run 的目录。

1. 本地重新检查题库、评分器与参考实现，不调用模型。
2. 自动找到本目录上一次正式运行；首次启动则创建新 run。
3. 弹出确认窗口，显示总题数、已完成数、本次待跑/重试数及并发数。点击“是”后才继续；点击“否”不会请求模型。无法显示图形窗口时，改为终端输入 `YES` 确认。
4. 隐藏输入 OpenRouter Key；也可预先设置当前进程的 `OPENROUTER_API_KEY` 或 `BENCH_ANTHROPIC_TOKEN`。密钥不保存到文件，不沿用旧实验的密钥。
5. 首次运行先做 OpenCode 工具/API 预检，再显示百分比进度条、已完成/总题数、耗时、预计剩余时间及实时日志。

首次确认应显示：**总题数 219、已完成 0、本次待跑 219**。默认并发 2，每题最多 600 秒；接口错误单列，绝不关闭 TLS 验证。

OpenCode 文件读写采用每个任务的明确路径白名单，同时匹配绝对路径与相对 Git worktree 的任务前缀；不会放行整个仓库。为防止搜索绕过路径范围，本轮不开放 glob/grep、Shell 或网页等工具，允许任务内文件读取与修改。预检必须同时观察到越界读取被拒绝、正常提交写入成功，不能仅凭进程退出码为 0 放行。

再次启动会自动续跑：

| 上次状态 | 下次双击 start.cmd |
|---|---|
| 已评分通过 / 已评分失败 | 跳过，避免重复付费 |
| 已到时限 / 正常结束但未提交 | 跳过，保留该次实验结果 |
| 接口错误 / 评分器执行错误 | 重新运行该题，保留旧尝试 |
| Ctrl+C 中断 / 进程意外退出 / 尚未开始 | 继续运行 |

完成的静态失败题不会为了“刷过”自动重试；如需独立重复所有题，显式使用 `--new-run`，重新弹窗确认。若题库、评分源码、模型、CLI 版本、运行器或并发/时限配置变化，续跑会拒绝混合数据。

唯一例外是尚未开始任何题目的预检失败：若只修订运行器/日志解析器，允许继续使用同一 run，先将旧配置与代码快照归档到 `config-revisions/`。已有任何题目尝试时仍保持严格冻结。

Key 输入只粘贴 `sk-or-v1-...` 本身；会去掉首尾空白和一对包裹引号，包含 JSON 字段名、逗号、换行等内容时会在请求前报错，不输出 Key 值。OpenCode 的普通错误文本、JSON 字符串/数组/null 等会作为诊断日志保留，不再当作事件对象解析。

## 环境

使用此前准备好的 `../2026-10-20-opus5-harness-comparison/.venv`，以及已安装的 OpenCode；不需要 Claude Code。`start.cmd` 不安装任何依赖。若在另一台电脑运行，先按仓库根目录 README 准备 Python/EmbedEval/OpenCode 环境，再双击启动。

实际远程接口：`https://openrouter.ai/api/v1/messages`，Anthropic Messages 兼容协议，与 10 题试验的 OpenCode 侧保持一致。本次不是本地部署推理；真实上游由 OpenRouter 路由决定。

## 参数与查看结果

在本目录 PowerShell 执行：

```powershell
# 默认：确认后开始或自动续跑
.\start.cmd

# 明确开始全新的一轮；不会覆盖旧结果
.\start.cmd --new-run

# 并发 4；首次使用新并发请新开一轮
.\start.cmd --new-run --concurrency 4

# 只刷新清单和参考检查，不确认、不请求 API
.\start.cmd --prepare-only

# 全量离线模拟，验证进度/评分/报告；不调用 API，明确标为模拟结果
.\start.cmd --dry-run

# 显式续跑某个本目录下的 run
.\start.cmd --resume ".\runs\run-具体目录"
```

`--yes` 是主动跳过确认的可选参数，默认不会启用。离线模拟使用单独的 latest-dry-run 指针和 dry-* 目录，不会混入正式结果。

结果位于 `runs/run-*/`，每完成一题更新：

- `report.md`：全量逐题状态、SDK、难度、耗时和观测 Token。
- `summary.json`：进度、通过率、错误数、待续跑题号、Token 覆盖情况。
- `tasks.csv`：表格分析数据。
- `results.sqlite`：每次尝试的结构化记录。
- `run.log`：实时任务日志。
- `tasks/<题号>/<attempt>/`：原始 prompt、生成文件、评分详情、脱敏 CLI 轨迹与日志。
- `config.json`、`frozen-runner.py`、`frozen-engine.py`：本轮配置和代码快照。

数据恢复以每题原子写入的 result.json 为准，重新建立 SQLite 索引。Ctrl+C 会终止活跃 CLI 进程树，已经完成的文件记录不丢弃。未知 Token 记为 unknown/null，部分事件只能提供下限；不根据自定义 provider 的零估价声称免费。

全量样本包括之前未测的平台和任务类型，尚无可靠总时长。仅按此前约 1–2 分钟/题、并发 2 粗略规划，约需数小时；首次实际运行后以进度条的观测 ETA 为准，长任务、600 秒时限及接口排队可能显著延长时间。

本目录已完成本地准备、离线流程验证以及真实 OpenRouter 微型任务的权限预检，结果见 permission-check.json；尚未自动启动 219 题正式评测，仍需在启动脚本中确认待跑数量。
