"""Negative tests for linux-driver-015 (regmap MMIO)."""

import re


def _swap_regmap_write_to_writel(code: str) -> str:
    """Replace regmap_write with raw writel on the __iomem base."""
    return re.sub(
        r"ret\s*=\s*regmap_write\s*\(\s*r->regmap,\s*REG_CTRL,\s*0x1\s*\);",
        "writel(0x1, base + REG_CTRL);",
        code,
    )


def _swap_regmap_read_to_readl(code: str) -> str:
    return re.sub(
        r"ret\s*=\s*regmap_read\s*\(\s*r->regmap,\s*REG_STATUS,\s*&status\s*\);",
        "status = readl(base + REG_STATUS);",
        code,
    )


def _drop_reg_bits(code: str) -> str:
    return code.replace("\t.reg_bits    = 32,\n", "")


def _drop_max_register(code: str) -> str:
    return code.replace("\t.max_register = REG_MAX,\n", "")


def _swap_devm_regmap_to_plain(code: str) -> str:
    return code.replace("devm_regmap_init_mmio", "regmap_init_mmio")


def _swap_is_err_regmap_to_null(code: str) -> str:
    return code.replace(
        "if (IS_ERR(r->regmap))\n\t\treturn PTR_ERR(r->regmap);",
        "if (!r->regmap)\n\t\treturn -ENODEV;",
    )


def _drop_devm_ioremap(code: str) -> str:
    """Substitute raw ioremap without the devm prefix; leak-on-failure plus
    the devm_regmap_init_mmio can still work."""
    return code.replace(
        "base = devm_platform_ioremap_resource(pdev, 0);",
        "base = of_iomap(pdev->dev.of_node, 0);",
    )


def _drop_regmap_write(code: str) -> str:
    return re.sub(
        r"\n\s*ret\s*=\s*regmap_write\([^;]*\);\s*\n\s*if\s*\(ret\)\s*\n\s*return\s*ret;",
        "",
        code,
    )


def _drop_regmap_read(code: str) -> str:
    return re.sub(
        r"\n\s*ret\s*=\s*regmap_read\([^;]*\);\s*\n\s*if\s*\(ret\)\s*\n\s*return\s*ret;",
        "",
        code,
    )


def _swap_ptr_err_to_eio(code: str) -> str:
    return re.sub(r"return\s+PTR_ERR\s*\([^;]*\);", "return -EIO;", code)


def _drop_regmap_header(code: str) -> str:
    return code.replace("#include <linux/regmap.h>\n", "")


def _drop_regmap_field(code: str) -> str:
    return code.replace("\tstruct regmap *regmap;\n", "")


NEGATIVES = [
    {
        "name": "use_writel_instead_of_regmap_write",
        "description": "Use raw writel to CONTROL instead of regmap_write — breaks the abstraction, binds driver to MMIO backend.",
        "mutation": _swap_regmap_write_to_writel,
        "must_fail": ["regmap_write_used", "no_raw_mmio_accessors"],
        "factor_id": "F2.1",
    },
    {
        "name": "use_readl_instead_of_regmap_read",
        "description": "Use raw readl to STATUS instead of regmap_read — same abstraction break.",
        "mutation": _swap_regmap_read_to_readl,
        "must_fail": ["regmap_read_used", "no_raw_mmio_accessors"],
        "factor_id": "F2.1",
    },
    {
        "name": "drop_reg_bits",
        "description": "Remove reg_bits from regmap_config — regmap_init refuses to initialise.",
        "mutation": _drop_reg_bits,
        "must_fail": ["regmap_config_declared"],
        "factor_id": "E6.2",
    },
    {
        "name": "drop_max_register",
        "description": "Remove max_register from regmap_config — regmap has no bounds, may touch unrelated mappings.",
        "mutation": _drop_max_register,
        "must_fail": ["regmap_config_stride_and_max"],
        "factor_id": "E6.2",
    },
    {
        "name": "use_plain_regmap_init_mmio",
        "description": "Use regmap_init_mmio instead of devm variant — must be manually freed; driver leaks on probe failure.",
        "mutation": _swap_devm_regmap_to_plain,
        "must_fail": ["devm_regmap_init_mmio_used"],
        "factor_id": "E3.1",
    },
    {
        "name": "null_check_on_regmap_init",
        "description": "NULL-check devm_regmap_init_mmio — ERR_PTR treated as success.",
        "mutation": _swap_is_err_regmap_to_null,
        "must_fail": ["is_err_guards_regmap_init"],
        "factor_id": "E2.1",
    },
    {
        "name": "swap_devm_ioremap_for_of_iomap",
        "description": "Use of_iomap instead of devm_platform_ioremap_resource — leaks on probe failure.",
        "mutation": _drop_devm_ioremap,
        "must_fail": ["devm_ioremap_used"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_regmap_write_call",
        "description": "Probe never writes CONTROL — peripheral never enabled.",
        "mutation": _drop_regmap_write,
        "must_fail": ["regmap_write_used"],
        "factor_id": "E2.1",
    },
    {
        "name": "drop_regmap_read_call",
        "description": "Probe never reads STATUS — status-check pattern lost.",
        "mutation": _drop_regmap_read,
        "must_fail": ["regmap_read_used"],
        "factor_id": "E2.1",
    },
    {
        "name": "hardcoded_eio_instead_of_ptr_err",
        "description": "Return -EIO instead of PTR_ERR — loses subsystem errno.",
        "mutation": _swap_ptr_err_to_eio,
        "must_fail": ["ptr_err_propagated"],
        "factor_id": "E2.2",
    },
    {
        "name": "drop_regmap_header",
        "description": "Remove #include <linux/regmap.h> — regmap API unresolved.",
        "mutation": _drop_regmap_header,
        "must_fail": ["regmap_header_included"],
        "factor_id": "F5.1",
    },
    {
        "name": "drop_regmap_field",
        "description": "Remove the struct regmap *field from per-device state — regmap handle lost.",
        "mutation": _drop_regmap_field,
        "must_fail": ["regmap_field_in_state"],
        "factor_id": "F5.2",
    },
]
