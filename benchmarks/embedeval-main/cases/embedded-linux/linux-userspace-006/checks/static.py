"""Static checks for linux-userspace-006 (spidev ioctl)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for header, name in [
        ("fcntl.h", "fcntl_header_included"),
        ("sys/ioctl.h", "ioctl_header_included"),
        ("linux/spi/spidev.h", "spidev_header_included"),
        ("unistd.h", "unistd_header_included"),
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
    has_main = scoped_contains(generated_code, "int main(", scope="code_only")
    details.append(
        CheckDetail(
            check_name="main_function_present",
            passed=has_main,
            expected="int main(...)",
            actual="present" if has_main else "missing",
            check_type="exact_match",
        )
    )
    return details
