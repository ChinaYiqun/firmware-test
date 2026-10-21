"""Negative tests for linux-driver-013 (managed resources).

Reference: cases/embedded-linux/linux-driver-013/reference/main.c
Checks:    cases/embedded-linux/linux-driver-013/checks/{static,behavior}.py

Each mutation targets at least one behavior check by name and pins a
failure factor from LLM-EMBEDDED-FAILURE-FACTORS.md. The CVE-2026-23068
mirror (manual free paired with devm) is the central discriminator.

Authored: 2026-04-19.
"""

import re


def _swap_all_ptr_err_to_eio(code: str) -> str:
    """Replace every ``return PTR_ERR(...);`` with ``return -EIO;``.

    Whole-file regex so the mutation remains representative of the
    ``ptr_err_used_for_error_propagation`` whole-file presence check,
    regardless of which error-pointer variables the reference uses.
    """
    return re.sub(r"return\s+PTR_ERR\s*\([^;]*\);", "return -EIO;", code)


NEGATIVES = [
    {
        "name": "drop_err_h_header",
        "description": "Remove #include <linux/err.h> — IS_ERR/PTR_ERR macros unresolved.",
        "mutation": lambda code: code.replace("#include <linux/err.h>\n", ""),
        "must_fail": ["err_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "plain_kzalloc_instead_of_devm",
        "description": "Use plain kzalloc for per-device state — leaks on probe failure after this allocation.",
        "mutation": lambda code: code.replace(
            "priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);",
            "priv = kzalloc(sizeof(*priv), GFP_KERNEL);",
        ),
        "must_fail": [
            "devm_kzalloc_used_in_probe",
            "no_plain_kzalloc_for_device_state",
        ],
        "factor_id": "E3.1",
    },
    {
        "name": "manual_iounmap_in_remove",
        "description": "Add iounmap in remove() — double-unmaps the devm_platform_ioremap_resource mapping (CVE-2026-23068 pattern).",
        "mutation": lambda code: code.replace(
            "static int example_sensor_remove(struct platform_device *pdev)\n{\n\t(void)pdev;\n\treturn 0;\n}",
            "static int example_sensor_remove(struct platform_device *pdev)\n{\n\tstruct example_sensor *priv = platform_get_drvdata(pdev);\n\tiounmap(priv->regs);\n\treturn 0;\n}",
        ),
        "must_fail": [
            "no_manual_free_for_devm_resource",
            "remove_does_not_double_free",
        ],
        "factor_id": "E1.1",
    },
    {
        "name": "manual_clk_put_after_devm_get",
        "description": "Call clk_put on a devm_clk_get_optional handle in remove — devm will also put it (double free).",
        "mutation": lambda code: code.replace(
            "static int example_sensor_remove(struct platform_device *pdev)\n{\n\t(void)pdev;\n\treturn 0;\n}",
            "static int example_sensor_remove(struct platform_device *pdev)\n{\n\tstruct example_sensor *priv = platform_get_drvdata(pdev);\n\tclk_put(priv->clk);\n\treturn 0;\n}",
        ),
        "must_fail": [
            "no_manual_free_for_devm_resource",
            "remove_does_not_double_free",
        ],
        "factor_id": "E1.1",
    },
    {
        "name": "manual_free_irq_in_remove",
        "description": "Call free_irq in remove — devm_request_threaded_irq already registers free_irq with devres, double free.",
        "mutation": lambda code: code.replace(
            "static int example_sensor_remove(struct platform_device *pdev)\n{\n\t(void)pdev;\n\treturn 0;\n}",
            "static int example_sensor_remove(struct platform_device *pdev)\n{\n\tstruct example_sensor *priv = platform_get_drvdata(pdev);\n\tfree_irq(priv->irq, priv);\n\treturn 0;\n}",
        ),
        "must_fail": [
            "no_manual_free_for_devm_resource",
            "remove_does_not_double_free",
        ],
        "factor_id": "E1.1",
    },
    {
        "name": "null_check_instead_of_is_err",
        "description": "Replace IS_ERR guard for devm_platform_ioremap_resource with plain NULL check — ERR_PTR is non-NULL, check silently passes a -ENODEV value through.",
        "mutation": lambda code: code.replace(
            "\tif (IS_ERR(priv->regs))\n\t\treturn PTR_ERR(priv->regs);",
            "\tif (!priv->regs)\n\t\treturn -ENODEV;",
        ),
        "must_fail": ["is_err_guards_err_ptr_apis"],
        "factor_id": "E2.1",
    },
    {
        "name": "null_check_instead_of_is_err_for_clk",
        "description": "Replace IS_ERR guard for devm_clk_get_optional with NULL check — identical ERR_PTR confusion, clk framework return value semantics broken.",
        "mutation": lambda code: code.replace(
            "\tif (IS_ERR(priv->clk))\n\t\treturn PTR_ERR(priv->clk);",
            "\tif (!priv->clk)\n\t\treturn -ENODEV;",
        ),
        "must_fail": ["is_err_guards_err_ptr_apis"],
        "factor_id": "E2.1",
    },
    {
        "name": "return_eio_instead_of_ptr_err",
        "description": "Swap PTR_ERR propagation for hardcoded -EIO — loses the actual errno (EPROBE_DEFER, ENOENT, etc.) from the subsystem.",
        "mutation": _swap_all_ptr_err_to_eio,
        "must_fail": ["ptr_err_used_for_error_propagation"],
        "factor_id": "E2.2",
    },
    {
        "name": "replace_devm_ioremap_with_manual",
        "description": "Use plain ioremap/of_iomap instead of devm_platform_ioremap_resource — regs leak on probe failure after this point.",
        "mutation": lambda code: code.replace(
            "\tpriv->regs = devm_platform_ioremap_resource(pdev, 0);\n"
            "\tif (IS_ERR(priv->regs))\n"
            "\t\treturn PTR_ERR(priv->regs);",
            "\tpriv->regs = of_iomap(pdev->dev.of_node, 0);\n"
            "\tif (!priv->regs)\n"
            "\t\treturn -ENOMEM;",
        ),
        "must_fail": ["devm_ioremap_used"],
        "factor_id": "E3.1",
    },
    {
        "name": "replace_devm_irq_with_plain_request",
        "description": "Use request_threaded_irq instead of devm_request_threaded_irq — IRQ never released when device unbinds.",
        "mutation": lambda code: code.replace(
            "devm_request_threaded_irq", "request_threaded_irq"
        ),
        "must_fail": ["devm_threaded_irq_used"],
        "factor_id": "E3.1",
    },
    {
        "name": "replace_devm_gpiod_with_plain_get",
        "description": "Use gpiod_get instead of devm_gpiod_get — reset GPIO leaks on probe failure after this step.",
        "mutation": lambda code: code.replace(
            'priv->reset = devm_gpiod_get(dev, "reset", GPIOD_OUT_LOW);',
            'priv->reset = gpiod_get(dev, "reset", GPIOD_OUT_LOW);',
        ),
        "must_fail": ["devm_gpiod_get_used"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_module_device_table",
        "description": "Remove MODULE_DEVICE_TABLE(of, ...) — module loader cannot auto-load from DT compatible match.",
        "mutation": lambda code: code.replace(
            "MODULE_DEVICE_TABLE(of, example_sensor_of_match);\n", ""
        ),
        "must_fail": ["module_device_table_of"],
        "factor_id": "F5.2",
    },
]
