"""Negative tests for linux-driver-012 (threaded IRQ split)."""

import re


def _swap_threaded_to_plain_request_irq(code: str) -> str:
    return re.sub(
        r"ret\s*=\s*request_threaded_irq\s*\(\s*b->irq,[^;]*;",
        "ret = request_irq(b->irq, example_button_primary, IRQF_TRIGGER_RISING, DRIVER_NAME, b);",
        code,
        flags=re.DOTALL,
    )


def _drop_thread_function(code: str) -> str:
    """Remove the example_button_thread function entirely and change
    IRQ_WAKE_THREAD to IRQ_HANDLED in primary."""
    code = re.sub(
        r"static irqreturn_t example_button_thread\(int irq, void \*dev_id\)\s*\{[^}]*\}\s*\n",
        "",
        code,
        flags=re.DOTALL,
    )
    code = code.replace(
        "return IRQ_WAKE_THREAD;", "return IRQ_HANDLED;"
    )
    code = code.replace(
        "\n\t\t\t\t   example_button_thread,", "\n\t\t\t\t   NULL,"
    )
    return code


def _swap_wake_thread_to_handled(code: str) -> str:
    """Primary returns IRQ_HANDLED instead of IRQ_WAKE_THREAD — thread
    never runs."""
    return code.replace("return IRQ_WAKE_THREAD;", "return IRQ_HANDLED;")


def _inject_msleep_in_primary(code: str) -> str:
    return code.replace(
        "b->last_press = ktime_get();",
        "b->last_press = ktime_get();\n\tmsleep(5);",
    )


def _inject_dev_info_in_primary(code: str) -> str:
    return code.replace(
        "b->last_press = ktime_get();",
        'b->last_press = ktime_get();\n\tdev_info(b->dev, "primary fired\\n");',
    )


def _drop_msleep_in_thread(code: str) -> str:
    return code.replace("\n\tmsleep(DEBOUNCE_MS);", "")


def _drop_irqf_oneshot(code: str) -> str:
    return code.replace(
        "IRQF_ONESHOT | IRQF_TRIGGER_RISING", "IRQF_TRIGGER_RISING"
    )


def _drop_ktime_get(code: str) -> str:
    return code.replace(
        "\n\tb->last_press = ktime_get();", ""
    )


def _drop_thread_dev_info(code: str) -> str:
    # Only the thread's dev_info — drop the ktime_to_ns one, not the probe-side dev_info.
    return re.sub(
        r"\n\s*dev_info\(b->dev,[^;]*ktime_to_ns[^;]*\);",
        "",
        code,
    )


def _drop_free_irq(code: str) -> str:
    return code.replace("\n\tfree_irq(b->irq, b);", "")


def _drop_delay_header(code: str) -> str:
    return code.replace("#include <linux/delay.h>\n", "")


def _inject_freertos_vtaskdelay(code: str) -> str:
    return code.replace(
        "msleep(DEBOUNCE_MS);",
        "vTaskDelay(5);\n\tmsleep(DEBOUNCE_MS);",
    )


NEGATIVES = [
    {
        "name": "use_plain_request_irq",
        "description": "Use request_irq instead of request_threaded_irq — all work runs in hardirq; debounce msleep would BUG.",
        "mutation": _swap_threaded_to_plain_request_irq,
        "must_fail": ["request_threaded_irq_used", "no_plain_request_irq"],
        "factor_id": "D5.1",
    },
    {
        "name": "drop_thread_handler",
        "description": "Remove the thread handler (pass NULL + drop IRQ_WAKE_THREAD) — debounce stops working.",
        "mutation": _drop_thread_function,
        "must_fail": ["two_isr_functions", "thread_handler_sleeps"],
        "factor_id": "B4.1",
    },
    {
        "name": "primary_returns_irq_handled",
        "description": "Primary returns IRQ_HANDLED — thread handler never runs.",
        "mutation": _swap_wake_thread_to_handled,
        "must_fail": ["primary_returns_irq_wake_thread"],
        "factor_id": "B4.1",
    },
    {
        "name": "msleep_in_primary",
        "description": "Inject msleep in primary — sleeping in hardirq BUGs.",
        "mutation": _inject_msleep_in_primary,
        "must_fail": ["primary_no_sleepable_calls"],
        "factor_id": "D5.2",
    },
    {
        "name": "dev_info_in_primary",
        "description": "Log from primary — violates the deferral split; logging belongs in thread handler.",
        "mutation": _inject_dev_info_in_primary,
        "must_fail": ["primary_no_logging"],
        "factor_id": "D5.2",
    },
    {
        "name": "drop_msleep_in_thread",
        "description": "Remove msleep from thread — debounce window gone, bounce events all fire.",
        "mutation": _drop_msleep_in_thread,
        "must_fail": ["thread_handler_sleeps"],
        "factor_id": "B2.1",
    },
    {
        "name": "drop_irqf_oneshot",
        "description": "Remove IRQF_ONESHOT — line unmasks before thread runs, reentry chaos.",
        "mutation": _drop_irqf_oneshot,
        "must_fail": ["irqf_oneshot_flag_used"],
        "factor_id": "D5.1",
    },
    {
        "name": "drop_ktime_get",
        "description": "Primary never records the timestamp — thread logs garbage.",
        "mutation": _drop_ktime_get,
        "must_fail": ["primary_timestamps_event"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_thread_dev_info",
        "description": "Thread never logs — observability regression.",
        "mutation": _drop_thread_dev_info,
        "must_fail": ["thread_handler_logs"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_free_irq",
        "description": "remove() never frees IRQ — stale handler lives after unbind.",
        "mutation": _drop_free_irq,
        "must_fail": ["remove_frees_irq"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_delay_header",
        "description": "Remove #include <linux/delay.h> — msleep unresolved.",
        "mutation": _drop_delay_header,
        "must_fail": ["delay_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_freertos_vtaskdelay",
        "description": "Inject FreeRTOS vTaskDelay — cross-RTOS contamination.",
        "mutation": _inject_freertos_vtaskdelay,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]

