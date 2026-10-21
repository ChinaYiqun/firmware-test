---
title: networking-kernel Phase C-2 baseline benchmark
created: 2026-04-19
status: pending-run
tc_family: networking-kernel-001..005
---

# networking-kernel Phase C-2 — Baseline Benchmark

## Status

**Pending execution.** The 5 new TCs ship green (all references pass 100% of
their own static + behavior checks; all 65 mutations trigger their `must_fail`
targets via `scripts/verify_negatives_oracle.py --category networking`). Phase 5
of `PLAN-linux-networking-kernel-phase-c.md` calls for an n=1 sanity run plus
(if non-degenerate) an n=3 confidence-interval run on Haiku + Sonnet. The run
itself requires either `ANTHROPIC_API_KEY` or a subscription-routed
`claude -p` harness — the latter is not safe to spawn from inside an
executing Claude Code session.

The commands below are the verified invocations. Populate per-TC pass rates
after the run completes.

## Run commands

### n=1 sanity (Haiku + Sonnet)

```bash
uv run embedeval run \
  --cases cases/ \
  --model claude-haiku-4-5-20251001 \
  --category networking --sdk embedded-linux \
  --run-id n1 \
  --output-dir runs/phase-c2-haiku

uv run embedeval run \
  --cases cases/ \
  --model claude-sonnet-4-6 \
  --category networking --sdk embedded-linux \
  --run-id n1 \
  --output-dir runs/phase-c2-sonnet
```

The `--category networking --sdk embedded-linux` intersection selects exactly
the 5 new TCs (the 10 existing `networking` TCs all live under zephyr /
esp-idf / stm32-hal buckets — verified via `cases/SDK_LAYOUT.yaml`).

### n=3 (if n=1 non-degenerate)

Repeat with `--run-id n2` then `--run-id n3` for both models. Degenerate
outcome = all TCs pass or all TCs fail. The softirq-discipline TC (001) and
the sk_buff-lifecycle TC (002) are expected to discriminate most strongly
based on the factor coverage they target.

## Expected discrimination (pre-run hypothesis)

Based on the factor analysis in `PLAN-linux-networking-kernel-phase-c.md`:

| TC                          | Dominant factor      | Hypothesised difficulty  | Hardest check                          |
|-----------------------------|----------------------|---------------------------|-----------------------------------------|
| networking-kernel-001       | D5 softirq context    | Hard — implicit           | `hook_fn_has_softirq_safe_body`         |
| networking-kernel-002       | E2/E3 skb lifecycle   | Hard — implicit           | `worker_uses_consume_skb_on_success`    |
| networking-kernel-003       | E1/E2 netlink cleanup | Hard — implicit           | `netlink_kernel_create_return_null_checked` |
| networking-kernel-004       | F5 struct surface     | Hard — directive-heavy    | `genl_family_has_module_this_module`    |
| networking-kernel-005       | E1/E2 register balance| Medium — simpler pattern  | `callback_returns_notify_ok_or_done`    |

The `consume_skb` vs `kfree_skb` distinction in 002 is the quietest signal —
most LLMs default to `kfree_skb` because it is the more familiar idiom, so
this check is expected to separate models that have seen
dropwatch-instrumented reference modules from those that haven't.

## Fill-in section (populate after run)

```
| TC                    | Haiku n=1 | Haiku n=3 mean ± stdev | Sonnet n=1 | Sonnet n=3 mean ± stdev |
|-----------------------|-----------|------------------------|------------|-------------------------|
| networking-kernel-001 |           |                        |            |                         |
| networking-kernel-002 |           |                        |            |                         |
| networking-kernel-003 |           |                        |            |                         |
| networking-kernel-004 |           |                        |            |                         |
| networking-kernel-005 |           |                        |            |                         |
| Aggregate             |           |                        |            |                         |
```

## Commentary slots

- `hook_fn_has_softirq_safe_body` discriminator direction (TC 001).
- `consume_skb` vs `kfree_skb` distinction (TC 002) — expect this to be the
  single most-frequently-failed check across both models.
- Genl deprecated-API avoidance (TC 004) — does either model default to
  `genl_register_family_with_ops`?
- Netdevice accessor recognition (TC 005) — does either model use
  `netdev_notifier_info_to_dev`, or fall back to direct cast?

## Follow-up

Once numbers land, update:
- `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` — bump to v1.7 with Phase C-1 + C-2
  check-name trailers (mirror commit `959de3d`).
- `memory/MEMORY.md` — TC count 267, Phase C-2 completion note, headline
  pass rates.
