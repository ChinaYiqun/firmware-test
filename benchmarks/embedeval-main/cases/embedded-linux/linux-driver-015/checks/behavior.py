"""Behavioral checks for linux-driver-015 (regmap MMIO abstraction)."""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_module_init_body,
    has_api_call,
    has_is_err_guard,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    stripped = strip_comments(generated_code)
    init_body = extract_module_init_body(generated_code) or ""

    # 1. regmap_config struct declared with reg_bits, val_bits.
    has_config = (
        "struct regmap_config" in stripped
        and "reg_bits" in stripped
        and "val_bits" in stripped
    )
    details.append(
        CheckDetail(
            check_name="regmap_config_declared",
            passed=has_config,
            expected="regmap_config with reg_bits and val_bits",
            actual="present" if has_config else "missing",
            check_type="constraint",
        )
    )

    # 2. reg_stride and max_register set.
    has_stride = "reg_stride" in stripped
    has_max_register = "max_register" in stripped
    details.append(
        CheckDetail(
            check_name="regmap_config_stride_and_max",
            passed=has_stride and has_max_register,
            expected="regmap_config sets reg_stride and max_register",
            actual=f"stride={has_stride}, max_register={has_max_register}",
            check_type="constraint",
        )
    )

    # 3. devm_regmap_init_mmio used (or non-devm init + explicit free).
    uses_devm_regmap = has_api_call(init_body, "devm_regmap_init_mmio")
    details.append(
        CheckDetail(
            check_name="devm_regmap_init_mmio_used",
            passed=uses_devm_regmap,
            expected="probe() calls devm_regmap_init_mmio",
            actual="present" if uses_devm_regmap else "missing",
            check_type="constraint",
        )
    )

    # 4. IS_ERR guards the regmap init result.
    regmap_guarded = has_is_err_guard(init_body, "devm_regmap_init_mmio")
    details.append(
        CheckDetail(
            check_name="is_err_guards_regmap_init",
            passed=regmap_guarded,
            expected="IS_ERR guards devm_regmap_init_mmio return (ERR_PTR API)",
            actual="present" if regmap_guarded else "missing",
            check_type="constraint",
        )
    )

    # 5. devm_platform_ioremap_resource used for the backing __iomem.
    uses_devm_ioremap = has_api_call(init_body, "devm_platform_ioremap_resource")
    details.append(
        CheckDetail(
            check_name="devm_ioremap_used",
            passed=uses_devm_ioremap,
            expected="probe() maps MMIO via devm_platform_ioremap_resource",
            actual="present" if uses_devm_ioremap else "missing",
            check_type="constraint",
        )
    )

    # 6. regmap_write is called with CONTROL register.
    uses_regmap_write = has_api_call(init_body, "regmap_write")
    details.append(
        CheckDetail(
            check_name="regmap_write_used",
            passed=uses_regmap_write,
            expected="probe() writes CONTROL via regmap_write",
            actual="present" if uses_regmap_write else "missing",
            check_type="constraint",
        )
    )

    # 7. regmap_read is called for STATUS.
    uses_regmap_read = has_api_call(init_body, "regmap_read")
    details.append(
        CheckDetail(
            check_name="regmap_read_used",
            passed=uses_regmap_read,
            expected="probe() reads STATUS via regmap_read",
            actual="present" if uses_regmap_read else "missing",
            check_type="constraint",
        )
    )

    # 8. MUST NOT use raw readl / writel / ioread32 / iowrite32.
    # regmap is the authoritative accessor.
    raw_accessors = []
    for api in ("readl", "writel", "readw", "writew", "readb", "writeb",
                "ioread32", "iowrite32"):
        if has_api_call(stripped, api):
            raw_accessors.append(api)
    details.append(
        CheckDetail(
            check_name="no_raw_mmio_accessors",
            passed=len(raw_accessors) == 0,
            expected="No raw readl/writel/ioread32/iowrite32 — regmap is the abstraction",
            actual="clean" if not raw_accessors else f"raw accessors used: {raw_accessors}",
            check_type="constraint",
        )
    )

    # 9. regmap struct field declared in per-device state.
    has_regmap_field = bool(re.search(r"\bstruct\s+regmap\s*\*\s*\w+\s*;", stripped))
    details.append(
        CheckDetail(
            check_name="regmap_field_in_state",
            passed=has_regmap_field,
            expected="struct regmap *field in per-device state",
            actual="present" if has_regmap_field else "missing",
            check_type="constraint",
        )
    )

    # 10. PTR_ERR used for error propagation.
    has_ptr_err = scoped_contains(generated_code, "PTR_ERR(", scope="code_only")
    details.append(
        CheckDetail(
            check_name="ptr_err_propagated",
            passed=has_ptr_err,
            expected="PTR_ERR() propagates ERR_PTR errno",
            actual="present" if has_ptr_err else "missing",
            check_type="constraint",
        )
    )

    # 11. No cross-platform APIs.
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
