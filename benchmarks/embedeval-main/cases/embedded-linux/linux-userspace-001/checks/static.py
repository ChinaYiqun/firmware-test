"""Static checks for linux-userspace-001 (libgpiod v2 CLI toggle)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for header, name in [
        ("gpiod.h", "gpiod_header_included"),
        ("stdio.h", "stdio_header_included"),
        ("stdlib.h", "stdlib_header_included"),
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
            expected="int main(int argc, char **argv)",
            actual="present" if has_main else "missing",
            check_type="exact_match",
        )
    )
    return details
