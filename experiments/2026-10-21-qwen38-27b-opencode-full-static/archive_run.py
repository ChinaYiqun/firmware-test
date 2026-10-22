"""Publish compact, credential-free results; keep raw task artifacts local."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import statistics


def archive(run):
    config = json.loads((run / "config.json").read_text(encoding="utf-8"))
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in config["cases"]}
    attempts = []
    for path in (run / "tasks").glob("*/*/result.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        row = {key: raw[key] for key in (
            "case_id", "attempt_id", "harness", "model", "status", "passed",
            "started_at", "ended_at", "duration_seconds", "exit_code",
            "submission_sha256", "tokens",
        ) if key in raw}
        row["local_artifact_directory"] = path.parent.relative_to(run).as_posix()
        row.update({key: cases[row["case_id"]][key] for key in ("sdk", "difficulty", "category")})
        evaluation_path = path.parent / "evaluation.json"
        if evaluation_path.is_file():
            evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
            row["evaluation"] = {
                "scope": evaluation["scope"], "passed": evaluation["passed"],
                "layers": [{"layer": layer["layer"], "passed": layer["passed"],
                            "checks": [{"name": check["check_name"], "passed": check["passed"]}
                                       for check in layer["details"]]}
                           for layer in evaluation["layers"]],
            }
        attempts.append(row)
    attempts.sort(key=lambda row: (row["started_at"], row["attempt_id"]))
    latest = {row["case_id"]: row for row in attempts}
    rows = [latest[case_id] for case_id in cases]
    assert len(rows) == summary["finished"] == summary["planned"]
    assert dict(Counter(row["status"] for row in rows)) == summary["status_counts"]
    assert sum(row["tokens"]["total"] or 0 for row in rows) == summary["observed_tokens"]
    for row in attempts:
        row["is_latest_attempt"] = row is latest[row["case_id"]]
    tz = timezone(timedelta(hours=8))
    start = min(datetime.fromisoformat(row["started_at"]) for row in attempts).astimezone(tz)
    end = max(datetime.fromisoformat(row["ended_at"]) for row in rows).astimezone(tz)
    seconds = [row["duration_seconds"] for row in rows]
    metrics = {
        "started_at_beijing": start.isoformat(), "ended_at_beijing": end.isoformat(),
        "elapsed_span_seconds_including_interruption": (end - start).total_seconds(),
        "latest_task_duration_sum_seconds": round(sum(seconds), 3),
        "mean_task_seconds": round(statistics.mean(seconds), 3),
        "median_task_seconds": round(statistics.median(seconds), 3),
        "attempt_count": len(attempts), "case_count": len(rows),
    }
    payload = {"summary": summary, "timing": metrics, "attempts": attempts}
    (run / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# OpenRouter Qwen 27B / OpenCode：219 题全量静态评测", "",
        f"模型 ID：`{config['model']}`；实际接口：`{config['base_url']}/v1/messages`（Anthropic Messages 兼容协议）。",
        f"OpenCode `{config['opencode_version']}`，并发 {config['concurrency']}，每题 {config['timeout_seconds']} 秒，每题一次；只评 L0/L3，未做 SDK 编译或硬件运行。", "",
        f"运行区间（北京时间）：{start:%Y-%m-%d %H:%M:%S} 至 {end:%Y-%m-%d %H:%M:%S}。中间发生中断后续跑，该跨度包含停机时间，不能视为连续执行耗时。", "",
        "| 指标 | 结果 |", "|---|---:|",
        f"| 已结束 / 计划题数 | {summary['finished']}/{summary['planned']} |",
        f"| 通过 / 计划（端到端成功率） | {summary['passed']}/{summary['planned']}（{100 * summary['passed'] / summary['planned']:.2f}%） |",
        f"| 通过 / 已评分 | {summary['passed']}/{summary['scored']}（{100 * summary['passed'] / summary['scored']:.2f}%） |",
        f"| 评分失败 / 超时 / 无提交 | {summary['status_counts']['scored_fail']} / {summary['status_counts']['timeout']} / {summary['status_counts']['no_submission']} |",
        f"| 最新每题耗时累加 | {sum(seconds):.3f} 秒 |",
        f"| 平均 / 中位每题耗时 | {statistics.mean(seconds):.3f} / {statistics.median(seconds):.3f} 秒 |",
        f"| 观测 Token 总量 | {summary['observed_tokens']:,} |",
        f"| 用量记录完整 / 部分 / 未知 | {summary['usage_coverage']['complete']} / {summary['usage_coverage']['partial']} / {summary['usage_coverage']['unknown']} |",
        f"| 尝试记录数（含中断记录） | {len(attempts)} |", "",
        "Token 为 CLI 事件累计，含输入、缓存及输出（含推理），存在不完整用量；不能当作准确账单，费用未知。耗时累加采用每题最新尝试，不等于并发后的墙钟时间，也不含被中断尝试的完整耗时。", "",
        "请求参数沿用 OpenCode 默认值；本次未显式指定 temperature、top_p、top_k 或思考开关。不能将本轮与显式 temperature=0、关闭 thinking、不同输出预算及协议适配的本地 FP8 实验视为严格受控的模型对比。模型身份按请求 ID 记录，未独立验证 OpenRouter 后端权重。", "",
        "## 逐题结果", "",
        f"完整的 {len(rows)} 题最新结果、{len(attempts)} 条尝试元数据及静态检查通过/失败明细见 [results.json](results.json)。下表采用每题最新尝试。原始日志、提交、数据库和工作区仅保存在运行电脑；JSON 中的 local_artifact_directory 是本地路径，不是仓库链接。", "",
        "| 题号 | SDK | 难度 | 状态 | 秒 | 观测 Token |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in rows:
        total = row["tokens"]["total"]
        token_text = "未知" if total is None else str(total)
        if row["tokens"]["coverage"] == "partial" and total is not None:
            token_text = f"≥{total}"
        lines.append(f"| {row['case_id']} | {row['sdk']} | {row['difficulty']} | {row['status']} | {row['duration_seconds']:.3f} | {token_text} |")
    (run / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    archive(parser.parse_args().run)
