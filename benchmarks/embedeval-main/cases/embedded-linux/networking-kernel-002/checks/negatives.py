"""Negative tests for networking-kernel-002 (sk_buff lifecycle).

Reference: cases/embedded-linux/networking-kernel-002/reference/main.c
Checks:    cases/embedded-linux/networking-kernel-002/checks/{static,behavior}.py
"""

import re


def _swap_skb_clone_to_gfp_kernel(code: str) -> str:
    """Use GFP_KERNEL in skb_clone — may sleep from softirq producer."""
    return re.sub(
        r"skb_clone\s*\(\s*skb\s*,\s*GFP_ATOMIC\s*\)",
        "skb_clone(skb, GFP_KERNEL)",
        code,
        count=1,
    )


def _drop_null_guard_after_clone(code: str) -> str:
    """Remove the NULL guard after skb_clone — NULL deref on allocation
    failure."""
    return re.sub(
        r"\n\s*if\s*\(\s*!\s*clone\s*\)\s*\n[^\n]*return\s*;\s*\n",
        "\n",
        code,
        count=1,
    )


def _swap_consume_skb_to_kfree_skb(code: str) -> str:
    """Use kfree_skb on the success path — wrong free fn; dropwatch
    flags every consumed packet as a drop."""
    return code.replace("consume_skb(skb);", "kfree_skb(skb);")


def _drop_skb_queue_head_init(code: str) -> str:
    """Skip skb_queue_head_init in init — first enqueue corrupts.

    Matches the init call regardless of which variable name the
    reference uses for the sk_buff_head."""
    return re.sub(
        r"\n[^\n]*skb_queue_head_init\s*\([^;]*\);\s*",
        "\n",
        code,
        count=1,
    )


def _drop_skb_queue_tail(code: str) -> str:
    """Remove skb_queue_tail — cloned skb leaks."""
    return re.sub(
        r"\n\s*skb_queue_tail\s*\([^;]*\);\s*",
        "\n",
        code,
        count=1,
    )


def _drop_skb_dequeue(code: str) -> str:
    """Remove skb_dequeue from worker — queue grows unbounded."""
    # Remove the while loop line wholesale.
    return re.sub(
        r"\n\s*while\s*\([^{]*skb_dequeue[^{]*\)\s*\{[^}]*\}",
        "\n",
        code,
        count=1,
    )


def _drop_skb_queue_purge(code: str) -> str:
    """Exit does not drain queue — leaks every queued skb on unload."""
    return re.sub(
        r"\n\s*skb_queue_purge\s*\([^;]*\);\s*",
        "\n",
        code,
        count=1,
    )


def _swap_cancel_and_purge(code: str) -> str:
    """Purge then cancel — worker races on purged queue during shutdown.

    Extracts the work_struct and sk_buff_head identifiers from their
    declarations so the swap doesn't depend on the reference's exact
    variable naming."""
    work = re.search(r"\bstruct\s+work_struct\s+(\w+)\s*;", code)
    head = re.search(r"\bstruct\s+sk_buff_head\s+(\w+)\s*;", code)
    if not (work and head):
        return code
    wn = re.escape(work.group(1))
    hn = re.escape(head.group(1))
    return re.sub(
        rf"(cancel_work_sync\s*\(\s*&\s*{wn}\s*\)\s*;)\s*"
        rf"(skb_queue_purge\s*\(\s*&\s*{hn}\s*\)\s*;)",
        r"\2\n\t\1",
        code,
        count=1,
    )


def _drop_export_symbol(code: str) -> str:
    """Drop EXPORT_SYMBOL — producer unreachable from other modules."""
    return re.sub(r"\nEXPORT_SYMBOL\s*\([^;]*\);\s*", "\n", code, count=1)


def _drop_skbuff_header(code: str) -> str:
    return code.replace("#include <linux/skbuff.h>\n", "")


def _drop_workqueue_header(code: str) -> str:
    return code.replace("#include <linux/workqueue.h>\n", "")


def _inject_gfp_kernel_in_enqueue(code: str) -> str:
    """Add a GFP_KERNEL kmalloc in the enqueue path — sleepable.

    Anchors on the ``skb_clone`` call site using its API shape, not on
    the LHS spelling — the clone variable name is free to vary."""
    return re.sub(
        r"(\w+\s*=\s*skb_clone\s*\([^;]*\);)",
        r"kmalloc(16, GFP_KERNEL);\n\t\1",
        code,
        count=1,
    )


def _inject_freertos_queue_send(code: str) -> str:
    """Inject xQueueSend — FreeRTOS contamination."""
    return re.sub(
        r"(schedule_work\s*\([^;]*\);)",
        r"xQueueSend(NULL, NULL, 0);\n\t\1",
        code,
        count=1,
    )


NEGATIVES = [
    {
        "name": "swap_skb_clone_to_gfp_kernel",
        "description": "Use GFP_KERNEL in skb_clone — may sleep from softirq caller.",
        "mutation": _swap_skb_clone_to_gfp_kernel,
        "must_fail": ["skb_clone_uses_gfp_atomic"],
        "factor_id": "D5.3",
    },
    {
        "name": "drop_null_guard_after_clone",
        "description": "Remove NULL guard after skb_clone — NULL deref on alloc failure.",
        "mutation": _drop_null_guard_after_clone,
        "must_fail": ["skb_clone_return_null_checked"],
        "factor_id": "E2.1",
    },
    {
        "name": "swap_consume_skb_to_kfree_skb",
        "description": "kfree_skb on success path — wrong free fn (dropwatch misreports).",
        "mutation": _swap_consume_skb_to_kfree_skb,
        "must_fail": ["worker_uses_consume_skb_on_success", "no_kfree_skb_on_success_path"],
        "factor_id": "E3.2",
    },
    {
        "name": "drop_skb_queue_head_init",
        "description": "Skip skb_queue_head_init — enqueue corrupts unin'd list.",
        "mutation": _drop_skb_queue_head_init,
        "must_fail": ["skb_queue_head_init_called"],
        "factor_id": "E6.2",
    },
    {
        "name": "drop_skb_queue_tail",
        "description": "Remove skb_queue_tail — clones leak immediately.",
        "mutation": _drop_skb_queue_tail,
        "must_fail": ["skb_queue_tail_called"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_skb_dequeue",
        "description": "Worker never dequeues — queue grows without bound.",
        "mutation": _drop_skb_dequeue,
        "must_fail": ["worker_uses_skb_dequeue", "worker_uses_consume_skb_on_success"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_skb_queue_purge",
        "description": "Exit skips skb_queue_purge — leaks every queued skb on unload.",
        "mutation": _drop_skb_queue_purge,
        "must_fail": ["exit_cancels_work_then_purges_queue"],
        "factor_id": "E3.3",
    },
    {
        "name": "purge_before_cancel",
        "description": "Exit drains queue before cancelling work — worker races purged list.",
        "mutation": _swap_cancel_and_purge,
        "must_fail": ["exit_cancels_work_then_purges_queue"],
        "factor_id": "E1.2",
    },
    {
        "name": "drop_export_symbol",
        "description": "Producer not exported — unreachable from other modules.",
        "mutation": _drop_export_symbol,
        "must_fail": ["export_symbol_present", "producer_exported"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_skbuff_header",
        "description": "Remove #include <linux/skbuff.h> — skb APIs unresolved.",
        "mutation": _drop_skbuff_header,
        "must_fail": ["skbuff_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_workqueue_header",
        "description": "Remove #include <linux/workqueue.h> — INIT_WORK / schedule_work unresolved.",
        "mutation": _drop_workqueue_header,
        "must_fail": ["workqueue_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_gfp_kernel_in_enqueue",
        "description": "Inject kmalloc(GFP_KERNEL) in producer — may sleep in softirq.",
        "mutation": _inject_gfp_kernel_in_enqueue,
        "must_fail": ["enqueue_not_using_gfp_kernel"],
        "factor_id": "D5.3",
    },
    {
        "name": "inject_freertos_queue_send",
        "description": "Inject FreeRTOS xQueueSend — cross-RTOS contamination.",
        "mutation": _inject_freertos_queue_send,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
