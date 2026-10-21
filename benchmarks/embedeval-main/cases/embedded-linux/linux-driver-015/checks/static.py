"""Static checks for linux-driver-015 (regmap MMIO)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for header, name in [
        ("linux/module.h", "module_header_included"),
        ("linux/regmap.h", "regmap_header_included"),
        ("linux/io.h", "io_header_included"),
        ("linux/err.h", "err_header_included"),
    ]:
        p = scoped_contains(generated_code, header, scope="code_only")
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"#include <{header}>",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    for tok, name in [
        ('MODULE_LICENSE("GPL")', "module_license_gpl"),
        ("MODULE_DEVICE_TABLE(of,", "module_device_table_of"),
        ('"vendor,example-regmap"', "compatible_string_present"),
        ("module_platform_driver(", "module_platform_driver_macro"),
    ]:
        p = scoped_contains(generated_code, tok, scope="code_only")
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"{tok} present",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    return details
