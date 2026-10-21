"""Static checks for networking-kernel-004 (generic netlink family)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    required_headers = [
        ("linux/module.h", "module_header_included"),
        ("net/genetlink.h", "genetlink_header_included"),
        ("linux/skbuff.h", "skbuff_header_included"),
    ]
    for header, name in required_headers:
        present = scoped_contains(generated_code, header, scope="code_only")
        details.append(
            CheckDetail(
                check_name=name,
                passed=present,
                expected=f"#include <{header}> present",
                actual="present" if present else "missing",
                check_type="exact_match",
            )
        )

    for tok, name in [
        ('MODULE_LICENSE("GPL")', "module_license_gpl"),
        ("module_init(", "module_init_macro"),
        ("module_exit(", "module_exit_macro"),
        ('"embedeval_genl"', "family_name_neutral"),
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
