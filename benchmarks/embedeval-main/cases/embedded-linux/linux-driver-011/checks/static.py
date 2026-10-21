"""Static checks for linux-driver-011 (deferred work via workqueue)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    required_headers = [
        ("linux/module.h", "module_header_included"),
        ("linux/platform_device.h", "platform_device_header_included"),
        ("linux/workqueue.h", "workqueue_header_included"),
        ("linux/interrupt.h", "interrupt_header_included"),
        ("linux/io.h", "io_header_included"),
        ("linux/slab.h", "slab_header_included"),
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

    for tok, name in [
        ('MODULE_LICENSE("GPL")', "module_license_gpl"),
        ("MODULE_DEVICE_TABLE(of,", "module_device_table_of"),
        ('"vendor,example-frame"', "compatible_string_present"),
        ("module_platform_driver(", "module_platform_driver_macro"),
    ]:
        present = scoped_contains(generated_code, tok, scope="code_only")
        details.append(
            CheckDetail(
                check_name=name,
                passed=present,
                expected=f"{tok} present",
                actual="present" if present else "missing",
                check_type="exact_match",
            )
        )

    return details
