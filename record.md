# 实验运行记录

本表按 `experiments/*/runs/run-*/` 中的实际运行结果整理。时间为各题最早开始至最晚结束的**北京时间（UTC+8）**，不是仅凭目录名推测。题数指不同题目数；同一题在两个 harness 各跑一次时，计为两个评测任务。以下均只评 L0/L3 静态规则，不含编译或硬件运行。

| 运行时间（北京时间） | 模型与接口 | Harness | 题数 / 任务数 | 结果速览 | 对应报告 |
|---|---|---|---:|---|---|
| 2026-10-20 15:44–15:58 | `claude-opus-5`，第三方网关 | OpenCode、Claude Code | 10 / 20 | OpenCode 7/10；Claude Code 7/10 | [本次 report.md](experiments/2026-10-20-opus5-harness-comparison/runs/run-20261020-154313-c6793e/report.md) |
| 2026-10-20 15:44–16:12 | `qwen/qwen3.8-27b`，OpenRouter | OpenCode、Claude Code | 10 / 20 | OpenCode 2/10；Claude Code 3/10；另有 2 次接口错误、1 次超时 | [本次 report.md](experiments/2026-10-20-qwen38-27b-harness-comparison/runs/run-20261020-154440-282906/report.md) |
| 2026-10-21 14:07–14:18 | `qwen3.8-27b-coder390-q6k-mtp`，本地社区版 | OpenCode | 10 / 10 | 2/10 | [本次 report.md](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/report.md) |
| 2026-10-21 19:19–20:14 | `qwen3.8-27b-coder390-fp8`，本地 | OpenCode | 219 / 219 | 116/219；另有 2 题超时 | [本次 report.md](experiments/2026-10-21-full-public-l0l3-qwen-fp8-opencode/runs/run-20261021-191945-c710e8/report.md) |

前 3 次使用同一组 10 道 Zephyr 题；最后一次使用全部 219 道公开题。`结果速览` 的分母是该 harness 计划运行的题数，包含评分失败、接口错误和超时；具体逐题状态以各自的 `report.md` 和同目录 `summary.json` 为准。

## 未生成正式报告的启动目录

- [OpenRouter Qwen 初次启动](experiments/2026-10-20-qwen38-27b-harness-comparison/runs/run-20261020-154313-a633c6/config.json)：选定 10 题，只有配置，没有逐题结果或 `report.md`；正式结果见上表第二行。
- [本地社区版初次启动](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140539-0d4de1/config.json)：选定 10 题，只有配置，没有逐题结果或 `report.md`；正式结果见上表第三行。

`runs/dry-*` 是离线流程测试或预检，不是正式模型跑分，因此不列入表中。

## 已准备、尚无正式报告的实验

- [OpenRouter Qwen / OpenCode 全量静态评测](experiments/2026-10-21-qwen38-27b-opencode-full-static/README.md)：已准备 219 题运行入口；截至本记录发布时，仓库内还没有它的正式 `report.md`。其他机器上的实际运行状态需以该机器的结果为准。

新增正式运行后，应依据该次 `config.json`、`summary.json` 和逐题 `result.json` 更新本表，并直接链接该次 `report.md`。
