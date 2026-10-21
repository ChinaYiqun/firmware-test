"""Static checks for linux-userspace-008 (eBPF CO-RE kprobe)."""

from embedeval.check_utils import scoped_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    for header, name in [
        ("vmlinux.h", "vmlinux_h_included"),
        ("bpf/bpf_helpers.h", "bpf_helpers_h_included"),
        ("bpf/bpf_core_read.h", "bpf_core_read_h_included"),
        ("bpf/bpf_tracing.h", "bpf_tracing_h_included"),
    ]:
        p = scoped_contains(generated_code, header, scope="code_only")
        details.append(
            CheckDetail(
                check_name=name,
                passed=p,
                expected=f"#include of {header}",
                actual="present" if p else "missing",
                check_type="exact_match",
            )
        )
    return details
