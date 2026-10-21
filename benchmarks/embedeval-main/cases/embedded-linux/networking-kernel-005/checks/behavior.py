"""Behavioral checks for networking-kernel-005 (netdevice notifier).

Validates:
  - struct notifier_block declared with .notifier_call field.
  - register_netdevice_notifier / unregister_netdevice_notifier
    balanced across init / exit.
  - Init checks the register return value.
  - Callback switches on NETDEV_UP / NETDEV_DOWN.
  - Callback uses netdev_notifier_info_to_dev accessor (NOT a raw
    pointer cast to struct net_device *).
  - Callback returns NOTIFY_OK / NOTIFY_DONE (NOT 0 or -errno).
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_function_body,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    strip_comments,
)
from embedeval.models import CheckDetail


def _find_notifier_callback_body(code: str) -> str:
    """Find the notifier callback — the function referenced by
    .notifier_call. If that field doesn't exist, fall back to the
    first function with the canonical 3-arg signature."""
    stripped = strip_comments(code)
    m = re.search(r"\.notifier_call\s*=\s*(\w+)\b", stripped)
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    m = re.search(
        r"static\s+int\s+(\w+)\s*\("
        r"\s*struct\s+notifier_block\s*\*\s*\w+\s*,"
        r"\s*unsigned\s+long\s+\w+\s*,"
        r"\s*void\s*\*\s*\w+\s*\)\s*\{",
        stripped,
    )
    if m:
        return extract_function_body(stripped, m.group(1)) or ""
    return ""


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)
    init_body = extract_module_init_body(generated_code) or ""
    exit_body = extract_module_exit_body(generated_code) or ""
    cb_body = _find_notifier_callback_body(generated_code)

    # 1. struct notifier_block declared.
    has_nb = bool(
        re.search(r"\bstruct\s+notifier_block\s+\w+\s*(=|;)", stripped)
    )
    details.append(
        CheckDetail(
            check_name="notifier_block_struct_declared",
            passed=has_nb,
            expected="struct notifier_block <name> at module scope",
            actual="present" if has_nb else "missing",
            check_type="constraint",
        )
    )

    # 2. .notifier_call field populated.
    has_notifier_call = bool(
        re.search(r"\.notifier_call\s*=\s*\w+", stripped)
    )
    details.append(
        CheckDetail(
            check_name="notifier_block_has_notifier_call",
            passed=has_notifier_call,
            expected=".notifier_call = <callback>",
            actual="present" if has_notifier_call else "missing",
            check_type="constraint",
        )
    )

    # 3. register_netdevice_notifier called from init.
    register_in_init = has_api_call(init_body, "register_netdevice_notifier")
    details.append(
        CheckDetail(
            check_name="register_netdevice_notifier_in_init",
            passed=register_in_init,
            expected="register_netdevice_notifier(&nb) in init",
            actual="present" if register_in_init else "missing",
            check_type="constraint",
        )
    )

    # 4. unregister_netdevice_notifier called from exit.
    unregister_in_exit = has_api_call(
        exit_body, "unregister_netdevice_notifier"
    )
    details.append(
        CheckDetail(
            check_name="unregister_netdevice_notifier_in_exit",
            passed=unregister_in_exit,
            expected="unregister_netdevice_notifier(&nb) in exit",
            actual="present" if unregister_in_exit else "missing",
            check_type="constraint",
        )
    )

    # 5. Init checks register return. Extract LHS of assignment.
    lhs = re.search(r"(\w+)\s*=\s*register_netdevice_notifier\s*\(", init_body)
    return_checked = False
    if lhs:
        name = re.escape(lhs.group(1))
        return_checked = bool(
            re.search(
                rf"if\s*\(\s*{name}\b|if\s*\(\s*{name}\s*[!<>=]",
                init_body,
            )
        )
    details.append(
        CheckDetail(
            check_name="init_checks_register_return",
            passed=return_checked,
            expected="if (ret) return ret; after register_netdevice_notifier",
            actual="checked" if return_checked else "unchecked return",
            check_type="constraint",
        )
    )

    # 6. Callback returns NOTIFY_OK or NOTIFY_DONE (not 0 / -errno).
    cb_returns_notify = bool(
        re.search(r"return\s+NOTIFY_(OK|DONE)\b", cb_body)
    )
    details.append(
        CheckDetail(
            check_name="callback_returns_notify_ok_or_done",
            passed=cb_returns_notify,
            expected="return NOTIFY_OK / NOTIFY_DONE (not 0 or errno)",
            actual="present" if cb_returns_notify else "missing NOTIFY_* return",
            check_type="constraint",
        )
    )

    # 7. Callback handles NETDEV_UP.
    cb_handles_up = bool(re.search(r"\bcase\s+NETDEV_UP\b", cb_body)) or bool(
        re.search(r"\bevent\s*==\s*NETDEV_UP\b", cb_body)
    )
    details.append(
        CheckDetail(
            check_name="callback_handles_netdev_up",
            passed=cb_handles_up,
            expected="case NETDEV_UP / event == NETDEV_UP in callback",
            actual="present" if cb_handles_up else "missing",
            check_type="constraint",
        )
    )

    # 8. Callback handles NETDEV_DOWN.
    cb_handles_down = bool(
        re.search(r"\bcase\s+NETDEV_DOWN\b", cb_body)
    ) or bool(re.search(r"\bevent\s*==\s*NETDEV_DOWN\b", cb_body))
    details.append(
        CheckDetail(
            check_name="callback_handles_netdev_down",
            passed=cb_handles_down,
            expected="case NETDEV_DOWN / event == NETDEV_DOWN in callback",
            actual="present" if cb_handles_down else "missing",
            check_type="constraint",
        )
    )

    # 9. Callback uses the 5.15 accessor for struct net_device *.
    # The prompt explicitly forbids a raw cast — kernel 3.11+ passes a
    # netdev_notifier_info wrapper, so a direct (struct net_device *)
    # cast reads the wrapper header as if it were a device and
    # silently corrupts. Only the accessor helper is acceptable.
    cb_uses_accessor = has_api_call(cb_body, "netdev_notifier_info_to_dev")
    cb_uses_cast = bool(
        re.search(
            r"\(\s*struct\s+net_device\s*\*\s*\)\s*\w+",
            cb_body,
        )
    )
    details.append(
        CheckDetail(
            check_name="callback_gets_net_device_from_ptr",
            passed=cb_uses_accessor,
            expected="netdev_notifier_info_to_dev(ptr) — direct cast forbidden by prompt",
            actual=(
                "accessor"
                if cb_uses_accessor
                else "direct cast (forbidden)" if cb_uses_cast else "missing"
            ),
            check_type="constraint",
        )
    )

    # 10. Callback emits a pr_info trace.
    cb_logs = has_api_call(cb_body, "pr_info") or has_api_call(cb_body, "printk")
    details.append(
        CheckDetail(
            check_name="callback_emits_pr_info",
            passed=cb_logs,
            expected="pr_info / printk inside callback",
            actual="present" if cb_logs else "missing",
            check_type="constraint",
        )
    )

    # 11. notifier_block declared at file scope, NOT on an init stack.
    # Module-scope declarations appear left-aligned (column 0) or with
    # a preceding ``static`` keyword. Stack-local declarations are
    # indented inside a function body. Check that at least one
    # declaration starts at the beginning of a line or with the
    # ``static`` qualifier.
    has_file_scope_nb = bool(
        re.search(
            r"^(?:static\s+)?struct\s+notifier_block\s+\w+\s*(=|;)",
            stripped,
            flags=re.MULTILINE,
        )
    )
    details.append(
        CheckDetail(
            check_name="notifier_block_is_static_or_global",
            passed=has_file_scope_nb,
            expected="notifier_block at file scope (static at column 0)",
            actual="present" if has_file_scope_nb else "missing file-scope decl",
            check_type="constraint",
        )
    )

    # 12. Exit always unregisters — not conditional.
    exit_has_condition = bool(
        re.search(
            r"if\s*\([^)]*\)\s*\n\s*unregister_netdevice_notifier",
            exit_body,
        )
    )
    details.append(
        CheckDetail(
            check_name="exit_always_unregisters",
            passed=unregister_in_exit and not exit_has_condition,
            expected="unconditional unregister_netdevice_notifier in exit",
            actual=(
                "clean"
                if unregister_in_exit and not exit_has_condition
                else "conditional or missing"
            ),
            check_type="constraint",
        )
    )

    # 13. No cross-platform APIs.
    cross_plat = check_no_cross_platform_apis(
        generated_code, skip_platforms=["Linux_Userspace", "POSIX"]
    )
    details.append(
        CheckDetail(
            check_name="no_cross_platform_apis",
            passed=len(cross_plat) == 0,
            expected="No FreeRTOS / Zephyr / Arduino / STM32 HAL APIs",
            actual="clean" if not cross_plat else f"found: {[a for a, _ in cross_plat]}",
            check_type="constraint",
        )
    )

    return details
