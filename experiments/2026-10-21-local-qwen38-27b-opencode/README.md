# 第三组：本地 Qwen / OpenCode

沿用第二组 `2026-10-20-qwen38-27b-harness-comparison` 的 10 道 Zephyr 题和 L0/L3 静态评分。本组只运行 OpenCode 1.19.3，模型为本地接口 `qwen3.8-27b-coder390-q6k-mtp`，地址为 `http://127.0.0.1:18931/v1`。远程 `qwen/qwen3.8-27b` 不重跑；对照结果取第二组已有的 OpenCode 数据（通过 2/10、完成评分 8/10）。

运行前确认本地模型服务已启动。在此目录运行 `start.cmd` 开始正式实验；`start.cmd --dry-run` 只验证题目、评分和报告流程，不调用模型。默认 10 题各 1 次、并发 2、每题限时 600 秒。任务开始前会预检模型调用、文件写入和越界读取拒绝。输出写入 `runs/run-*`，包括 `report.md`、`summary.json`、`tasks.csv`、轨迹和逐题评分。

本地接口不需要远程 OpenRouter 密钥。预检与评分仅覆盖 L0/L3；不验证固件编译或硬件运行。对照时还需注意远程模型与本地模型的量化和后端可能不同。

正式运行已完成，10 题通过 2 题、完成评分 10 题。逐题对照见 [comparison.md](comparison.md)。
