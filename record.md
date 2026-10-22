# 实验运行记录

本表按 `experiments/*/runs/run-*/` 中的实际运行结果整理。时间为各题最早开始至最晚结束的**北京时间（UTC+8）**，不是仅凭目录名推测。题数指不同题目数；同一题在两个 harness 各跑一次时，计为两个评测任务。以下均只评 L0/L3 静态规则，不含编译或硬件运行。

| 运行时间（北京时间） | 模型与接口 | Harness | 题数 / 任务数 | 结果速览 | 对应报告 |
|---|---|---|---:|---|---|
| 2026-10-20 15:44–15:58 | `claude-opus-5`，第三方网关 | OpenCode、Claude Code | 10 / 20 | OpenCode 7/10（70.0%）；Claude Code 7/10（70.0%） | [本次 report.md](experiments/2026-10-20-opus5-harness-comparison/runs/run-20261020-154313-c6793e/report.md) |
| 2026-10-20 15:44–16:12 | `qwen/qwen3.8-27b`，OpenRouter | OpenCode、Claude Code | 10 / 20 | OpenCode 2/10（20.0%）；Claude Code 3/10（30.0%） | [本次 report.md](experiments/2026-10-20-qwen38-27b-harness-comparison/runs/run-20261020-154440-282906/report.md) |
| 2026-10-21 14:07–14:18 | `qwen3.8-27b-coder390-q6k-mtp`，本地社区版 | OpenCode | 10 / 10 | 2/10（20.0%） | [本次 report.md](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/report.md) |
| 2026-10-21 19:08 至 2026-10-22 10:05（含中断、续跑） | `qwen/qwen3.8-27b`，OpenRouter | OpenCode | 219 / 219 | 120/219（54.8%） | [本次 report.md](experiments/2026-10-21-qwen38-27b-opencode-full-static/runs/run-20261021-185529-c2b052/report.md) |
| 2026-10-21 19:19–20:14 | `qwen3.8-27b-coder390-fp8`，本地 | OpenCode | 219 / 219 | 116/219（53.0%） | [本次 report.md](experiments/2026-10-21-full-public-l0l3-qwen-fp8-opencode/runs/run-20261021-191945-c710e8/report.md) |

前 3 次使用同一组 10 道 Zephyr 题；后两次使用全部 219 道公开题。`结果速览` 的分母是该 harness 计划运行的题数，包含评分失败、接口错误和超时；具体逐题状态以各自的 `report.md` 和同目录 `summary.json` 为准。

## 未生成正式报告的启动目录

- [OpenRouter Qwen 初次启动](experiments/2026-10-20-qwen38-27b-harness-comparison/runs/run-20261020-154313-a633c6/config.json)：选定 10 题，只有配置，没有逐题结果或 `report.md`；正式结果见上表第二行。
- [本地社区版初次启动](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140539-0d4de1/config.json)：选定 10 题，只有配置，没有逐题结果或 `report.md`；正式结果见上表第三行。

`runs/dry-*` 是离线流程测试或预检，不是正式模型跑分，因此不列入表中。

仓库保留实验脚本、固定题集、环境检查、正式报告与汇总配置，以及详细报告实际引用的案例提交和评分文件。其余逐题工作区、原始日志、数据库和临时状态保存在运行电脑，不随 Git 发布。

## 相关报告与实验入口

- [固定 OpenCode 的三模型对比报告](FIRMWARE_BENCHMARK_REPORT_OPENCODE_THREE_MODELS.md)：汇总前 3 次 10 题实验，并附本地社区版的案例证据。
- [本地社区版实验说明](experiments/2026-10-21-local-qwen38-27b-opencode/README.md)及[与 OpenRouter 版对照](experiments/2026-10-21-local-qwen38-27b-opencode/comparison.md)。
- [本地 FP8 全量实验说明及启动入口](experiments/2026-10-21-full-public-l0l3-qwen-fp8-opencode/README.md)。
- [OpenRouter Qwen / OpenCode 全量静态评测说明及启动入口](experiments/2026-10-21-qwen38-27b-opencode-full-static/README.md)。

新增正式运行后，应依据该次 `config.json`、`summary.json` 和逐题 `result.json` 更新本表，并直接链接该次 `report.md`。
