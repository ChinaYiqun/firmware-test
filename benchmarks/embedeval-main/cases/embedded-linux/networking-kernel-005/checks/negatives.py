"""Negative tests for networking-kernel-005 (netdevice notifier).

Reference: cases/embedded-linux/networking-kernel-005/reference/main.c
Checks:    cases/embedded-linux/networking-kernel-005/checks/{static,behavior}.py
"""

import re


def _drop_notifier_call_field(code: str) -> str:
    """Drop .notifier_call — struct has no callback pointer."""
    return re.sub(
        r"\n\s*\.notifier_call\s*=\s*\w+\s*,?\s*", "\n", code, count=1
    )


def _drop_register_call(code: str) -> str:
    """Drop register_netdevice_notifier — notifier never activates."""
    return re.sub(
        r"\n\s*ret\s*=\s*register_netdevice_notifier\s*\([^;]*\);\s*",
        "\n\tret = 0;\n",
        code,
        count=1,
    )


def _drop_unregister_call(code: str) -> str:
    """Drop unregister_netdevice_notifier — dangling callback pointer."""
    return re.sub(
        r"\n\s*unregister_netdevice_notifier\s*\([^;]*\);\s*",
        "\n",
        code,
        count=1,
    )


def _drop_return_check(code: str) -> str:
    """Drop the ret-check after register — errno swallowed silently.

    Extracts the register-return LHS so the regex doesn't depend on
    the reference's ``ret`` spelling."""
    lhs = re.search(r"(\w+)\s*=\s*register_netdevice_notifier\s*\(", code)
    if not lhs:
        return code
    name = re.escape(lhs.group(1))
    return re.sub(
        rf"\n\s*if\s*\(\s*{name}\s*\)\s*\{{[^}}]*\}}",
        "\n",
        code,
        count=1,
    )


def _return_zero_from_callback(code: str) -> str:
    """Return 0 instead of NOTIFY_OK — wrong return protocol for the
    notifier chain."""
    return code.replace("return NOTIFY_OK;", "return 0;")


def _drop_netdev_up_case(code: str) -> str:
    """Drop case NETDEV_UP — UP events silent."""
    return re.sub(
        r"case\s+NETDEV_UP\s*:.*?break\s*;",
        "/* UP case removed */",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_netdev_down_case(code: str) -> str:
    """Drop case NETDEV_DOWN — DOWN events silent."""
    return re.sub(
        r"case\s+NETDEV_DOWN\s*:.*?break\s*;",
        "/* DOWN case removed */",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_netdev_notifier_info_accessor(code: str) -> str:
    """Cast ptr directly to net_device * — legacy pre-3.11 form; on
    5.15 the info wrapper is what the kernel passes, so the
    direct-cast reads the wrapper as if it were a net_device."""
    # Keep the check_cb permissive — remove BOTH accessor and direct-cast
    # so neither arm of ``callback_gets_net_device_from_ptr`` fires.
    return code.replace(
        "struct net_device *dev = netdev_notifier_info_to_dev(ptr);",
        "struct net_device *dev = NULL; (void)ptr;",
    )


def _drop_pr_info_in_callback(code: str) -> str:
    """Remove both pr_info calls in the callback — notifier is silent."""
    return re.sub(
        r"\n\s*pr_info\s*\([^;]*\);\s*", "\n", code, count=2
    )


def _drop_netdevice_header(code: str) -> str:
    return code.replace("#include <linux/netdevice.h>\n", "")


def _drop_notifier_header(code: str) -> str:
    return code.replace("#include <linux/notifier.h>\n", "")


def _make_notifier_block_stack_local(code: str) -> str:
    """Move the notifier_block onto the init function's stack — lifetime
    bug: it's gone the moment init returns.

    Extracts the notifier_block identifier and the init function name
    from the reference so the mutation survives renames of either."""
    nb_decl = re.search(
        r"static\s+struct\s+notifier_block\s+(\w+)\s*=\s*\{[^}]*\};",
        code,
        flags=re.DOTALL,
    )
    init_sig = re.search(
        r"(static\s+int\s+__init\s+\w+\s*\(\s*void\s*\)\s*\n\s*\{)",
        code,
    )
    if not (nb_decl and init_sig):
        return code
    nb_name = nb_decl.group(1)
    cb = re.search(r"\.notifier_call\s*=\s*(\w+)", nb_decl.group(0))
    cb_name = cb.group(1) if cb else "notifier_cb"
    # Delete the module-scope declaration.
    code = code.replace(nb_decl.group(0), "", 1)
    # Inject a stack-local declaration at the top of init.
    code = code.replace(
        init_sig.group(1),
        init_sig.group(1)
        + f"\n\tstruct notifier_block {nb_name} = {{ .notifier_call = {cb_name} }};",
        1,
    )
    return code


def _inject_freertos_xsemaphore(code: str) -> str:
    """Inject xSemaphoreTake — FreeRTOS contamination.

    Anchors on the register_netdevice_notifier API call, not on a
    specific LHS variable name."""
    return re.sub(
        r"(\w+\s*=\s*register_netdevice_notifier\s*\([^;]*\);)",
        r"xSemaphoreTake(NULL, 0);\n\t\1",
        code,
        count=1,
    )


NEGATIVES = [
    {
        "name": "drop_notifier_call_field",
        "description": ".notifier_call absent — register succeeds with NULL callback.",
        "mutation": _drop_notifier_call_field,
        "must_fail": ["notifier_block_has_notifier_call"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_register_call",
        "description": "Init skips register_netdevice_notifier — notifier never arms.",
        "mutation": _drop_register_call,
        "must_fail": ["register_netdevice_notifier_in_init"],
        "factor_id": "E1.1",
    },
    {
        "name": "drop_unregister_call",
        "description": "Exit skips unregister — dangling callback on rmmod, kernel BUG.",
        "mutation": _drop_unregister_call,
        "must_fail": ["unregister_netdevice_notifier_in_exit", "exit_always_unregisters"],
        "factor_id": "E1.2",
    },
    {
        "name": "drop_return_check",
        "description": "Init does not check register return — errno swallowed.",
        "mutation": _drop_return_check,
        "must_fail": ["init_checks_register_return"],
        "factor_id": "E2.2",
    },
    {
        "name": "return_zero_from_callback",
        "description": "Callback returns 0 instead of NOTIFY_OK — wrong chain protocol.",
        "mutation": _return_zero_from_callback,
        "must_fail": ["callback_returns_notify_ok_or_done"],
        "factor_id": "F5.3",
    },
    {
        "name": "drop_netdev_up_case",
        "description": "case NETDEV_UP removed — UP transitions silent.",
        "mutation": _drop_netdev_up_case,
        "must_fail": ["callback_handles_netdev_up"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_netdev_down_case",
        "description": "case NETDEV_DOWN removed — DOWN transitions silent.",
        "mutation": _drop_netdev_down_case,
        "must_fail": ["callback_handles_netdev_down"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_netdev_notifier_info_accessor",
        "description": "Remove netdev_notifier_info_to_dev — callback reads wrapper as raw net_device.",
        "mutation": _drop_netdev_notifier_info_accessor,
        "must_fail": ["callback_gets_net_device_from_ptr"],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_pr_info_in_callback",
        "description": "Remove pr_info trace — observability regression.",
        "mutation": _drop_pr_info_in_callback,
        "must_fail": ["callback_emits_pr_info"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_netdevice_header",
        "description": "Remove <linux/netdevice.h> — net_device / NETDEV_* unresolved.",
        "mutation": _drop_netdevice_header,
        "must_fail": ["netdevice_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_notifier_header",
        "description": "Remove <linux/notifier.h> — notifier_block / NOTIFY_OK unresolved.",
        "mutation": _drop_notifier_header,
        "must_fail": ["notifier_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "make_notifier_block_stack_local",
        "description": "Move notifier_block to init's stack — lifetime bug (freed on init return).",
        "mutation": _make_notifier_block_stack_local,
        "must_fail": ["notifier_block_is_static_or_global"],
        "factor_id": "E3.4",
    },
    {
        "name": "inject_freertos_xsemaphore",
        "description": "Inject FreeRTOS xSemaphoreTake — cross-RTOS contamination.",
        "mutation": _inject_freertos_xsemaphore,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
