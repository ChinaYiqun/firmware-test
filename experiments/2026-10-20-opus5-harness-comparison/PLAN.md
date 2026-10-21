# 第一期评测计划：OpenCode / Claude Code × claude-opus-5 × EmbedEval

日期：2026-10-20（Asia/Shanghai）  
状态：静态评测环境及初版运行脚本已准备，未启动模型生成或正式评测。本文保留设计目标；当前实现与使用方法以 [README.md](README.md) 为准。

已验证：Python 3.12.9 独立环境、10/10 题参考实现通过 L0/L3、20 个离线模拟任务和无重复断点续跑、超时与密钥脱敏测试、OpenCode 原生配置解析。尚未验证真实网关生成调用。初版使用工具权限限制而非操作系统沙箱；不做外部自动重试；推理参数使用各自默认值；Token/费用保留原始事件，统一汇总暂记未知。上述实现边界取代本文相应的拟定值。

## 1. 本期要回答的问题

通过同一个网关、同一个模型 ID、同一组任务，比较 OpenCode 和 Claude Code 的任务完成效果、耗时与资源消耗。

本期测试的是两个 Agent Harness 的实际执行效果。保留各自内置的系统提示词、上下文管理与工具编排差异；统一用户任务、可访问材料、工具权限范围和外部时间预算。结论属于“网关上的模型 + 指定版本 Harness + 本次配置”的组合，不能直接解释为模型本身的能力差异。

第一期先做 10 题的静态评测试验，不直接跑全量，也不据此宣称完整固件正确率。后续可以原样扩展到公开的 219 道题。

## 2. 当前准备情况

| 项目 | 已核实情况 | 开跑前还需要做什么 |
|---|---|---|
| OpenCode | 本机 `opencode --version` 返回 `1.19.3` | 隔离配置；验证网关、流式响应与文件工具调用 |
| Claude Code | 本机 `claude --version` 返回 `2.1.304` | 隔离配置；验证网关、流式响应与文件工具调用 |
| 网关 | `https://sky.tinyandbeautiful.com`；此前带认证查询 `/v1/models` 成功 | 验证实际 `/v1/messages` 请求 |
| 模型 | 网关列出 `claude-opus-5`，标注支持 Anthropic 接口 | 核对响应模型字段、工具调用和用量字段；实际后端身份无法仅凭列表确认 |
| EmbedEval | 已下载；源码内发现 219 个公开题目 metadata 文件 | 固定源码与题目清单哈希；安装独立评测依赖 |
| 题目清单 | 已有 10 题清单，题目、L0/L3 检查文件均存在 | 预检参考实现及评分器，冻结实验清单 |
| 运行环境 | Windows；Python、Node、Git、uv 可找到 | 文件隔离与任务权限方案待落实；Docker 命令未在 PATH 中发现 |
| 调度与结果库 | 尚未实现 | 实现两个 Harness 适配器、队列、超时、断点续跑和结果落库 |

现有源码：`D:\firmware-test\benchmarks\embedeval-main`。原始 ZIP 仍保留；此前 Windows 解压仅对历史结果目录中的冒号作了替换，题目源码未因此改名。正式实验保存原始 ZIP 与实际使用题目/评分源码的 SHA-256。

密钥不写进本文件、配置样例、命令参数或结果。运行器通过子进程环境注入认证值，日志落盘前脱敏；不读取或修改用户原有的 Harness 登录配置。

## 3. 第一批题目

来源：`D:\firmware-test\evaluation\embedeval-pilot-10.json`。按覆盖面人工选取 3 道简单、4 道中等、3 道困难题，不是随机抽样或代表性排行榜子集。此前 12 题清单保留为历史记录，本次以 pilot-10.json 为准。

| 难度 | 题目 ID | 任务 |
|---|---|---|
| easy | gpio-basic-001 | GPIO 按键中断与 LED 翻转 |
| easy | uart-001 | UART 回显 |
| easy | spi-i2c-002 | SPI 回环 |
| medium | spi-i2c-001 | I2C 寄存器读取与错误处理 |
| medium | timer-002 | 单次定时器提交工作队列 |
| medium | threading-001 | 消息队列生产者/消费者 |
| medium | dma-001 | 内存到内存 DMA |
| hard | threading-004 | 优先级继承互斥锁 |
| hard | dma-003 | DMA 环形缓冲区 |
| hard | isr-concurrency-001 | ISR 安全环形缓冲区 |

正式生成开始前，用评测器对这些题的参考实现跑 L0/L3 健康检查。若参考实现不能通过、评分器报错或检查无法执行，先修复环境并记录；若需修改或替换题目，发布新的清单版本，两个 Harness 使用同一版本，不能依据某个 Harness 的表现选题。

## 4. 统一实验条件

| 参数 | 本期拟定值 |
|---|---|
| 模型 ID | 精确固定为 `claude-opus-5`，不使用 `opus` 等别名 |
| 接口协议 | 两侧都使用 Anthropic Messages，经同一网关 |
| 每题输入 | 原始 `prompt.md` + 完全相同的产物提交说明 |
| 产物 | 任务目录内 `submission/main.c`，以文件内容为评分输入 |
| 场景 | generation；本期不做 bugfix |
| 外部评分反馈轮数 | 0；结束后评分，不把隐藏检查失败反馈给 Agent |
| Agent 内部工具交互 | 允许在限时内阅读题目和编写、修改提交文件；统计调用次数 |
| 外部单任务时限 | 600 秒，包含 Harness 启动与 API 等待，排队时间另记 |
| 全局任务并发 | 初始 2；预检通过后最多 4，并记录在实验配置中 |
| 同 Harness 并发 | 初始最多 1，各 Harness 交错运行；升到全局 4 后各最多 2 |
| 评分并发 | 初始 1，避免评分耗时与资源争抢混入 Agent 耗时 |
| 网络重试 | 对明确的限流/连接失败最多 2 次，退避等待计入任务总时限 |
| 自动模型降级 | 禁止，失败时不切换到其他模型或供应商 |
| 重复次数 | 首轮每组合 1 次；扩展后每组合总计 3 次，独立新会话 |
| 扩展、记忆、MCP | 禁用外部插件、用户记忆、用户规则、额外 MCP 和跨题会话继承 |
| 工具权限 | 仅任务文件读取、搜索与写入；首轮不开放任意 Shell 或网页搜索 |

原始 prompt 常要求“只输出 C 源码”。统一补充说明仅将提交方式改为写入 `submission/main.c`，不补充解题知识、不改任务要求。保存原始 prompt 和最终投递 prompt；报告注明这个 Agent 适配，不能直接等同于原项目单次文本生成设置。

两个 Harness 的内置工具实现不同，本实验按能力范围对齐，不宣称逐 token 或逐工具完全一致。首轮不开放 Shell，因此测到的是文件工具驱动的代码生成效果，尚不涵盖完整编译调试 Agent 能力。

温度、推理档位、输出上限及上下文上限先在网关兼容性检查中确认。能显式共同设置的参数冻结为相同值；不能对齐的参数逐项记录其“默认 / 未知 / 不支持”状态，不能写成已经相同。若因此影响比较，将实验标记为“各自默认策略比较”，在报告中列出差异。

参考答案、评分脚本和其他任务结果只对评分进程可见。Agent 子进程不能仅靠不同工作目录隔离：开跑前落实可验证的文件访问限制，并用探针检查不能读取题库参考答案或其他运行目录；隔离验证失败则不发布正式对比分数。两侧允许访问相同的文件集合。

## 5. API 与 Harness 配置方案（待预检冻结）

统一抽象配置如下；这是评测框架配置草案，不是可直接传给两个 CLI 的原生配置。

```yaml
experiment: opus5-opencode-vs-claude-code-embedeval-pilot-v1
provider:
  protocol: anthropic-messages
  base_url: https://sky.tinyandbeautiful.com
  token_env: BENCH_ANTHROPIC_TOKEN
  model: claude-opus-5
harnesses:
  - id: opencode
    version: 1.19.3
  - id: claude-code
    version: 2.1.304
benchmark:
  id: embedeval
  subset: subsets/pilot-10.json
  scenario: generation
  scoring: L0+L3
  feedback_rounds: 0
execution:
  concurrency: 2
  per_harness_concurrency: 1
  repetitions: 1
  timeout_seconds: 600
  transport_retries: 2
```

- OpenCode：使用 Anthropic 协议 provider，设置网关地址与环境变量认证；用 `opencode run --format json --pure` 收集事件，模型绑定到精确 ID。最终 provider 配置、认证头与 `/v1` 拼接规则以预检结果为准。
- Claude Code：使用 `claude -p --model claude-opus-5`，配结构化输出与实验专用 settings。拟注入 `ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`，验证请求确实走指定网关，且无订阅登录或其他供应商回退。
- Claude Code 当前 `--bare` 模式的帮助说明要求 `ANTHROPIC_API_KEY` 或 apiKeyHelper，不能假定现有 AUTH_TOKEN 在 bare 模式下直接可用。预检先确认网关是否接受对应的认证方式，再决定采用 bare 或隔离后的非 bare 模式，记录最终选择。
- 任何辅助/小模型请求也必须使用同一个指定模型，或禁用；检查响应/事件中的模型清单。若发现其他模型调用，标记配置不符合实验条件，修正后重新预检。
- 不硬套 EmbedEval 自带的 `agent` 命令：该命令自身负责模型调用与评分反馈，本期由实际 OpenCode / Claude Code 执行任务，完成后再调用 EmbedEval 评分器。
- CLI 参数模板尚未完成执行验证；正式运行保存实际 argv（脱敏）、配置快照及配置哈希。

## 6. 执行阶段与任务数量

### A. 本地准备及健康检查

建立独立评测依赖环境；固定源码、题目清单和配置；实现适配器、并发调度与结果库；验证产物解析、超时杀进程树、断点恢复、文件隔离与日志脱敏。对参考实现做评分健康检查。

### B. 网关和工具调用预检

每个 Harness 运行 1 个不含 benchmark 题目的微型任务，例如创建一个指定内容的小文件。核对 Messages 认证、工具调用、流式结束事件、实际模型、文件产物和用量记录。

预计 2 个预检任务，不计入 benchmark 分数。若网关不兼容工具调用、模型不可用或隔离不成立，暂停正式任务，保留诊断结果。

### C. 10 题首轮

10 题 × 2 Harness × 1 次 = **20 个计分任务**。各任务独立会话、独立目录。按固定种子打乱题目顺序，并交错运行两个 Harness，减少网关不同时段负载的影响。先出逐题结果和初步报告。

### D. 重复实验（首轮通过后再安排）

每个组合补 2 次，共新增 **40 个计分任务**，累计 **60 个计分任务**。只有 C、D 的题目、配置、版本和评分哈希完全一致时才合并；如有变化，保留 C 的结果，另开实验 ID，不能直接拼接统计。

### E. 后续扩展（不包含在本次试跑范围）

公开全量 219 题 × 2 Harness × 3 次 = 1,314 个计分任务。编译/仿真另开实验版本，补齐 SDK、构建和沙箱环境后再安排。48 道私有题目前无法本地获取，不在范围内。

## 7. 评分和失败口径

第一期主指标：**L0 + L3 静态评测通过率**。L0 是静态规则检查，L3 是领域启发式检查；两者都不是实际硬件行为验证。本期明确禁用 L1 编译和 L2 运行，并在报告写为“未评测”，不显示为通过。L4 用于检查评分规则质量，不计入 Agent 主通过率。

尊重原评分器遇到前层失败就停止的行为：L0 失败时 L3 标为未执行。原有规则可能对变量命名或等价写法敏感；保留原始官方评分，单列人工复核疑似误判，不通过静默改规则提升分数。评分规则修订必须生成新实验版本。

分别报告以下状态：

- `scored_pass` / `scored_fail`：已产出可评分代码，并完成评分。
- `no_submission`：正常结束但缺失/空白提交；计入端到端失败。
- `timeout`：达到任务外部时限，保留部分产物与轨迹；主指标计失败，不能拿部分产物替代正式完成。
- `infra_error`：认证、限流耗尽、网关、Harness 启动等基础设施错误；单列，不伪装为代码错误。
- `evaluator_error`：评分进程或规则执行异常；暂停排查，不当作 Agent 生成错误。
- `cancelled` / `pending`：未完整执行，不用于已完成任务能力比较。

报告同时列出计划总数、实际完成数和覆盖率。试验批次完成后，端到端成功率以该批次所有计划计分任务为分母，基础设施失败保留在其中；代码评分通过率只以完成评分的任务为分母，并同时展示分母与 infra_error 数量。未完成批次的任何比率标记为临时结果。

重复 3 次时报告每次通过率、每题 0/3 至 3/3 稳定性、两个 Harness 的逐题差异。10 个独立题目不足以支持强显著性结论，不能把重复运行当成 30 道独立题目。单次轨迹内部多轮工具交互仍属于一个 Agent 尝试，不当成多个 pass@k 样本。

## 8. 结果保存什么

SQLite 保存结构化索引，单一写入器落库；每个任务的原始文件单独保存。任务启动、进度和终态均及时持久化，中断后把遗留 running 状态标为 interrupted。恢复时只调度未完成任务；重跑创建新的 attempt 记录，不覆盖旧轨迹，不重复累计成功任务。

| 记录类型 | 字段/内容 |
|---|---|
| 实验身份 | experiment_id、run_id、case_id、harness、model、repeat_index、attempt_id |
| 可复现条件 | CLI 版本、系统/依赖版本、源码/题目/配置哈希、随机种子、实际权限及参数 |
| 运行状态 | 排队/开始/结束时间（UTC 原值、报告显示上海时间）、退出码、状态、重试原因 |
| 时间 | 排队、Agent、评分、重试等待、总耗时；报告 median 与 p95 |
| 评分 | L0/L3 各检查明细、未执行原因、总体通过状态、失败分类 |
| 模型响应 | 请求模型、返回模型、实际出现的辅助模型、请求 ID（可获得时） |
| 开销 | 输入/输出/cache/reasoning token（能获得的字段）、工具调用数、模型调用数 |
| 费用 | Harness 估算、网关账单值分别存储；来源不明或缺失记 unknown，不填零 |
| 产物与轨迹 | 最终 C 文件、文件哈希、投递 prompt、CLI JSON 事件、stdout/stderr、脱敏日志 |

不保存认证头或完整环境变量。Harness 无法暴露的请求字段不宣称已记录。第三方网关价格可能与 CLI 内置估价不同；目前无定价依据，本计划不填写预计金额。

最终报告包含：两个 Harness 总览对比表、逐题胜负表、按难度/类别统计、失败原因、速度/用量、基础设施可靠性、疑似评分误判及方法限制。导出 `report.md`、`summary.json` 和 `tasks.csv`。

## 9. 独立目录布局

本期目录：`D:\firmware-test\experiments\2026-10-20-opus5-harness-comparison`。

```text
2026-10-20-opus5-harness-comparison/
  PLAN.md                       # 当前已创建：本计划
  subsets/pilot-10.json          # 当前已创建：题目清单副本
  preparation.json              # 当前已创建：本地版本与源码校验记录
  configs/                      # 以下为后续拟创建内容
    experiment.yaml
    opencode.json
    claude-settings.json
  results.sqlite
  runs/<run-id>/
    frozen-config.json
    environment.json
    tasks/<harness>/<case-id>/<repeat>/<attempt>/
      prompt.md
      workspace/submission/main.c
      trace.jsonl
      stdout.log
      stderr.log
      evaluation.json
      result.json
    report.md
    summary.json
    tasks.csv
```

Agent 实际执行目录应位于受限环境内，仅收集后的产物归档到上述目录；不能让 Agent 访问包含其他任务答案的 results 根目录。

## 10. 时间估算

以下为规划值，尚无该网关 `claude-opus-5` 的实测延迟。假设单任务平均 2–6 分钟、全局并发 2、整体额外开销约 20%。B 阶段后按实际耗时更新，重试等待已包含在单任务时限内。

| 阶段 | 预计时间 | 说明 |
|---|---|---|
| A：框架实现、隔离与本地验证 | 2–4 小时 | 一次性开发估算；Windows 隔离若需新环境，另行估时 |
| B：两侧网关/工具预检 | 5–15 分钟 | 不含发现兼容性问题后的修复 |
| C：20 个任务首轮 | 25–75 分钟 | 运行阶段墙钟时间 |
| D：新增 40 个任务 | 50–150 分钟 | 运行阶段墙钟时间 |
| C+D：累计 60 个任务 | 75–225 分钟 | 约 1.25–3.75 小时，不再与 C/D 相加 |
| 汇总与失败抽查 | 20–40 分钟 | 人工复核量较大时延长 |

如果每个任务都耗尽 600 秒，60 个任务在并发 2 时仅任务运行就约 5 小时，另加调度/评测开销。并发 4 理想情况下接近减半，但网关限流或排队可能抵消收益。实现及隔离工作不计入模型执行耗时。

## 11. 计划审阅后的执行顺序

1. 按本计划实现最小运行器和两个适配器，准备独立依赖与权限隔离。
2. 完成无模型的本地预检，再做 2 个微型 API/工具任务，冻结所有实际参数。
3. 运行 20 个首轮计分任务，提交第一份对比报告。
4. 根据首轮基础设施与评分健康情况，安排补足 3 次重复；全量题库与编译/仿真作为后续独立范围。

当前没有真实 benchmark 测试结果；版本检查与模型列表查询不能替代任务评测。

## 12. 参考依据

- [OpenCode 官方文档](https://opencode.ai/docs/) 与 [Provider 配置](https://opencode.ai/docs/providers/)；CLI 版本和 run 参数以本机检查为准。
- [Claude Code 非交互执行](https://code.claude.com/docs/en/headless) 与 [网关说明](https://code.claude.com/docs/en/llm-gateway)；bare 模式认证限制同时参考本机 2.1.304 的帮助输出。
- [EmbedEval 项目说明](https://github.com/Ecro/embedeval)；实际题目数与评分层行为以本地下载源码为准。
