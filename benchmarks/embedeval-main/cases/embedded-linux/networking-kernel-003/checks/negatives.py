"""Negative tests for networking-kernel-003 (netlink kernel socket).

Reference: cases/embedded-linux/networking-kernel-003/reference/main.c
Checks:    cases/embedded-linux/networking-kernel-003/checks/{static,behavior}.py
"""

import re


def _sock_name(code: str) -> str | None:
    """Extract the ``struct sock *`` identifier the reference uses for
    the kernel netlink endpoint."""
    m = re.search(r"\bstruct\s+sock\s*\*\s*(\w+)\s*;", code)
    return m.group(1) if m else None


def _drop_netlink_create(code: str) -> str:
    """Remove netlink_kernel_create — no listening socket at all.

    Anchors on the API call, not on the reference sock variable name."""
    return re.sub(
        r"\n\s*(\w+)\s*=\s*netlink_kernel_create\s*\([^;]*;\s*",
        r"\n\t\1 = NULL;\n",
        code,
        count=1,
    )


def _drop_netlink_release(code: str) -> str:
    """Remove netlink_kernel_release — dangling kernel socket on rmmod.

    Drops the guard + release together. Works regardless of the sock
    variable name by matching the release API call."""
    name = _sock_name(code)
    if not name:
        return re.sub(
            r"\n[^\n]*netlink_kernel_release\s*\([^;]*\);\s*",
            "\n",
            code,
            count=1,
        )
    escaped = re.escape(name)
    return re.sub(
        rf"\n\s*if\s*\(\s*{escaped}\s*\)\s*\n\s*netlink_kernel_release\s*\([^;]*\);\s*",
        "\n",
        code,
        count=1,
    )


def _drop_cfg_input_field(code: str) -> str:
    """Strip .input field from netlink_kernel_cfg — create returns a
    sock but no user->kernel messages are ever consumed."""
    return re.sub(
        r"\.input\s*=\s*\w+\s*,?\s*",
        "",
        code,
        count=1,
    )


def _drop_null_check_after_create(code: str) -> str:
    """Remove NULL check after netlink_kernel_create — init succeeds
    with invalid sock pointer. Extracts the sock LHS from the create
    assignment so the regex tracks any variable name."""
    lhs = re.search(r"(\w+)\s*=\s*netlink_kernel_create\s*\(", code)
    if not lhs:
        return code
    name = re.escape(lhs.group(1))
    return re.sub(
        rf"\n\s*if\s*\(\s*!\s*{name}\s*\)\s*\{{[^}}]*\}}",
        "",
        code,
        count=1,
    )


def _drop_enomem_return(code: str) -> str:
    """Fall through to return 0 even on NULL sock — silent failure."""
    return re.sub(
        r"return\s+-ENOMEM\s*;",
        "/* fall through */",
        code,
        count=1,
    )


def _swap_proto_to_usersock(code: str) -> str:
    """Replace custom proto with NETLINK_USERSOCK — reserved by kernel."""
    return code.replace(
        "EMBEDEVAL_NETLINK_PROTO", "NETLINK_USERSOCK"
    )


def _drop_nlmsg_hdr(code: str) -> str:
    """Remove nlmsg_hdr(skb) — pid extracted from uninitialised ptr.

    Anchors on the API call, capturing whatever LHS the reference uses."""
    return re.sub(
        r"\n\s*(\w+)\s*=\s*nlmsg_hdr\s*\([^;]*\);\s*",
        r"\n\t\1 = NULL;\n",
        code,
        count=1,
    )


def _drop_nlmsg_put(code: str) -> str:
    """Remove nlmsg_put — reply has no netlink header."""
    return re.sub(
        r"\n\s*(\w+)\s*=\s*nlmsg_put\s*\([^;]*\);\s*",
        r"\n\t\1 = NULL;\n",
        code,
        count=1,
    )


def _drop_netlink_unicast(code: str) -> str:
    """Remove netlink_unicast — reply never sent; leaks the reply skb."""
    return re.sub(
        r"\n\s*(\w+)\s*=\s*netlink_unicast\s*\([^;]*\);\s*",
        r"\n\t\1 = 0;\n",
        code,
        count=1,
    )


def _drop_nlmsg_new(code: str) -> str:
    """Remove nlmsg_new — no reply allocation."""
    return re.sub(
        r"\n\s*(\w+)\s*=\s*nlmsg_new\s*\([^;]*\);\s*",
        r"\n\t\1 = NULL;\n",
        code,
        count=1,
    )


def _drop_netlink_header(code: str) -> str:
    return code.replace("#include <linux/netlink.h>\n", "")


def _drop_net_netlink_header(code: str) -> str:
    return code.replace("#include <net/netlink.h>\n", "")


def _inject_freertos_xsemaphore(code: str) -> str:
    """Inject xSemaphoreTake — FreeRTOS contamination.

    Anchors on the netlink_kernel_create API call irrespective of the
    reference's sock variable name, protocol macro name, or argument
    formatting."""
    return re.sub(
        r"(\w+\s*=\s*netlink_kernel_create\s*\([^;]*\);)",
        r"xSemaphoreTake(NULL, 0);\n\t\1",
        code,
        count=1,
    )


NEGATIVES = [
    {
        "name": "drop_netlink_create",
        "description": "Init never creates socket — module loads with no listener.",
        "mutation": _drop_netlink_create,
        "must_fail": ["netlink_kernel_create_called", "netlink_kernel_create_in_init"],
        "factor_id": "E1.1",
    },
    {
        "name": "drop_netlink_release",
        "description": "Exit never releases socket — leaked kernel sock on rmmod.",
        "mutation": _drop_netlink_release,
        "must_fail": ["netlink_kernel_release_in_exit"],
        "factor_id": "E1.2",
    },
    {
        "name": "drop_cfg_input_field",
        "description": "cfg missing .input — inbound messages never surfaced.",
        "mutation": _drop_cfg_input_field,
        "must_fail": ["netlink_kernel_cfg_has_input_field"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_null_check_after_create",
        "description": "No NULL check on create return — undefined behaviour on alloc fail.",
        "mutation": _drop_null_check_after_create,
        "must_fail": ["netlink_kernel_create_return_null_checked"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_enomem_return",
        "description": "Init returns 0 even on NULL sock — silent failure.",
        "mutation": _drop_enomem_return,
        "must_fail": ["init_returns_negative_errno_on_null"],
        "factor_id": "E2.2",
    },
    {
        "name": "swap_proto_to_usersock",
        "description": "Use NETLINK_USERSOCK — reserved number, may clash.",
        "mutation": _swap_proto_to_usersock,
        "must_fail": ["custom_netlink_proto_not_generic_usersock"],
        "factor_id": "F5.5",
    },
    {
        "name": "drop_nlmsg_hdr",
        "description": "Remove nlmsg_hdr — pid read from NULL.",
        "mutation": _drop_nlmsg_hdr,
        "must_fail": ["input_cb_uses_nlmsg_hdr"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_nlmsg_put",
        "description": "Remove nlmsg_put — reply has no valid header.",
        "mutation": _drop_nlmsg_put,
        "must_fail": ["input_cb_uses_nlmsg_put"],
        "factor_id": "E2.3",
    },
    {
        "name": "drop_netlink_unicast",
        "description": "Never sends reply — leaks allocated reply skb.",
        "mutation": _drop_netlink_unicast,
        "must_fail": ["input_cb_sends_netlink_unicast"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_nlmsg_new",
        "description": "Remove nlmsg_new — nlmsg_put on NULL skb.",
        "mutation": _drop_nlmsg_new,
        "must_fail": ["input_cb_allocates_reply_skb"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_netlink_header",
        "description": "Remove <linux/netlink.h> — nlmsg_pid field access unresolved.",
        "mutation": _drop_netlink_header,
        "must_fail": ["netlink_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_net_netlink_header",
        "description": "Remove <net/netlink.h> — nlmsg_put / nlmsg_new unresolved.",
        "mutation": _drop_net_netlink_header,
        "must_fail": ["net_netlink_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "inject_freertos_xsemaphore",
        "description": "Inject FreeRTOS xSemaphoreTake — cross-RTOS contamination in Linux kernel module.",
        "mutation": _inject_freertos_xsemaphore,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
