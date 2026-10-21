"""Negative tests for linux-driver-010 (IRQ-safe locking).

Reference: cases/embedded-linux/linux-driver-010/reference/main.c
Checks:    cases/embedded-linux/linux-driver-010/checks/{static,behavior}.py
"""

import re


def _swap_read_irqsave_to_plain_lock(code: str) -> str:
    """In read(), replace spin_lock_irqsave(&r->lock, flags) with plain
    spin_lock(&r->lock); and spin_unlock_irqrestore with spin_unlock.
    Only the *second* occurrence (inside read()) is the target — the
    first is inside the IRQ handler."""
    # Both ISR and read have the same pattern. We must target only read.
    # Easier: replace BOTH occurrences with plain form in the whole file
    # except the one inside the irqreturn_t function. Since the reference
    # has exactly two identical lock blocks, replacing the second
    # occurrence (.find from position after the ISR body) works.
    anchor = "example_ring_read"
    idx = code.find(anchor)
    if idx == -1:
        return code
    head, tail = code[:idx], code[idx:]
    tail = tail.replace(
        "spin_lock_irqsave(&r->lock, flags);",
        "spin_lock(&r->lock);",
        1,
    ).replace(
        "spin_unlock_irqrestore(&r->lock, flags);",
        "spin_unlock(&r->lock);",
        1,
    )
    return head + tail


def _swap_isr_irqsave_to_plain(code: str) -> str:
    """Similar but targets the ISR body (first occurrence)."""
    return code.replace(
        "spin_lock_irqsave(&r->lock, flags);",
        "spin_lock(&r->lock);",
        1,
    ).replace(
        "spin_unlock_irqrestore(&r->lock, flags);",
        "spin_unlock(&r->lock);",
        1,
    )


def _swap_spinlock_to_mutex(code: str) -> str:
    code = code.replace("spinlock_t lock;", "struct mutex lock;")
    code = code.replace("spin_lock_init(&r->lock);", "mutex_init(&r->lock);")
    code = re.sub(
        r"spin_lock_irqsave\s*\(\s*&r->lock\s*,\s*flags\s*\);",
        "mutex_lock(&r->lock);",
        code,
    )
    code = re.sub(
        r"spin_unlock_irqrestore\s*\(\s*&r->lock\s*,\s*flags\s*\);",
        "mutex_unlock(&r->lock);",
        code,
    )
    return code


def _inject_msleep_in_isr(code: str) -> str:
    return code.replace(
        "b = readb(r->regs + DATA_REG);",
        "msleep(1);\n\tb = readb(r->regs + DATA_REG);",
    )


def _inject_copy_to_user_in_isr(code: str) -> str:
    return code.replace(
        "wake_up_interruptible(&r->wq);",
        "copy_to_user(NULL, &b, 1);\n\twake_up_interruptible(&r->wq);",
    )


def _drop_wake_up_in_isr(code: str) -> str:
    return code.replace(
        "\n\twake_up_interruptible(&r->wq);\n\treturn IRQ_HANDLED;",
        "\n\treturn IRQ_HANDLED;",
    )


def _drop_wait_event_in_read(code: str) -> str:
    return re.sub(
        r"ret\s*=\s*wait_event_interruptible\s*\([^;]*\);\s*\n\s*if\s*\(ret\)\s*\n\s*return\s*ret;\s*\n",
        "",
        code,
    )


def _drop_spin_lock_init(code: str) -> str:
    return code.replace("\n\tspin_lock_init(&r->lock);\n", "\n")


def _drop_waitqueue_init(code: str) -> str:
    return code.replace("\n\tinit_waitqueue_head(&r->wq);\n", "\n")


def _drop_copy_to_user_in_read(code: str) -> str:
    # Remove the copy_to_user call + its error branch.
    return re.sub(
        r"if\s*\(copy_to_user\([^;]*\)\)\s*\n\s*return\s*-EFAULT;\s*\n",
        "",
        code,
    )


def _drop_spinlock_header(code: str) -> str:
    return code.replace("#include <linux/spinlock.h>\n", "")


def _inject_freertos_xtaskcreate(code: str) -> str:
    """Cross-platform contamination (FreeRTOS API in Linux driver).

    Zephyr's k_sleep would be equally illustrative but is not in the
    central forbidden_apis.yaml; using FreeRTOS keeps the mutation
    detectable without expanding the global API list.
    """
    return code.replace(
        "platform_set_drvdata(pdev, r);",
        "xTaskCreate(NULL, \"foo\", 256, NULL, 1, NULL);\n\tplatform_set_drvdata(pdev, r);",
        1,
    )


NEGATIVES = [
    {
        "name": "read_uses_plain_spin_lock",
        "description": "Replace spin_lock_irqsave with plain spin_lock in read() — races with IRQ handler on the same CPU (read() preempted by ISR mid-critical-section).",
        "mutation": _swap_read_irqsave_to_plain_lock,
        "must_fail": ["read_uses_spin_lock_irqsave", "read_no_plain_spin_lock"],
        "factor_id": "D5.1",
    },
    {
        "name": "isr_uses_plain_spin_lock",
        "description": "Replace spin_lock_irqsave with plain spin_lock in ISR — still atomic relative to read() but misses documentation of IRQ-safety requirement; flags variable also becomes unused.",
        "mutation": _swap_isr_irqsave_to_plain,
        "must_fail": ["isr_uses_spin_lock_irqsave"],
        "factor_id": "D5.1",
    },
    {
        "name": "use_mutex_instead_of_spinlock",
        "description": "Swap spinlock for mutex — mutex_lock in hardirq context is forbidden and triggers a scheduling-while-atomic bug.",
        "mutation": _swap_spinlock_to_mutex,
        "must_fail": ["no_mutex_for_irq_shared_state", "spinlock_t_declared"],
        "factor_id": "D6.1",
    },
    {
        "name": "msleep_in_isr",
        "description": "Inject msleep in IRQ handler — sleeping in hardirq context is illegal.",
        "mutation": _inject_msleep_in_isr,
        "must_fail": ["isr_no_sleepable_calls"],
        "factor_id": "D5.2",
    },
    {
        "name": "copy_to_user_in_isr",
        "description": "Inject copy_to_user in IRQ handler — copy_*_user may page-fault and sleep, illegal in hardirq.",
        "mutation": _inject_copy_to_user_in_isr,
        "must_fail": ["isr_no_sleepable_calls"],
        "factor_id": "D5.2",
    },
    {
        "name": "drop_wake_up_in_isr",
        "description": "Remove wake_up_interruptible from ISR — reader sleeps forever, even with data queued.",
        "mutation": _drop_wake_up_in_isr,
        "must_fail": ["isr_wakes_readers"],
        "factor_id": "B4.1",
    },
    {
        "name": "drop_wait_event_in_read",
        "description": "Remove wait_event_interruptible from read() — read() becomes a busy-spin instead of blocking.",
        "mutation": _drop_wait_event_in_read,
        "must_fail": ["read_uses_wait_event"],
        "factor_id": "B3.1",
    },
    {
        "name": "drop_spin_lock_init",
        "description": "Remove spin_lock_init() from probe — uninitialized spinlock behavior is undefined.",
        "mutation": _drop_spin_lock_init,
        "must_fail": ["spin_lock_init_called"],
        "factor_id": "E6.2",
    },
    {
        "name": "drop_waitqueue_init",
        "description": "Remove init_waitqueue_head — wake_up/wait_event on uninit wq is UB.",
        "mutation": _drop_waitqueue_init,
        "must_fail": ["waitqueue_initialized"],
        "factor_id": "E6.2",
    },
    {
        "name": "drop_copy_to_user_in_read",
        "description": "Remove copy_to_user — read() would expose kernel stack/heap to userspace.",
        "mutation": _drop_copy_to_user_in_read,
        "must_fail": ["read_uses_copy_to_user"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_spinlock_header",
        "description": "Remove #include <linux/spinlock.h> — spinlock macros unresolved.",
        "mutation": _drop_spinlock_header,
        "must_fail": ["spinlock_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_freertos_xtaskcreate",
        "description": "Inject FreeRTOS xTaskCreate — cross-RTOS contamination in Linux driver.",
        "mutation": _inject_freertos_xtaskcreate,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
