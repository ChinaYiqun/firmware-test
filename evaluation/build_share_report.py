"""Build the requested share edition without altering the original report/data."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "FIRMWARE_BENCHMARK_REPORT.md"
TARGET = ROOT / "FIRMWARE_BENCHMARK_REPORT_SHARE.md"


def main():
    original = SOURCE.read_text(encoding="utf-8")

    def section(n):
        match = re.search(rf"^## {n}\. .*?(?=^## \d+\. |\Z)", original, re.M | re.S)
        assert match, n
        return match.group(0).strip()

    def block(key):
        match = re.search(rf"<!-- {key}_START -->\s*(.*?)\s*<!-- {key}_END -->", original, re.S)
        assert match, key
        return match.group(1).strip()

    def table_from(text, prefix):
        lines = text.splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
        end = start
        while end < len(lines) and lines[end].startswith("|"):
            end += 1
        return "\n".join(lines[start:end])

    dataset = section(1)
    platform_table = table_from(dataset, "| 本地公开题维度")
    cases_table = table_from(dataset, "| 题号")
    scores, difficulty = block("SCORES").split("按难度计算的端到端通过数（分母包含超时和接口错误）：", 1)
    scores = scores.strip()
    # Tags stay inside the core comparison table; full URLs move to the appendix.
    scores = scores.replace("Opus（第三方网关）", "`claude-opus-5` · `云端` `第三方网关·非原生`")
    scores = scores.replace("Qwen（OpenRouter）", '<span style="color:#f59e0b;font-weight:700"><strong>qwen/qwen3.8-27b</strong></span> · `模拟本地` `OpenRouter`')
    scores = scores.replace("| OpenCode |", '| <span style="color:#22d3ee;font-weight:700"><strong>OpenCode</strong></span> |')
    practice = section(2).split("\n", 1)[1].strip()
    bad = section(9).split("\n", 1)[1].strip()
    bad = re.sub(r"^### 9\.(\d+)", r"### 5.\1", bad, flags=re.M)
    settings = section(4).split("\n", 1)[1].strip()
    scoring = section(5).split("### 5.1 评分口径", 1)[1].split("<!-- SCORES_START -->", 1)[0].strip()
    notes = section(7).split("\n", 1)[1].strip()
    sources = section(8).split("\n", 1)[1].strip()
    sources = sources.replace("将重建指标填入本文的数据表", "将重建指标填入原合并报告的数据表")
    token_notes = section(5).split("### 5.3 Token 与工具交互", 1)[1].split("<!-- TOKENS_START -->", 1)[0].strip()
    token_caveats = section(5).split("<!-- TOKENS_END -->", 1)[1].strip()

    text = f"""# 固件代码生成评测：Claude Code 与 OpenCode 对比

评测日期：2026-10-20。使用同一组 10 道 EmbedEval 任务，对比 OpenCode 1.19.3 与 Claude Code 2.1.304，分别调用 Opus、Qwen 两组远程模型接口。共执行 **40 个任务**，每个组合运行 1 次。

## 1. 测试集与抽样范围

[EmbedEval](https://github.com/Ecro/embedeval) 面向 LLM 生成嵌入式固件，检查模型是否知道中断安全、外设 API、线程同步、DMA、设备树及构建配置等领域约束。每题通常包含需求 `prompt.md`、题目元数据、参考实现以及自动评分脚本。

项目标称总数为 **267 题：219 题公开、48 题私有保留**。本地实际逐个统计到 219 个公开题目元数据文件，私有题未获取。本报告的公开题统计以本地冻结源码为准。

从公开题中人工选取 **10/219 ≈ 4.6%**，简单 3、中等 4、困难 3，覆盖 7 个任务类别。本次执行 **L0 + L3 静态检查**，未验证编译和硬件运行。题目均为 Zephyr，属于场景覆盖试跑，不是全数据集的随机代表性抽样。

## 2. 核心结果

模型接口来源以标签标注：Opus 经第三方网关，并非直连 Anthropic 官方原生 API；Qwen 标为“模拟本地”，实际通过 OpenRouter 远程接口调用，未进行本地部署或本地推理性能测量。

{scores}

端到端成功率以计划的 10 题为分母；“通过 / 已评分”只统计实际完成静态评分的提交。表中保留异常数量，详细计量口径和接口地址见后文。

| 对比范围 | OpenCode | Claude Code | 主要结论 |
|---|---|---|---|
| Opus：全部 10 题 | 7/10 | 7/10 | 逐题通过/失败集合完全相同；Claude Code 的平均耗时和记录 Token 更少 |
| Qwen：全部 10 题 | 2/10 | 3/10 | 端到端成功数相差 1 题；OpenCode 有 2 次 TLS 证书错误，需与代码问题区分 |
| Qwen：两侧都完成评分的共同 7 题 | 2/7 | 2/7 | 逐题结果一致；多通过的 timer-002 在 OpenCode 侧是接口错误，不能据此判断解题能力胜出 |

上述结论仅适用于本次小样本、单次执行和默认推理策略，不作通用 Harness 排名。部分失败存在等价代码写法被评分规则漏识别的情况，原始分数未作人工调整，案例见第 5 节。

## 3. 执行时间与 Token 对比

### 3.1 执行时间

{block('TIMES')}

单位为秒。任务耗时包含 CLI 启动、模型等待、工具交互及内部重试，不含排队、预检和评分；累加秒数不是并发墙钟时间。统计保留全部任务的实际耗时。

Opus 上，Claude Code 平均耗时低约 **28.8%**，但中位数几乎相同（47.8 秒与 48.2 秒），差异主要体现在慢任务尾部。Qwen 的均值受长任务与接口异常影响，不直接等于模型推理速度。

两组正式任务的实测批次墙钟：

{block('WALL')}

两组重叠执行，从最早正式任务到最晚结束共约 **28 分 29 秒**；不含环境准备与预检。

### 3.2 Token 与工具调用

{block('TOKENS')}

Token 总量按非缓存输入、缓存读/写和含推理输出合计；多轮上下文会被重复计量。`≥` 表示已观测下限，未知用量没有按零处理。

Opus 两侧用量记录完整，Claude Code 总 Token 比 OpenCode 少约 **48.3%**。Qwen 两侧存在不完整记录，不据此计算完整预算或精确性价比。所有 Token 均来自网关/CLI 返回值，未经账单独立对账；详细口径见第 6 节。

## 4. 如何更贴近实际 firmware 开发

{practice}

## 5. Qwen / OpenCode 的代表性 bad case

{bad}

## 6. 补充说明

### 6.1 公开题目分布

{platform_table}

Embedded Linux 归组包含 Linux 驱动、用户态、Yocto 等任务；上述 SDK 数量按题目 metadata 统计，并非声称全部任务都具有可用的编译或硬件运行测试。

### 6.2 评分分层与统计口径

评分分层如下：L0 静态规则、L1 SDK 编译、L2 运行/仿真、L3 领域启发式检查、L4 检查规则的变异测试。本次只执行 **L0 + L3**，L0 失败后不再执行 L3；L1/L2 明确未评测，L4 不计模型主分数。部分名为 behavior 的检查仍是代码模式匹配，不能当成真实行为测试。

{scoring}

P95 使用 `(n-1)×0.95` 位置的线性插值，10 个样本下仅作描述。批次墙钟包含正式任务的排队等待，不含预检和环境准备。

### 6.3 本次 10 题清单

{cases_table}

题目元数据的 SDK 版本为 Zephyr 4.1.0，未覆盖 ESP-IDF、STM32、Linux 或 Yocto。公开题中困难题占 48.9%，本子集中占 30%，不能把本次分数外推到全部题目。运行前，10 题参考实现均通过 L0/L3 健康检查，但这不证明评分器接受所有等价正确实现。

### 6.4 按难度统计

分母包含该难度中计划执行的全部题目。

{difficulty.strip()}

### 6.5 接口与实验配置

{settings}

### 6.6 Token 计量与费用边界

{token_notes}

{token_caveats}

### 6.7 结论边界与后续验证

{notes}

### 6.8 原始记录与复现文件

本分享版只重排和精简展示，未改变评分、耗时、用量或原始记录。所有本地证据链接均使用相对路径；对外转发时如需访问证据，应连同对应的 evaluation/ 与 experiments/ 文件一并分享。

{sources}

## 7. 逐题详细数据

每格：`状态；秒；观测总 Token`。通过/失败均指原 L0/L3 规则。`≥` 是失败前已记录的部分用量，`未知` 是缺少可结算用量，不是 0。

{block('DETAILS')}

### 原始失败检查明细

以下保留原始 check 名称；它表示规则拒绝原因，不一定等于已经确认的语义缺陷。

{block('FAILURES')}
"""
    # Avoid editor-specific resource URLs in the file being shared.
    assert 'vscode-resource' not in text
    TARGET.write_text(text, encoding="utf-8")
    print(TARGET)


if __name__ == '__main__':
    main()
