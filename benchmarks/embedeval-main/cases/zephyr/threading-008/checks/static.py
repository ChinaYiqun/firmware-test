"""Static analysis checks for real-time thread with deadline measurement."""

import re

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate real-time timing measurement code."""
    details: list[CheckDetail] = []

    # Check 1: kernel header
    has_kernel_h = scoped_contains(generated_code, 'zephyr/kernel.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="kernel_header_included",
            passed=has_kernel_h,
            expected="zephyr/kernel.h included",
            actual="present" if has_kernel_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: k_cycle_get_32 used for timing
    has_cycle_get = scoped_contains(generated_code, 'k_cycle_get_32', scope='code_only')
    details.append(
        CheckDetail(
            check_name="k_cycle_get_32_used",
            passed=has_cycle_get,
            expected="k_cycle_get_32() used for high-resolution timing",
            actual="present" if has_cycle_get else "missing (k_uptime_get?)",
            check_type="exact_match",
        )
    )

    # Check 3: Cycle-to-time conversion present
    has_conversion = (
        scoped_contains(generated_code, 'k_cyc_to_us_near32', scope='code_only')
        or scoped_contains(generated_code, 'k_cyc_to_ns_near64', scope='code_only')
        or scoped_contains(generated_code, 'k_cyc_to_ms_near32', scope='code_only')
        or scoped_contains(generated_code, 'k_cyc_to_us_floor32', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="cycle_to_time_conversion",
            passed=has_conversion,
            expected="k_cyc_to_us_near32() or equivalent conversion used",
            actual="present" if has_conversion else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: Deadline threshold referenced (10000 us or 10 ms)
    has_deadline = scoped_contains(generated_code, '10000', scope='code_only') or scoped_contains(generated_code, '10 * 1000', scope='code_only')
    details.append(
        CheckDetail(
            check_name="deadline_threshold_defined",
            passed=has_deadline,
            expected="10ms deadline (10000 us) threshold referenced",
            actual="present" if has_deadline else "missing",
            check_type="constraint",
        )
    )

    # Check 5: Thread priority < 5 (high priority)
    # Look for K_THREAD_DEFINE or k_thread_create with priority argument
    priority_match = re.search(
        r"K_THREAD_DEFINE\s*\([^,]+,[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,\s*(\d+)\s*,",
        generated_code,
    )
    if not priority_match:
        priority_match = re.search(
            r"#define\s+\w*(?:PRIO|PRIORITY)\w*\s+(\d+)",
            generated_code,
        )
    prio_val = int(priority_match.group(1)) if priority_match else 99
    has_high_prio = prio_val < 5
    details.append(
        CheckDetail(
            check_name="high_thread_priority",
            passed=has_high_prio,
            expected="Thread priority < 5 (high priority for real-time)",
            actual=f"priority={prio_val}" if priority_match else "priority not found",
            check_type="constraint",
        )
    )

    return details
