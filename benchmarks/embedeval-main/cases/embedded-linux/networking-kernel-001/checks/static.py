"""Static checks for networking-kernel-001 (netfilter PRE_ROUTING hook)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    required_headers = [
        ("linux/module.h", "module_header_included"),
        ("linux/netfilter.h", "netfilter_header_included"),
        ("linux/netfilter_ipv4.h", "netfilter_ipv4_header_included"),
        ("linux/workqueue.h", "workqueue_header_included"),
        ("linux/atomic.h", "atomic_header_included"),
        ("net/net_namespace.h", "net_namespace_header_included"),
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
