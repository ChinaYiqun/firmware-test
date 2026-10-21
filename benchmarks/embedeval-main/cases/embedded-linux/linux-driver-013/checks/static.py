"""Static analysis checks for linux-driver-013 (managed resources)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate header inclusion, module metadata, and DT binding shape."""
    details: list[CheckDetail] = []

    required_headers = [
        ("linux/module.h", "module_header_included"),
        ("linux/platform_device.h", "platform_device_header_included"),
        ("linux/of.h", "of_header_included"),
        ("linux/mod_devicetable.h", "mod_devicetable_header_included"),
        ("linux/err.h", "err_header_included"),
    ]
    for header, check_name in required_headers:
        present = scoped_contains(generated_code, header, scope="code_only")
        details.append(
            CheckDetail(
                check_name=check_name,
                passed=present,
                expected=f"#include <{header}> present",
                actual="present" if present else "missing",
                check_type="exact_match",
            )
        )

    has_gpl = scoped_contains(
        generated_code, 'MODULE_LICENSE("GPL")', scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="module_license_gpl",
            passed=has_gpl,
            expected='MODULE_LICENSE("GPL") declared',
            actual="present" if has_gpl else "missing",
            check_type="exact_match",
        )
    )

    has_module_device_table = scoped_contains(
        generated_code, "MODULE_DEVICE_TABLE(of,", scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="module_device_table_of",
            passed=has_module_device_table,
            expected="MODULE_DEVICE_TABLE(of, ...) declared",
            actual="present" if has_module_device_table else "missing",
            check_type="exact_match",
        )
    )

    has_compatible = scoped_contains(
        generated_code, '"vendor,example-sensor"', scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="compatible_string_present",
            passed=has_compatible,
            expected='.compatible = "vendor,example-sensor"',
            actual="present" if has_compatible else "missing",
            check_type="exact_match",
        )
    )

    has_module_platform_driver = scoped_contains(
        generated_code, "module_platform_driver(", scope="code_only"
    )
    details.append(
        CheckDetail(
            check_name="module_platform_driver_macro",
            passed=has_module_platform_driver,
            expected="module_platform_driver() registration macro used",
            actual="present" if has_module_platform_driver else "missing",
            check_type="exact_match",
        )
    )

    return details
