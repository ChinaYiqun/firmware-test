"""Behavioral checks for networking-kernel-003 (netlink kernel socket).

Validates:
  - netlink_kernel_create called from init with init_net + custom proto.
  - Return NULL-checked in init.
  - netlink_kernel_cfg struct has .input field populated.
  - netlink_kernel_release called from exit.
  - Input callback uses nlmsg_hdr / nlmsg_put / netlink_unicast.
"""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_function_body,
    extract_module_exit_body,
    extract_module_init_body,
    has_api_call,
    has_netlink_kernel_api,
    strip_comments,
)
from embedeval.models import CheckDetail


def _find_input_callback_body(code: str) -> str:
    """Find the input callback: either the function assigned to
    .input, or any ``void name(struct sk_buff *skb)`` at file scope."""
    stripped = strip_comments(code)
    m = re.search(r"\.input\s*=\s*(\w+)\b", stripped)
    if m:
        body = extract_function_body(stripped, m.group(1))
        if body:
            return body
    m = re.search(
        r"static\s+void\s+(\w+)\s*\(\s*struct\s+sk_buff\s*\*\s*\w+\s*\)\s*\{",
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
    cb_body = _find_input_callback_body(generated_code)

    apis_used = has_netlink_kernel_api(generated_code)

    # 1. netlink_kernel_create used anywhere.
    create_called = "netlink_kernel_create" in apis_used
    details.append(
        CheckDetail(
            check_name="netlink_kernel_create_called",
            passed=create_called,
            expected="netlink_kernel_create(&init_net, proto, &cfg)",
            actual="present" if create_called else "missing",
            check_type="constraint",
        )
    )

    # 2. The create call lives inside module init.
    create_in_init = has_api_call(init_body, "netlink_kernel_create")
    details.append(
        CheckDetail(
            check_name="netlink_kernel_create_in_init",
            passed=create_in_init,
            expected="netlink_kernel_create invoked from init",
            actual="present" if create_in_init else "missing",
            check_type="constraint",
        )
    )

    # 3. Return value NULL-checked. Extract LHS of the assignment and
    # scan init_body for a ``if (!lhs)`` guard.
    lhs = re.search(r"(\w+)\s*=\s*netlink_kernel_create\s*\(", init_body)
    null_ok = False
    if lhs:
        name = re.escape(lhs.group(1))
        null_ok = bool(
            re.search(
                rf"if\s*\(\s*!\s*{name}\b|if\s*\(\s*{name}\s*==\s*NULL\b",
                init_body,
            )
        )
    details.append(
        CheckDetail(
            check_name="netlink_kernel_create_return_null_checked",
            passed=null_ok,
            expected="if (!nl_sk) ... after netlink_kernel_create",
            actual="guarded" if null_ok else "missing null check",
            check_type="constraint",
        )
    )

    # 4. netlink_kernel_cfg declared with .input.
    has_cfg = bool(
        re.search(
            r"\bstruct\s+netlink_kernel_cfg\s+\w+\s*=\s*\{[^}]*\.input\s*=",
            stripped,
            flags=re.DOTALL,
        )
    )
    details.append(
        CheckDetail(
            check_name="netlink_kernel_cfg_has_input_field",
            passed=has_cfg,
            expected="struct netlink_kernel_cfg { .input = <fn> }",
            actual="present" if has_cfg else "missing .input in cfg",
            check_type="constraint",
        )
    )

    # 5. Exit calls netlink_kernel_release.
    release_in_exit = has_api_call(exit_body, "netlink_kernel_release")
    details.append(
        CheckDetail(
            check_name="netlink_kernel_release_in_exit",
            passed=release_in_exit,
            expected="netlink_kernel_release(nl_sk) in exit",
            actual="present" if release_in_exit else "missing",
            check_type="constraint",
        )
    )

    # 6. Input callback uses nlmsg_hdr.
    cb_uses_hdr = has_api_call(cb_body, "nlmsg_hdr")
    details.append(
        CheckDetail(
            check_name="input_cb_uses_nlmsg_hdr",
            passed=cb_uses_hdr,
            expected="nlmsg_hdr(skb) in input callback",
            actual="present" if cb_uses_hdr else "missing",
            check_type="constraint",
        )
    )

    # 7. Input callback allocates a reply skb.
    cb_allocates_reply = has_api_call(cb_body, "nlmsg_new") or has_api_call(
        cb_body, "alloc_skb"
    )
    details.append(
        CheckDetail(
            check_name="input_cb_allocates_reply_skb",
            passed=cb_allocates_reply,
            expected="nlmsg_new / alloc_skb in input callback",
            actual="present" if cb_allocates_reply else "missing",
            check_type="constraint",
        )
    )

    # 8. Input callback fills header via nlmsg_put.
    cb_puts = has_api_call(cb_body, "nlmsg_put")
    details.append(
        CheckDetail(
            check_name="input_cb_uses_nlmsg_put",
            passed=cb_puts,
            expected="nlmsg_put(reply, ...) in input callback",
            actual="present" if cb_puts else "missing",
            check_type="constraint",
        )
    )

    # 9. Input callback sends via unicast.
    cb_unicasts = has_api_call(cb_body, "netlink_unicast")
    details.append(
        CheckDetail(
            check_name="input_cb_sends_netlink_unicast",
            passed=cb_unicasts,
            expected="netlink_unicast(nl_sk, reply, pid, 0)",
            actual="present" if cb_unicasts else "missing",
            check_type="constraint",
        )
    )

    # 10. Init returns -ENOMEM (or any negative errno) on NULL sock.
    # Accept three common forms:
    #   a) ``if (!x) { ... return -E*; ... }`` — braced block (DOTALL).
    #   b) ``if (!x)\n    return -E*;`` — statement on next line.
    #   c) ``if (!x) return -E*;`` — single-line compact form.
    has_enomem_return = (
        bool(
            re.search(
                r"if\s*\(\s*!\s*\w+\s*\)[^{]*\{[^}]*return\s+-E[A-Z]+",
                init_body,
                flags=re.DOTALL,
            )
        )
        or bool(
            re.search(
                r"if\s*\(\s*!\s*\w+\s*\)\s*\n\s*return\s+-E[A-Z]+",
                init_body,
            )
        )
        or bool(
            re.search(
                r"if\s*\(\s*!\s*\w+\s*\)\s+return\s+-E[A-Z]+",
                init_body,
            )
        )
    )
    details.append(
        CheckDetail(
            check_name="init_returns_negative_errno_on_null",
            passed=has_enomem_return,
            expected="return -ENOMEM / -errno if netlink_kernel_create == NULL",
            actual="present" if has_enomem_return else "missing explicit errno return",
            check_type="constraint",
        )
    )

    # 11. Custom proto number — NOT NETLINK_USERSOCK or NETLINK_GENERIC.
    proto_reserved = bool(
        re.search(r"netlink_kernel_create\s*\([^,]+,\s*NETLINK_(USERSOCK|GENERIC)\b", stripped)
    )
    details.append(
        CheckDetail(
            check_name="custom_netlink_proto_not_generic_usersock",
            passed=not proto_reserved,
            expected="custom protocol number (>= 24), not USERSOCK / GENERIC",
            actual="clean" if not proto_reserved else "uses reserved protocol",
            check_type="constraint",
        )
    )

    # 12. Module-scope sock * declared.
    has_sock = bool(
        re.search(r"\bstruct\s+sock\s*\*\s*\w+\s*;", stripped)
    )
    details.append(
        CheckDetail(
            check_name="module_scope_sock_declared",
            passed=has_sock,
            expected="struct sock *<name>; at module scope",
            actual="present" if has_sock else "missing",
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
