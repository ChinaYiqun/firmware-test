"""Negative tests for networking-kernel-004 (generic netlink family).

Reference: cases/embedded-linux/networking-kernel-004/reference/main.c
Checks:    cases/embedded-linux/networking-kernel-004/checks/{static,behavior}.py
"""

import re


def _drop_module_this_module(code: str) -> str:
    """Remove .module = THIS_MODULE — lifetime tracking broken."""
    return re.sub(r"\n\s*\.module\s*=\s*THIS_MODULE\s*,?\s*", "\n", code, count=1)


def _drop_n_ops(code: str) -> str:
    """Drop .n_ops — family thinks it has 0 commands."""
    return re.sub(r"\n\s*\.n_ops\s*=\s*[^,\n]+,?\s*", "\n", code, count=1)


def _drop_maxattr(code: str) -> str:
    """Drop .maxattr — attribute validation unbounded."""
    return re.sub(r"\n\s*\.maxattr\s*=\s*[^,\n]+,?\s*", "\n", code, count=1)


def _drop_ops_pointer(code: str) -> str:
    """Drop .ops — family has no command handlers. Matches any
    identifier assigned to .ops, not just the reference's spelling."""
    return re.sub(
        r"\n\s*\.ops\s*=\s*\w+\s*,?\s*", "\n", code, count=1
    )


def _use_deprecated_register_with_ops(code: str) -> str:
    """Swap to removed genl_register_family_with_ops API.

    Captures the family argument from the live register call so the
    swap doesn't depend on the reference's family identifier."""
    return re.sub(
        r"genl_register_family\s*\(\s*([^)]+)\)\s*;",
        r"genl_register_family_with_ops(\1, NULL);",
        code,
        count=1,
    )


def _drop_genl_register(code: str) -> str:
    """Init does not register family — userspace gets -ENOENT."""
    return re.sub(
        r"\n\s*ret\s*=\s*genl_register_family\s*\([^;]*\);\s*",
        "\n\tret = 0;\n",
        code,
        count=1,
    )


def _drop_genl_unregister(code: str) -> str:
    """Exit does not unregister — rmmod leaves dangling family."""
    return re.sub(
        r"\n\s*genl_unregister_family\s*\([^;]*\);\s*", "\n", code, count=1
    )


def _drop_doit_field(code: str) -> str:
    """Remove .doit from ops entry — family has no command handler.

    Matches any identifier on the RHS — the reference's handler name
    is not hardcoded."""
    return re.sub(r"\n\s*\.doit\s*=\s*\w+\s*,?\s*", "\n", code, count=1)


def _drop_cmd_field(code: str) -> str:
    """Remove .cmd from ops entry — entry defaults to 0 (CMD_UNSPEC).

    Matches any identifier on the RHS — the reference's command enum
    is not hardcoded."""
    return re.sub(r"\n\s*\.cmd\s*=\s*\w+\s*,?\s*", "\n", code, count=1)


def _vendor_prefix_name(code: str) -> str:
    """Swap neutral family name for vendor-prefixed one — violates
    namespace neutrality."""
    return code.replace('"embedeval_genl"', '"qcells-genl"')


def _drop_genlmsg_end(code: str) -> str:
    """Handler skips genlmsg_end — reply length header stays invalid."""
    return re.sub(r"\n\s*genlmsg_end\s*\([^;]*\);\s*", "\n", code, count=1)


def _drop_genlmsg_reply(code: str) -> str:
    """Handler never sends reply — request blocks until timeout."""
    return re.sub(
        r"return\s+genlmsg_reply\s*\([^;]*\);",
        "nlmsg_free(reply);\n\treturn 0;",
        code,
        count=1,
    )


def _drop_policy_binding(code: str) -> str:
    """Drop the .policy field from the family — attribute validation
    is disabled even though an nla_policy[] array is declared."""
    return re.sub(r"\n\s*\.policy\s*=\s*\w+\s*,?\s*", "\n", code, count=1)


def _inject_freertos_xsemaphore(code: str) -> str:
    """Inject xSemaphoreTake — FreeRTOS contamination."""
    return re.sub(
        r"(genl_register_family\s*\([^;]*\);)",
        r"xSemaphoreTake(NULL, 0);\n\t\1",
        code,
        count=1,
    )


NEGATIVES = [
    {
        "name": "drop_module_this_module",
        "description": ".module = THIS_MODULE removed — module ref counting broken.",
        "mutation": _drop_module_this_module,
        "must_fail": ["genl_family_has_module_this_module"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_n_ops",
        "description": ".n_ops absent — family believes it has no commands.",
        "mutation": _drop_n_ops,
        "must_fail": ["genl_family_has_n_ops"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_maxattr",
        "description": ".maxattr absent — attribute validation unbounded.",
        "mutation": _drop_maxattr,
        "must_fail": ["genl_family_has_maxattr"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_ops_pointer",
        "description": ".ops pointer absent — no dispatch target.",
        "mutation": _drop_ops_pointer,
        "must_fail": ["genl_family_has_ops_field"],
        "factor_id": "F5.4",
    },
    {
        "name": "use_deprecated_register_with_ops",
        "description": "Use removed genl_register_family_with_ops — compile fail on 5.15.",
        "mutation": _use_deprecated_register_with_ops,
        "must_fail": ["no_deprecated_genl_register_family_with_ops"],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_genl_register",
        "description": "Init skips genl_register_family — userspace gets -ENOENT.",
        "mutation": _drop_genl_register,
        "must_fail": ["genl_register_family_in_init"],
        "factor_id": "E1.1",
    },
    {
        "name": "drop_genl_unregister",
        "description": "Exit skips genl_unregister_family — dangling family after rmmod.",
        "mutation": _drop_genl_unregister,
        "must_fail": ["genl_unregister_family_in_exit"],
        "factor_id": "E1.2",
    },
    {
        "name": "drop_doit_field",
        "description": ".doit removed — dispatch has NULL handler.",
        "mutation": _drop_doit_field,
        "must_fail": ["genl_ops_array_with_cmd_and_doit"],
        "factor_id": "F5.4",
    },
    {
        "name": "drop_cmd_field",
        "description": ".cmd removed — entry defaults to CMD_UNSPEC.",
        "mutation": _drop_cmd_field,
        "must_fail": ["genl_ops_array_with_cmd_and_doit"],
        "factor_id": "F5.4",
    },
    {
        "name": "vendor_prefix_name",
        "description": "Use vendor-prefixed family name — violates namespace neutrality.",
        "mutation": _vendor_prefix_name,
        "must_fail": ["family_name_is_neutral_not_qcells", "family_name_neutral"],
        "factor_id": "F2.2",
    },
    {
        "name": "drop_genlmsg_end",
        "description": "Handler skips genlmsg_end — reply length header invalid.",
        "mutation": _drop_genlmsg_end,
        "must_fail": ["handler_uses_genlmsg_reply_builder"],
        "factor_id": "E2.3",
    },
    {
        "name": "drop_genlmsg_reply",
        "description": "Handler never replies — userspace request times out.",
        "mutation": _drop_genlmsg_reply,
        "must_fail": ["handler_uses_genlmsg_reply_builder"],
        "factor_id": "E2.3",
    },
    {
        "name": "drop_policy_binding",
        "description": ".policy field removed — attribute validation disabled.",
        "mutation": _drop_policy_binding,
        "must_fail": ["genl_family_has_policy_array"],
        "factor_id": "F5.4",
    },
    {
        "name": "inject_freertos_xsemaphore",
        "description": "Inject FreeRTOS xSemaphoreTake — cross-RTOS contamination.",
        "mutation": _inject_freertos_xsemaphore,
        "must_fail": ["no_cross_platform_apis"],
        "factor_id": "F2.1",
    },
]
