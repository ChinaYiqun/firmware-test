"""Fill report tables from reconstructed metrics; narrative/manual review stays intact."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "evaluation/merged-results.json").read_text(encoding="utf-8"))
REPORT = ROOT / "FIRMWARE_BENCHMARK_REPORT.md"
LABELS = {"opus": "Opus（第三方网关）", "qwen": "Qwen（OpenRouter）"}
HL = {"opencode": "OpenCode", "claude-code": "Claude Code"}
SUBSET = json.loads((ROOT / "experiments/2026-10-20-opus5-harness-comparison/subsets/pilot-10.json").read_text(encoding="utf-8"))["cases"]
ROWS = DATA["tasks"]


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)] +
                     ["| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in row) + " |" for row in rows])


def block(text, key, value):
    pattern = rf"(<!-- {key}_START -->).*?(<!-- {key}_END -->)"
    updated, count = re.subn(pattern, lambda m: m[1] + "\n" + value + "\n" + m[2], text, flags=re.S)
    assert count == 1, key
    return updated


def main():
    text = REPORT.read_text(encoding="utf-8")
    groups = DATA["groups"]
    scores = table(["模型 / 接口", "Harness", "通过 / 计划", "端到端成功率", "通过 / 已评分", "L0通过 / 已评分", "L3通过 / 已执行", "超时", "接口错误"], [
        [LABELS[g["model_group"]], HL[g["harness"]], f"{g['passed']}/10", f"{g['passed']/10:.0%}",
         f"{g['passed']}/{g['scored']}（{g['passed']/g['scored']:.1%}）", f"{g['l0_passed']}/{g['scored']}",
         f"{g['l3_passed']}/{g['l3_evaluated']}", g["status_counts"].get("timeout", 0),
         g["status_counts"].get("infra_error", 0)] for g in groups])
    scores += "\n\n按难度计算的端到端通过数（分母包含超时和接口错误）：\n\n"
    scores += table(["模型", "Harness", "简单", "中等", "困难"], [
        [LABELS[g["model_group"]], HL[g["harness"]]] + [
            f"{sum(r['passed'] for r in ROWS if r['model_group']==g['model_group'] and r['harness']==g['harness'] and r['case_id'] in {c['id'] for c in SUBSET if c['difficulty']==difficulty})}/{sum(c['difficulty']==difficulty for c in SUBSET)}"
            for difficulty in ["easy", "medium", "hard"]] for g in groups])
    text = block(text, "SCORES", scores)
    text = block(text, "TIMES", table(["模型", "Harness", "10题累加秒", "平均秒/题", "中位秒/题", "P95秒", "最长秒"], [
        [LABELS[g["model_group"]], HL[g["harness"]]] + [f"{g[key]:.1f}" for key in ["sum_seconds", "mean_seconds", "median_seconds", "p95_seconds", "max_seconds"]] for g in groups]))
    text = block(text, "WALL", table(["批次", "正式任务起始（上海时间）", "结束（上海时间）", "实测墙钟"], [
        [LABELS[m], b["started_shanghai"][11:19], b["ended_shanghai"][11:19],
         f"{int(b['batch_wall_seconds']//60)} 分 {b['batch_wall_seconds']%60:.1f} 秒"] for m,b in DATA["batches"].items()]))
    text = block(text, "TOKENS", table(["模型", "Harness", "非缓存输入", "缓存读", "输出含推理", "其中单列推理", "观测总Token", "用量覆盖", "工具调用"], [
        [LABELS[g["model_group"]], HL[g["harness"]]] + [
            ("≥ " if g["usage_coverage"].get("partial") or g["usage_coverage"].get("unknown") else "") + f"{g['usage_sums'][key]:,}"
            for key in ["observed_input", "observed_cache_read", "observed_output_including_reasoning", "observed_reasoning", "observed_total"]] +
        ["；".join(f"{n}题{dict(complete='完整',partial='部分',unknown='未知')[status]}" for status,n in g["usage_coverage"].items()), g["tool_calls"]]
        for g in groups]) + "\n\n缓存写入：四组已记录值均为 0；Qwen 未知用量仍未知。")
    status_labels = {"scored_pass":"通过", "scored_fail":"失败", "timeout":"超时", "infra_error":"接口错误"}
    index = {(r["model_group"],r["harness"],r["case_id"]):r for r in ROWS}
    keys = [("opus","opencode"),("opus","claude-code"),("qwen","opencode"),("qwen","claude-code")]
    detail_rows = []
    for case in SUBSET:
        cells = [case["id"]]
        for model,harness in keys:
            r = index[model,harness,case["id"]]
            tok = "未知" if r["observed_total"] is None else ("≥" if r["coverage"] == "partial" else "") + f"{r['observed_total']:,}"
            cells.append(f"{status_labels[r['status']]}；{r['seconds']:.1f}s；{tok}")
        detail_rows.append(cells)
    text = block(text, "DETAILS", table(["题号", "Opus / OpenCode", "Opus / Claude Code", "Qwen / OpenCode", "Qwen / Claude Code"], detail_rows))
    failure_rows=[]
    for case in SUBSET:
        for model,harness in keys:
            r=index[model,harness,case['id']]
            if r['passed']:continue
            checks='；'.join(f"L{f['layer']}: `{f['check']}`" for f in r['failed_checks'])
            if r['status']=='infra_error':checks='TLS：unknown certificate verification error'
            if r['status']=='timeout':checks='600 秒时限；未完成评分'
            link=r['artifact_directory']+('/evaluation.json' if r['failed_checks'] else '/result.json')
            failure_rows.append([case['id'],LABELS[model]+' / '+HL[harness],status_labels[r['status']],checks,f"[记录]({link})"])
    text=block(text,'FAILURES',table(['题号','组合','状态','原始拒绝/异常原因','来源'],failure_rows))
    for marker,cid in [('DMA','dma-001'),('GPIO','gpio-basic-001'),('UART','uart-001'),('MUTEX','threading-004'),('QUEUE','threading-001'),('ISR','isr-concurrency-001')]:
        r=index['qwen','opencode',cid]
        folder=r['artifact_directory']
        links=f"[生成代码]({folder}/workspace/submission/main.c) · [评分明细]({folder}/evaluation.json) · [执行记录]({folder}/result.json)"
        text=text.replace(f'<!-- BAD_{marker}_LINK -->',links)
    links=' · '.join(f"[{cid} 执行记录]({index['qwen','opencode',cid]['artifact_directory']}/result.json)" for cid in ['dma-003','timer-002'])
    text=text.replace('<!-- BAD_INFRA_LINKS -->',links)
    assert not re.search(r'<!-- BAD_\w+_LINK',text)
    REPORT.write_text(text,encoding='utf-8')
    print('Merged report tables rendered from 40 original task records.')


if __name__ == '__main__':
    main()
