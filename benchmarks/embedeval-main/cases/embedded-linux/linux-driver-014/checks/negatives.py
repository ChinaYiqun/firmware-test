"""Negative tests for linux-driver-014 (cooperative kthread)."""

import re


def _drop_should_stop(code: str) -> str:
    return code.replace("!kthread_should_stop()", "1")


def _drop_kthread_stop(code: str) -> str:
    return code.replace("\n\tkthread_stop(p->task);", "")


def _swap_kthread_stop_and_kfree(code: str) -> str:
    return code.replace(
        "\n\tkthread_stop(p->task);\n\tiounmap(p->regs);\n\tkfree(p);",
        "\n\tkfree(p);\n\tiounmap(p->regs);\n\tkthread_stop(p->task);",
    )


def _swap_kthread_run_to_create_no_wake(code: str) -> str:
    """kthread_create alone never runs the thread until wake_up_process."""
    return code.replace(
        "p->task = kthread_run(example_poll_thread, p, \"%s-poll\", DRIVER_NAME);",
        "p->task = kthread_create(example_poll_thread, p, \"%s-poll\", DRIVER_NAME);",
    )


def _swap_is_err_to_null_on_kthread(code: str) -> str:
    return code.replace(
        "if (IS_ERR(p->task))",
        "if (!p->task)",
    )


def _drop_sleep_in_thread(code: str) -> str:
    return code.replace("\n\t\tmsleep_interruptible(POLL_MS);", "")


def _drop_readl_in_thread(code: str) -> str:
    return re.sub(
        r"\n\s*p->last_reading\s*=\s*readl\([^)]*\);",
        "",
        code,
    )


def _swap_ptr_err_to_eio(code: str) -> str:
    return re.sub(
        r"ret\s*=\s*PTR_ERR\s*\([^;]*\);", "ret = -EIO;", code
    )


def _drop_kthread_header(code: str) -> str:
    return code.replace("#include <linux/kthread.h>\n", "")


def _drop_err_header(code: str) -> str:
    return code.replace("#include <linux/err.h>\n", "")


def _drop_task_struct_field(code: str) -> str:
    return code.replace("\n\tstruct task_struct *task;", "")


def _inject_freertos_vtaskdelete(code: str) -> str:
    return code.replace(
        "platform_set_drvdata(pdev, p);",
        "vTaskDelete(NULL);\n\tplatform_set_drvdata(pdev, p);",
    )


NEGATIVES = [
    {
        "name": "thread_ignores_should_stop",
        "description": "Thread loop condition becomes ``while (1)`` — kthread_stop never returns, module unload hangs forever.",
        "mutation": _drop_should_stop,
        "must_fail": ["thread_checks_should_stop"],
        "factor_id": "B3.1",
    },
    {
        "name": "drop_kthread_stop",
        "description": "remove() never calls kthread_stop — thread outlives the module; next poll dereferences freed state.",
        "mutation": _drop_kthread_stop,
        "must_fail": ["remove_calls_kthread_stop"],
        "factor_id": "E3.1",
    },
    {
        "name": "kfree_before_kthread_stop",
        "description": "Reorder remove() so kfree runs BEFORE kthread_stop — thread's last poll UAFs on freed state.",
        "mutation": _swap_kthread_stop_and_kfree,
        "must_fail": ["kthread_stop_before_kfree"],
        "factor_id": "E1.1",
    },
    {
        "name": "kthread_create_without_wake",
        "description": "Use kthread_create without wake_up_process — thread never runs.",
        "mutation": _swap_kthread_run_to_create_no_wake,
        "must_fail": ["kthread_started_in_probe"],
        "factor_id": "F2.1",
    },
    {
        "name": "null_check_on_kthread_run",
        "description": "NULL-check the kthread_run result — ERR_PTR is non-NULL; failed-start goes undetected.",
        "mutation": _swap_is_err_to_null_on_kthread,
        "must_fail": ["is_err_guards_kthread_start"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_sleep_in_thread",
        "description": "Thread loop has no sleep — burns 100% CPU on one core.",
        "mutation": _drop_sleep_in_thread,
        "must_fail": ["thread_has_sleep"],
        "factor_id": "B3.2",
    },
    {
        "name": "drop_readl_in_thread",
        "description": "Thread never reads the register — cached value always stale.",
        "mutation": _drop_readl_in_thread,
        "must_fail": ["thread_reads_register"],
        "factor_id": "E2.1",
    },
    {
        "name": "hardcoded_eio_instead_of_ptr_err",
        "description": "Return -EIO instead of PTR_ERR — loses the actual errno from kthread_run.",
        "mutation": _swap_ptr_err_to_eio,
        "must_fail": ["ptr_err_propagated"],
        "factor_id": "E2.2",
    },
    {
        "name": "drop_kthread_header",
        "description": "Remove #include <linux/kthread.h> — kthread_run / kthread_should_stop unresolved.",
        "mutation": _drop_kthread_header,
        "must_fail": ["kthread_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_err_header",
        "description": "Remove #include <linux/err.h> — IS_ERR / PTR_ERR unresolved.",
        "mutation": _drop_err_header,
        "must_fail": ["err_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_task_struct_field",
        "description": "Remove task_struct pointer field — thread handle lost; kthread_stop has no target.",
        "mutation": _drop_task_struct_field,
        "must_fail": ["task_struct_field_declared"],
        "factor_id": "F5.2",
    },
    {
        "name": "inject_freertos_vtaskdelete",
        "description": "Inject FreeRTOS vTaskDelete — cross-RTOS contamination in Linux driver.",
        "mutation": _inject_freertos_vtaskdelete,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
