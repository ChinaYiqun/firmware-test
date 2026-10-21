"""Negative tests for linux-driver-009 (GFP flag discipline).

Reference: cases/embedded-linux/linux-driver-009/reference/main.c
"""

import re


def _swap_isr_gfp_atomic_to_kernel(code: str) -> str:
    """Change GFP_ATOMIC in ISR to GFP_KERNEL (may-sleep BUG)."""
    # Target only the ISR's kmalloc — the reference has GFP_KERNEL in
    # probe and GFP_ATOMIC in ISR. Swap ISR's occurrence.
    return code.replace(
        "kmalloc(sizeof(*r), GFP_ATOMIC)",
        "kmalloc(sizeof(*r), GFP_KERNEL)",
    )


def _swap_probe_gfp_kernel_to_atomic(code: str) -> str:
    """Change probe's GFP_KERNEL to GFP_ATOMIC (wasteful, uses reserves)."""
    return code.replace(
        "kzalloc(sizeof(*d), GFP_KERNEL)",
        "kzalloc(sizeof(*d), GFP_ATOMIC)",
    )


def _drop_isr_alloc_failure_check(code: str) -> str:
    """Remove the ``if (!r) return IRQ_NONE;`` guard — ISR dereferences NULL."""
    return code.replace(
        "\tif (!r)\n\t\treturn IRQ_NONE;\n\n",
        "",
    )


def _swap_spin_lock_irqsave_to_plain_in_isr(code: str) -> str:
    """ISR uses plain spin_lock — race with another CPU calling remove()."""
    return code.replace(
        "spin_lock_irqsave(&d->lock, flags);\n\tlist_add_tail(&r->node, &d->head);\n\tspin_unlock_irqrestore(&d->lock, flags);",
        "spin_lock(&d->lock);\n\tlist_add_tail(&r->node, &d->head);\n\tspin_unlock(&d->lock);",
    )


def _drop_spin_lock_init(code: str) -> str:
    return code.replace("\n\tspin_lock_init(&d->lock);", "")


def _drop_init_list_head(code: str) -> str:
    return code.replace("\n\tINIT_LIST_HEAD(&d->head);", "")


def _drop_list_add(code: str) -> str:
    return code.replace(
        "\n\tlist_add_tail(&r->node, &d->head);", ""
    )


def _drop_remove_list_drain(code: str) -> str:
    return re.sub(
        r"\n\tspin_lock_irqsave\(&d->lock, flags\);\n"
        r"\tlist_for_each_entry_safe\(r, tmp, &d->head, node\) \{\n"
        r"\t\tlist_del\(&r->node\);\n"
        r"\t\tkfree\(r\);\n"
        r"\t\}\n"
        r"\tspin_unlock_irqrestore\(&d->lock, flags\);\n",
        "",
        code,
    )


def _swap_free_irq_and_drain_order(code: str) -> str:
    """Drain list BEFORE free_irq — IRQ may add records to already-drained list."""
    return code.replace(
        "free_irq(d->irq, d);\n\n\tspin_lock_irqsave(&d->lock, flags);",
        "spin_lock_irqsave(&d->lock, flags);",
    ).replace(
        "\tspin_unlock_irqrestore(&d->lock, flags);\n\n\tiounmap(d->regs);",
        "\tspin_unlock_irqrestore(&d->lock, flags);\n\n\tfree_irq(d->irq, d);\n\tiounmap(d->regs);",
    )


def _drop_list_header(code: str) -> str:
    return code.replace("#include <linux/list.h>\n", "")


def _drop_slab_header(code: str) -> str:
    return code.replace("#include <linux/slab.h>\n", "")


def _inject_freertos_xqueuesend(code: str) -> str:
    return code.replace(
        "platform_set_drvdata(pdev, d);",
        'xQueueSend(NULL, NULL, 0);\n\tplatform_set_drvdata(pdev, d);',
    )


NEGATIVES = [
    {
        "name": "gfp_kernel_in_isr",
        "description": "Use GFP_KERNEL inside hardirq handler — sleeping in atomic context BUGs the kernel.",
        "mutation": _swap_isr_gfp_atomic_to_kernel,
        "must_fail": ["isr_uses_gfp_atomic", "isr_no_gfp_kernel"],
        "factor_id": "D5.2",
    },
    {
        "name": "gfp_atomic_in_probe",
        "description": "Use GFP_ATOMIC in probe() — wasteful (taps reserved atomic pool) when sleep is fine.",
        "mutation": _swap_probe_gfp_kernel_to_atomic,
        "must_fail": ["probe_uses_gfp_kernel"],
        "factor_id": "C3.1",
    },
    {
        "name": "drop_isr_alloc_null_check",
        "description": "Remove the NULL check after ISR kmalloc — ISR dereferences NULL on OOM.",
        "mutation": _drop_isr_alloc_failure_check,
        "must_fail": ["isr_null_checks_alloc_result"],
        "factor_id": "E6.1",
    },
    {
        "name": "isr_uses_plain_spin_lock",
        "description": "ISR uses plain spin_lock / spin_unlock instead of the _irqsave variant — races with removing CPU.",
        "mutation": _swap_spin_lock_irqsave_to_plain_in_isr,
        "must_fail": ["isr_uses_spin_lock_irqsave"],
        "factor_id": "D4.1",
    },
    {
        "name": "drop_spin_lock_init",
        "description": "Remove spin_lock_init from probe — uninitialised spinlock UB.",
        "mutation": _drop_spin_lock_init,
        "must_fail": ["list_and_lock_initialized_in_probe"],
        "factor_id": "E6.2",
    },
    {
        "name": "drop_init_list_head",
        "description": "Remove INIT_LIST_HEAD from probe — first list_add_tail dereferences garbage.",
        "mutation": _drop_init_list_head,
        "must_fail": ["list_and_lock_initialized_in_probe"],
        "factor_id": "E6.2",
    },
    {
        "name": "drop_list_add_in_isr",
        "description": "Remove list_add_tail from ISR — record allocated but never queued; immediate kmalloc leak.",
        "mutation": _drop_list_add,
        "must_fail": ["isr_appends_record"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_remove_list_drain",
        "description": "Remove the list-drain loop from remove() — all queued records leak on module unload.",
        "mutation": _drop_remove_list_drain,
        "must_fail": ["remove_drains_list"],
        "factor_id": "E3.1",
    },
    {
        "name": "drain_before_free_irq",
        "description": "Drain the list BEFORE free_irq — IRQ can still fire and add records to the drained-but-not-released list.",
        "mutation": _swap_free_irq_and_drain_order,
        "must_fail": ["free_irq_before_list_drain"],
        "factor_id": "E1.1",
    },
    {
        "name": "drop_list_header",
        "description": "Remove #include <linux/list.h> — list_head / INIT_LIST_HEAD unresolved.",
        "mutation": _drop_list_header,
        "must_fail": ["list_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_slab_header",
        "description": "Remove #include <linux/slab.h> — kmalloc/kzalloc/kfree unresolved.",
        "mutation": _drop_slab_header,
        "must_fail": ["slab_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_freertos_xqueuesend",
        "description": "Inject FreeRTOS xQueueSend — cross-RTOS contamination.",
        "mutation": _inject_freertos_xqueuesend,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
