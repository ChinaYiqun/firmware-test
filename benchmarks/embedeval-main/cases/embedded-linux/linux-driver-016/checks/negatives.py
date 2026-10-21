"""Negative tests for linux-driver-016 (mixed error-return conventions).

Reference: cases/embedded-linux/linux-driver-016/reference/main.c
Checks:    cases/embedded-linux/linux-driver-016/checks/{static,behavior}.py

Each mutation targets a specific error-convention confusion — swapping
the guard shape to the wrong one for an API — or removes a required
cleanup call.
"""

import re


def _swap_is_err_clk_to_null(code: str) -> str:
    return re.sub(
        r"if\s*\(\s*IS_ERR\s*\(\s*priv->clk\s*\)\s*\)",
        "if (!priv->clk)",
        code,
    )


def _swap_is_err_rst_to_null(code: str) -> str:
    return re.sub(
        r"if\s*\(\s*IS_ERR\s*\(\s*priv->rst\s*\)\s*\)",
        "if (!priv->rst)",
        code,
    )


def _swap_ioremap_null_to_is_err(code: str) -> str:
    return re.sub(
        r"if\s*\(\s*!\s*priv->regs\s*\)",
        "if (IS_ERR(priv->regs))",
        code,
    )


def _swap_irq_neg_to_is_err(code: str) -> str:
    return re.sub(
        r"if\s*\(\s*priv->irq\s*<\s*0\s*\)",
        "if (IS_ERR_VALUE(priv->irq))",
        code,
    )


def _swap_ptr_err_to_hardcoded_eio(code: str) -> str:
    # Reference assigns PTR_ERR to `ret` then goto's; match both direct
    # return and assigned-to-ret forms.
    code = re.sub(r"return\s+PTR_ERR\s*\([^;]*\);", "return -EIO;", code)
    code = re.sub(r"ret\s*=\s*PTR_ERR\s*\([^;]*\);", "ret = -EIO;", code)
    return code


def _drop_clk_put_in_remove(code: str) -> str:
    # Target the remove() sequence, not the err_clk label in probe.
    # Remove sequence: ``reset_control_put(priv->rst);\n\tclk_put(priv->clk);``
    return code.replace(
        "reset_control_put(priv->rst);\n\tclk_put(priv->clk);\n\tkfree(priv);",
        "reset_control_put(priv->rst);\n\tkfree(priv);",
    )


def _drop_iounmap_in_remove(code: str) -> str:
    # Remove only the occurrence following free_irq (i.e., in remove() not err path).
    return code.replace(
        "free_irq(priv->irq, priv);\n\tiounmap(priv->regs);",
        "free_irq(priv->irq, priv);",
    )


def _drop_free_irq_in_remove(code: str) -> str:
    return code.replace(
        "free_irq(priv->irq, priv);\n\t",
        "",
        1,
    )


def _drop_reset_put_in_remove(code: str) -> str:
    return code.replace(
        "iounmap(priv->regs);\n\treset_control_put(priv->rst);",
        "iounmap(priv->regs);",
    )


def _devm_kzalloc_substitute(code: str) -> str:
    return code.replace(
        "priv = kzalloc(sizeof(*priv), GFP_KERNEL);",
        "priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);",
    )


def _drop_kzalloc_null_check(code: str) -> str:
    return re.sub(
        r"if\s*\(!priv\)\s*\n\s*return\s*-ENOMEM;\s*\n",
        "",
        code,
        count=1,
    )


NEGATIVES = [
    {
        "name": "null_check_on_clk_get",
        "description": "Swap IS_ERR guard for clk_get result with plain NULL check — ERR_PTR is non-NULL, a -ENODEV errno silently passes as success.",
        "mutation": _swap_is_err_clk_to_null,
        "must_fail": ["is_err_guards_clk_get"],
        "factor_id": "E2.1",
    },
    {
        "name": "null_check_on_reset_control_get",
        "description": "Swap IS_ERR guard for reset_control_get with plain NULL check — same ERR_PTR confusion class.",
        "mutation": _swap_is_err_rst_to_null,
        "must_fail": ["is_err_guards_reset_control_get"],
        "factor_id": "E2.1",
    },
    {
        "name": "is_err_on_ioremap",
        "description": "Wrap ioremap result in IS_ERR — but ioremap returns NULL on failure, so the check is a category error and a valid NULL is treated as success.",
        "mutation": _swap_ioremap_null_to_is_err,
        "must_fail": ["no_is_err_on_ioremap", "null_check_on_ioremap"],
        "factor_id": "E6.1",
    },
    {
        "name": "is_err_value_on_platform_get_irq",
        "description": "Wrap platform_get_irq int return in IS_ERR_VALUE — a subtle but wrong guard; correct is `< 0`.",
        "mutation": _swap_irq_neg_to_is_err,
        "must_fail": ["neg_check_on_platform_get_irq"],
        "factor_id": "E6.1",
    },
    {
        "name": "hardcoded_eio_instead_of_ptr_err",
        "description": "Swap every PTR_ERR() propagation for hardcoded -EIO — loses subsystem errno (EPROBE_DEFER, ENOENT, etc.).",
        "mutation": _swap_ptr_err_to_hardcoded_eio,
        "must_fail": ["ptr_err_propagated"],
        "factor_id": "E2.2",
    },
    {
        "name": "drop_clk_put_in_remove",
        "description": "Remove clk_put from remove() — clock ref leaks on device unbind.",
        "mutation": _drop_clk_put_in_remove,
        "must_fail": ["remove_releases_all_resources"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_iounmap_in_remove",
        "description": "Remove iounmap from remove() — mapped register window leaks.",
        "mutation": _drop_iounmap_in_remove,
        "must_fail": ["remove_releases_all_resources"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_free_irq_in_remove",
        "description": "Remove free_irq from remove() — IRQ handler stays registered after driver unbinds, accessing freed state.",
        "mutation": _drop_free_irq_in_remove,
        "must_fail": ["remove_releases_all_resources"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_reset_put_in_remove",
        "description": "Remove reset_control_put from remove() — reset controller ref leaks.",
        "mutation": _drop_reset_put_in_remove,
        "must_fail": ["remove_releases_all_resources"],
        "factor_id": "E3.1",
    },
    {
        "name": "use_devm_kzalloc",
        "description": "Use devm_kzalloc instead of kzalloc — violates the traditional-lifecycle requirement and decouples from the subsequent kfree in remove.",
        "mutation": _devm_kzalloc_substitute,
        "must_fail": ["no_devm_apis_used"],
        "factor_id": "F2.1",
    },
    {
        "name": "drop_kzalloc_null_check",
        "description": "Drop the NULL check after kzalloc — probe dereferences NULL on allocation failure.",
        "mutation": _drop_kzalloc_null_check,
        "must_fail": ["null_check_on_kzalloc"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_err_header",
        "description": "Remove #include <linux/err.h> — IS_ERR/PTR_ERR unresolved.",
        "mutation": lambda code: code.replace("#include <linux/err.h>\n", ""),
        "must_fail": ["err_header_included"],
        "factor_id": "F5.1",
    },
]
