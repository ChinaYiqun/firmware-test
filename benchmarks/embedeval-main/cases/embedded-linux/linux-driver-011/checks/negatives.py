"""Negative tests for linux-driver-011 (deferred work via workqueue).

Reference: cases/embedded-linux/linux-driver-011/reference/main.c
Checks:    cases/embedded-linux/linux-driver-011/checks/{static,behavior}.py
"""

import re


def _inline_frame_read_in_isr(code: str) -> str:
    """Move the frame readl from the worker into the ISR — defeats the
    whole point of deferring heavy I/O. Removes the readl from the
    worker so the check ``worker_reads_frame_register`` correctly fires.

    Uses flexible regex to survive whitespace/comment variance in the
    reference — previously a double-space-before-``/* ack */`` anchor
    silently no-op'd on reformatted references.
    """
    # Inject a frame read immediately after the ack-write in the ISR.
    code = re.sub(
        r"(writel\(\s*0x1\s*,\s*\w+->regs\s*\+\s*STATUS_REG\s*\)\s*;\s*[^\n]*\n)",
        r"\1\treadl(f->regs + FRAME_REG);\n",
        code,
        count=1,
    )
    # Remove the worker's frame readl so the check observes the move.
    code = re.sub(r"\n\s*frame\s*=\s*readl\s*\([^)]*\);", "", code, count=1)
    return code


def _log_in_isr(code: str) -> str:
    return code.replace(
        "schedule_work(&f->work);",
        'dev_info(&f->pdev->dev, "irq fired\\n");\n\tschedule_work(&f->work);',
    )


def _drop_init_work(code: str) -> str:
    return code.replace(
        "\n\tINIT_WORK(&f->work, example_frame_worker);", ""
    )


def _drop_schedule_work(code: str) -> str:
    return code.replace("\n\tschedule_work(&f->work);", "")


def _drop_cancel_work_sync(code: str) -> str:
    return code.replace("\n\tcancel_work_sync(&f->work);", "")


def _swap_order_cancel_and_kfree(code: str) -> str:
    """Put kfree BEFORE cancel_work_sync — classic worker UAF.

    Regex-based so a reformatted reference (different indent, different
    variable name, or absent iounmap line) doesn't silently no-op the
    mutation."""
    # Match ``cancel_work_sync(...);`` … ``kfree(...);`` in sequence
    # inside remove(), capturing everything in between so it can be
    # preserved on reorder.
    pat = re.compile(
        r"(cancel_work_sync\s*\([^)]*\)\s*;)(?P<middle>.*?)(kfree\s*\([^)]*\)\s*;)",
        re.DOTALL,
    )
    return pat.sub(r"\3\g<middle>\1", code, count=1)


def _swap_order_free_irq_and_cancel(code: str) -> str:
    """Put cancel_work_sync BEFORE free_irq — IRQ may fire and
    re-schedule the worker in the gap."""
    return code.replace(
        "\tfree_irq(f->irq, f);\n\tcancel_work_sync(&f->work);",
        "\tcancel_work_sync(&f->work);\n\tfree_irq(f->irq, f);",
    )


def _msleep_in_isr(code: str) -> str:
    return code.replace(
        "writel(0x1, f->regs + STATUS_REG);",
        "msleep(1);\n\twritel(0x1, f->regs + STATUS_REG);",
    )


def _drop_worker_readl(code: str) -> str:
    return re.sub(
        r"\n\s*frame\s*=\s*readl\s*\([^)]*\);", "", code
    )


def _drop_worker_logging(code: str) -> str:
    return re.sub(
        r"\n\s*dev_info\s*\([^;]*\);",
        "",
        code,
        count=1,  # worker's is first
    )


def _drop_workqueue_header(code: str) -> str:
    return code.replace("#include <linux/workqueue.h>\n", "")


def _inject_freertos_xsemaphore(code: str) -> str:
    return code.replace(
        "platform_set_drvdata(pdev, f);",
        'xSemaphoreTake(NULL, 0);\n\tplatform_set_drvdata(pdev, f);',
    )


NEGATIVES = [
    {
        "name": "inline_frame_read_in_isr",
        "description": "Inline the frame register read into the ISR — defeats the deferral pattern and may hold a bus mutex in hardirq.",
        "mutation": _inline_frame_read_in_isr,
        "must_fail": ["worker_reads_frame_register"],
        "factor_id": "D5.1",
    },
    {
        "name": "log_in_isr",
        "description": "Emit dev_info from the ISR — violates the deferral discipline, makes log line pressure block interrupts.",
        "mutation": _log_in_isr,
        "must_fail": ["isr_no_logging"],
        "factor_id": "D5.2",
    },
    {
        "name": "drop_init_work",
        "description": "Remove INIT_WORK from probe — schedule_work on uninitialised work_struct is UB.",
        "mutation": _drop_init_work,
        "must_fail": ["init_work_called_in_probe"],
        "factor_id": "E6.2",
    },
    {
        "name": "drop_schedule_work",
        "description": "Remove schedule_work from ISR — worker never runs; frame never consumed.",
        "mutation": _drop_schedule_work,
        "must_fail": ["isr_schedules_work"],
        "factor_id": "B4.1",
    },
    {
        "name": "drop_cancel_work_sync",
        "description": "Remove cancel_work_sync from remove — worker may dereference state after kfree (use-after-free).",
        "mutation": _drop_cancel_work_sync,
        "must_fail": ["remove_flushes_or_cancels_work", "kfree_after_cancel_work"],
        "factor_id": "E3.1",
    },
    {
        "name": "kfree_before_cancel_work",
        "description": "Reorder remove() so kfree runs BEFORE cancel_work_sync — worker dereferences freed state.",
        "mutation": _swap_order_cancel_and_kfree,
        "must_fail": ["kfree_after_cancel_work"],
        "factor_id": "E3.1",
    },
    {
        "name": "cancel_work_before_free_irq",
        "description": "Cancel workers before freeing IRQ — IRQ may re-schedule the worker in the gap.",
        "mutation": _swap_order_free_irq_and_cancel,
        "must_fail": ["free_irq_before_cancel_work"],
        "factor_id": "E1.1",
    },
    {
        "name": "msleep_in_isr",
        "description": "Inject msleep in IRQ handler — sleeping in hardirq is illegal.",
        "mutation": _msleep_in_isr,
        "must_fail": ["isr_no_sleepable_calls"],
        "factor_id": "D5.2",
    },
    {
        "name": "drop_worker_readl",
        "description": "Worker never reads the frame register — deferred work is a no-op.",
        "mutation": _drop_worker_readl,
        "must_fail": ["worker_reads_frame_register"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_worker_logging",
        "description": "Worker never logs — observability regression (and the reason we deferred in the first place).",
        "mutation": _drop_worker_logging,
        "must_fail": ["worker_logs"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_workqueue_header",
        "description": "Remove #include <linux/workqueue.h> — INIT_WORK / schedule_work unresolved.",
        "mutation": _drop_workqueue_header,
        "must_fail": ["workqueue_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_freertos_xsemaphore",
        "description": "Inject FreeRTOS xSemaphoreTake — cross-RTOS contamination in Linux driver.",
        "mutation": _inject_freertos_xsemaphore,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
