# 固件代码生成评测：固定 OpenCode，对比三种模型接口

评测日期：2026-10-20 至 2026-10-21。使用同一组 10 道 EmbedEval 题，固定 **OpenCode 1.19.3**，比较第三方网关 `claude-opus-5`、OpenRouter `qwen/qwen3.8-27b`、本地 `qwen3.8-27b-coder390-q6k-mtp`。每组每题运行 1 次，共 **30 个 OpenCode 任务**。原始分数均未人工调整。

## 1. 测试集与抽样范围

[EmbedEval](https://github.com/Ecro/embedeval) 的本地冻结题库包含 219 道公开题；本次人工选取其中 10 道 Zephyr 题（简单 3、中等 4、困难 3），覆盖 GPIO、UART、SPI/I2C、定时器、线程、DMA 和 ISR 并发。10 题仅占公开题约 4.6%，不是随机代表性抽样。

三组使用同一题目清单、同一评分源码哈希 `3a34460a8589c9c30e881a372950e84eea6db365df66d96de2de0243ba9a57af`。只执行 **L0 静态规则 + L3 领域启发式检查**；L0 失败后不执行 L3。L1 编译、L2 运行和硬件测试均未执行。三组运行前的参考实现健康检查均为 10/10；这只说明参考实现通过当前 L0/L3 规则。

| 题号 | 难度 | 任务 |
|---|---|---|
| gpio-basic-001 | 简单 | GPIO 按键中断、LED 翻转 |
| uart-001 | 简单 | UART 轮询回显 |
| spi-i2c-002 | 简单 | SPI 回环测试 |
| spi-i2c-001 | 中等 | I2C 读取与错误处理 |
| timer-002 | 中等 | 定时器回调提交工作队列 |
| threading-001 | 中等 | 消息队列生产者/消费者 |
| dma-001 | 中等 | 内存到内存 DMA |
| threading-004 | 困难 | 互斥锁优先级继承 |
| dma-003 | 困难 | DMA 环形缓冲 |
| isr-concurrency-001 | 困难 | ISR 安全环形缓冲 |

## 2. 核心结果

| 模型与接口 | 通过 / 计划 | 端到端成功率 | 通过 / 已评分 | L0 通过 / 已评分 | L3 通过 / 已执行 | 基础设施错误 |
|---|---:|---:|---:|---:|---:|---:|
| `claude-opus-5` · 第三方远程网关 | 7/10 | 70% | 7/10 | 8/10 | 7/8 | 0 |
| `qwen/qwen3.8-27b` · OpenRouter 远程接口 | 2/10 | 20% | 2/8 | 5/8 | 2/5 | 2 |
| **`qwen3.8-27b-coder390-q6k-mtp` · 社区优化版、本地接口** | **2/10** | **20%** | **2/10** | **6/10** | **2/6** | **0** |

端到端成功率使用计划的 10 题作分母。OpenRouter 组的 `timer-002` 和 `dma-003` 因 TLS 证书错误未完成评分；不能把它们写成代码失败，也不能在“已评分通过率”中把它们计入分母。本地社区版 10 题均完成评分，没有接口错误。Opus 在当前规则下通过 7 题，比两组 Qwen 各多 5 题；10 题、单次运行不支持通用能力排名。

两组 Qwen 总通过数相同，但成功题目有变化：两者都通过 `spi-i2c-001`；OpenRouter 组另通过 `spi-i2c-002`，本地社区版另通过 `threading-001`。在 OpenRouter 组实际完成评分的共同 8 题上，两组都是 2/8，但不是同一批题通过。`timer-002` 和 `dma-003` 在本地组均完成评分且未通过，不能拿这两题推断远程组本来会通过或失败。

| 模型与接口 | 简单 | 中等 | 困难 |
|---|---:|---:|---:|
| Opus 第三方网关 | 3/3 | 3/4 | 1/3 |
| Qwen OpenRouter | 1/3 | 1/4 | 0/3 |
| Qwen 本地社区版 | 0/3 | 2/4 | 0/3 |

分母包含该难度全部计划题目，包括 OpenRouter 组的接口错误。

## 3. 特别说明：本地 `qwen3.8-27b-coder390-q6k-mtp`

这是用户提供的**社区优化版模型标识**，本次由本机 OpenAI 兼容接口 `http://127.0.0.1:18931/v1/chat/completions` 提供服务；运行前 `/v1/models` 返回了相同模型 ID。它是实际完成本地推理的第三组，不能沿用上一版分享报告中“没有本地推理组”的描述。

模型名称中的 `coder390`、`q6k`、`mtp` 是服务端暴露的标识片段。本次未取得权重哈希、发布页面、优化方法、量化参数、底层运行引擎或硬件规格，因此**不能仅凭名称断定其权重与 OpenRouter 版相同、量化方式为何，或优化具体带来了什么效果**。OpenRouter 的模型 ID 也未锁定单一上游供应商。这里比较的是两个实际可调用的服务配置，不是严格的同权重部署对照。

本地组沿用同样的题目与 L0/L3 评分，但另建了单题独立 Git 工作区，确保 OpenCode 的越界读取预检真正拒绝工作区外文件；预检结果为“越界读取拒绝、提交文件写入成功”。该组使用 OpenAI 兼容协议，前两组使用 Anthropic Messages 兼容协议；冻结运行器、服务后端、网络条件及执行日期并不相同。三组都使用每题独立会话、相同写入 `submission/main.c` 的提交说明、文件读写/搜索工具，无 Shell、网页或子 Agent。工具权限预检不等于操作系统沙箱。

## 4. 执行时间、Token 与工具调用

### 4.1 任务耗时

| 模型与接口 | 10 题累加秒 | 平均秒/题 | 中位秒/题 | P95 秒 | 最长秒 |
|---|---:|---:|---:|---:|---:|
| Opus 第三方网关 | 648.7 | 64.9 | 48.2 | 150.3 | 154.6 |
| Qwen OpenRouter | 898.6 | 89.9 | 37.6 | 287.2 | 398.8 |
| Qwen 本地社区版 | 1302.0 | 130.2 | 127.6 | 248.5 | 313.1 |

任务耗时包括 CLI 启动、模型等待、工具交互及内部重试，不含排队、预检和评分；OpenRouter 组的时间包含两次基础设施错误任务。累加秒数不是并发墙钟。按各组 OpenCode 首个计分任务开始到最后一个结束计算，Opus 为约 12 分 32 秒，OpenRouter Qwen 为约 26 分 33 秒，本地社区版为约 10 分 58 秒。各组并发调度和服务条件不同，**墙钟与任务耗时均不能直接解释为模型纯推理速度**。P95 使用 `(n-1)×0.95` 位置线性插值，仅作描述。

### 4.2 观测 Token 与工具调用

| 模型与接口 | 非缓存输入 | 缓存读 | 输出含单列推理 | 其中单列推理 | 观测总 Token | 用量覆盖 | 工具调用 |
|---|---:|---:|---:|---:|---:|---|---:|
| Opus 第三方网关 | 407,459 | 0 | 115,295 | 0 | 522,754 | 10 题完整 | 36 |
| Qwen OpenRouter | ≥ 91,323 | ≥ 179,600 | ≥ 73,919 | ≥ 57,829 | ≥ 344,842 | 8 题完整、1 题部分、1 题未知 | 43 |
| Qwen 本地社区版 | 184,460 | 157,811 | 50,481 | 0 | 392,752 | 10 题完整 | 40 |

缓存写入三组记录值均为 0。OpenCode `step_finish.part.tokens` 的各次记录相加得出表中数值；观测总量为非缓存输入、缓存读/写、输出及单列推理之和。`≥` 表示 OpenRouter 组的已观测下限，未知项没有按零处理。本地组的推理字段记录为 0，仅表示服务未单列该字段，不能证明模型没有推理。不同服务的 tokenizer 和缓存计量可能不同，Token 数不宜当成跨服务的精确计算成本；未取得独立账单，不计算费用或性价比。工具调用包括被拒绝的调用，不等于有效修改次数。

## 5. 代表性案例：区分规则拒绝与代码风险

以下均保留原始 L0/L3 得分。静态规则拒绝不自动等于编译或硬件故障；规则漏识别也不自动证明整份代码正确。

### 5.1 `uart-001`：两组 Qwen 的 `while (true)` 均被漏识别

本地社区版的提交在 UART 设备准备检查后使用 `while (true)` 循环读取并回显，原始结果是 **L3 失败**，唯一拒绝项为 `infinite_loop_present`。OpenRouter 组同题也因相同检查项失败。该规则只搜索 `while (1)` / `while(1)` / `for (;;)` / `for(;;)`，未识别可见的 `while (true)`。这是一处规则覆盖不足；程序是否能编译并正确回显仍未验证。[本地代码](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__uart-001__1/8971329a/workspace/submission/main.c) · [本地评分](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__uart-001__1/8971329a/evaluation.json)

### 5.2 `timer-002`：静态失败之外还有可核对的 API 参数风险

本地社区版原始结果为 **L0 失败**，拒绝项 `one_shot_period_no_wait`：评分器未找到一次性定时器应使用的 `K_NO_WAIT` 周期。生成代码还写了 `K_TIMER_DEFINE(my_timer, timer_expiry)` 与 `k_timer_start(&my_timer, K_MSEC(1000))`，均只传入两个实参。Zephyr 4.1 的 [Timer API](https://docs.zephyrproject.org/4.1.0/doxygen/html/group__timer__apis.html)分别要求三个参数：定义宏包含 `stop_fn`，启动函数包含 `period`。因此这里有明确的签名不匹配风险；本次仍未实际编译。OpenRouter 组该题为 TLS 基础设施错误，不能作逐题代码优劣比较。[本地代码](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__timer-002__1/4de58bb2/workspace/submission/main.c) · [本地评分](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__timer-002__1/4de58bb2/evaluation.json)

### 5.3 `threading-004`：优先级规则失败与宏调用风险同时存在

本地社区版原始结果为 **L3 失败**，拒绝项 `three_distinct_priorities`。代码表面写有低/中/高线程优先级 10、7、4，但 `K_THREAD_DEFINE` 把第三个参数写成 `K_THREAD_STACK_SECTION_DEFAULT`，随后还传入入口函数等参数；每次调用共 11 个实参。评分器按正确的参数位置提取优先级，因此未识别这三个值。Zephyr 4.1 的 [线程 API](https://docs.zephyrproject.org/4.1.0/doxygen/html/group__thread__apis.html)规定 `K_THREAD_DEFINE` 为 9 个参数，第三个应是线程入口。此处不能只当作正则误判，生成代码本身也有明确的宏签名风险。[本地代码](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__threading-004__1/a083a580/workspace/submission/main.c) · [本地评分](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__threading-004__1/a083a580/evaluation.json)

### 5.4 `spi-i2c-002`：本地组从远程通过变为规则失败

OpenRouter Qwen 通过该题，本地社区版则因 L3 `ready_check_before_spi` 未通过。评分器要求在 `spi_transceive()` 前调用 `device_is_ready()`；本地代码改为 `spi_is_ready(spi)`。Zephyr 4.1 [SPI API](https://docs.zephyrproject.org/4.1.0/doxygen/html/group__spi__interface.html)文档列出的是接收 `spi_dt_spec` 的 `spi_is_ready_dt()`；现有代码的函数名和传参值得编译核对。这里既有评分器只认固定写法的问题，也有实际 API 适配风险，不能直接补分。[本地代码](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__spi-i2c-002__1/5d517765/workspace/submission/main.c) · [本地评分](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__spi-i2c-002__1/5d517765/evaluation.json)

### 5.5 `isr-concurrency-001`：全文件 `printk` 规则无法定位调用上下文

三组 OpenCode 均在 L0 `no_printk` 被拒绝。本地代码的可见 `printk` 位于消费者线程和 `main()` 演示路径，ISR 函数本身没有打印；但规则全文件搜索 `printk`。因此这项拒绝不能被描述成“已观察到在 ISR 内调用打印”。本地代码仍包含 GPIO 中断配置和环形缓冲并发逻辑，未编译或运行，不能由此证明 ISR 安全。[本地代码](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__isr-concurrency-001__1/8f38f270/workspace/submission/main.c) · [本地评分](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/tasks/opencode__isr-concurrency-001__1/8f38f270/evaluation.json)

## 6. 逐题详细数据

每格为“原始状态；任务秒数；观测总 Token”。通过/失败仅指 L0/L3 规则。`≥` 为错误前的部分用量，“未知”表示无可用用量，均未做人工补分。

| 题号 | Opus 第三方网关 | Qwen OpenRouter | Qwen 本地社区版 |
|---|---|---|---|
| gpio-basic-001 | 通过；32.7s；41,839 | 失败；38.1s；11,248 | 失败；52.8s；11,825 |
| uart-001 | 通过；32.1s；28,120 | 失败；13.9s；15,056 | 失败；69.4s；20,756 |
| spi-i2c-002 | 通过；49.2s；40,279 | 通过；25.5s；23,027 | 失败；42.0s；25,087 |
| spi-i2c-001 | 通过；29.8s；30,604 | 通过；37.1s；14,296 | 通过；124.3s；15,086 |
| timer-002 | 通过；47.2s；45,673 | 接口错误；15.8s；未知 | 失败；168.8s；19,683 |
| threading-001 | 失败；57.0s；60,551 | 失败；63.0s；83,658 | 通过；169.6s；25,738 |
| dma-001 | 通过；76.9s；59,601 | 失败；150.8s；33,965 | 失败；65.4s；22,057 |
| threading-004 | 通过；24.2s；14,035 | 失败；31.3s；39,308 | 失败；130.9s；56,710 |
| dma-003 | 失败；145.0s；61,104 | 接口错误；124.4s；≥19,949 | 失败；165.6s；41,840 |
| isr-concurrency-001 | 失败；154.6s；140,948 | 失败；398.8s；104,335 | 失败；313.1s；153,970 |

## 7. 结论边界与后续验证

这是一份“固定 OpenCode、改变模型接口”的观察报告，但不是完全受控的模型单变量实验。Opus 为第三方远程网关，**不是 Anthropic 官方原生直连**；OpenRouter Qwen 由远程服务路由；社区优化版通过本地接口运行且实际权重身份未独立验证。协议、冻结运行器、后端、网络、硬件、运行日期及默认推理策略不完全一致。每组仅 10 道 Zephyr 题、每题一次，且没有编译或运行验收，原始分数只能表示当前 L0/L3 规则下的结果。

下一步应先保留本次原始记录，再固定三组的 SDK/工程和编译环境，对全部提交统一增加 L1 编译与必要的 L2 行为检查；修订 `while (true)` 等规则漏识别时给评分器单独版本，并用同一新版本对所有组重评。扩大按平台、类别和难度分层的题集，重复多次，记录社区版权重哈希、量化配置、本地引擎与硬件，再讨论能力、速度或部署收益。

## 8. 原始记录与复现文件

- [Opus 原始运行](experiments/2026-10-20-opus5-harness-comparison/runs/run-20261020-154313-c6793e/report.md)、[OpenRouter Qwen 原始运行](experiments/2026-10-20-qwen38-27b-harness-comparison/runs/run-20261020-154440-282906/report.md)、[社区版本地运行](experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11/report.md)。
- [三组 OpenCode 指标 JSON](evaluation/opencode-three-model-results.json)、[逐题 CSV](evaluation/opencode-three-model-results.csv)、[只读重建脚本](evaluation/aggregate_three_model_opencode.py)。这些指标按各题 `result.json`、`evaluation.json` 和 `trace.json` 重建，不改原始评分。
- [固定 10 题清单](experiments/2026-10-20-opus5-harness-comparison/subsets/pilot-10.json)。各 run 目录保留 `config.json`、`frozen-runner.py`、预检记录与逐题产物。

分享本报告时，应连同 `evaluation/`、`experiments/` 中对应证据文件一起分享；相对路径链接离开仓库将无法访问。
