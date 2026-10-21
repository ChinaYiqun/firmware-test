"""Static checks for boot-uboot-003 (extlinux.conf)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    # extlinux.conf is whitespace-separated tokens; use raw scope.
    for tok, name in [
        ("default", "default_directive_present"),
        ("timeout", "timeout_directive_present"),
        ("label", "label_directive_present"),
        ("kernel", "kernel_directive_present"),
        ("fdt", "fdt_directive_present"),
        ("initrd", "initrd_directive_present"),
        ("append", "append_directive_present"),
    ]:
        p = scoped_contains(generated_code, tok, scope="raw")
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"{tok} directive present",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    return details
