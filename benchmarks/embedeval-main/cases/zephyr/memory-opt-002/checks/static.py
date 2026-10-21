"""Static analysis checks for Zephyr stack size optimization Kconfig."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate Kconfig fragment structure for memory optimization."""
    details: list[CheckDetail] = []

    has_main_stack = scoped_contains(generated_code, 'CONFIG_MAIN_STACK_SIZE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="main_stack_size_defined",
            passed=has_main_stack,
            expected="CONFIG_MAIN_STACK_SIZE set",
            actual="present" if has_main_stack else "missing",
            check_type="exact_match",
        )
    )

    has_isr_stack = scoped_contains(generated_code, 'CONFIG_ISR_STACK_SIZE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="isr_stack_size_defined",
            passed=has_isr_stack,
            expected="CONFIG_ISR_STACK_SIZE set",
            actual="present" if has_isr_stack else "missing",
            check_type="exact_match",
        )
    )

    has_minimal_libc = scoped_contains(generated_code, 'CONFIG_MINIMAL_LIBC', scope='code_only')
    details.append(
        CheckDetail(
            check_name="minimal_libc_enabled",
            passed=has_minimal_libc,
            expected="CONFIG_MINIMAL_LIBC=y present",
            actual="present" if has_minimal_libc else "missing",
            check_type="exact_match",
        )
    )

    has_newlib_conflict = scoped_contains(generated_code, 'CONFIG_NEWLIB_LIBC=y', scope='code_only')
    details.append(
        CheckDetail(
            check_name="newlib_not_enabled",
            passed=not has_newlib_conflict,
            expected="CONFIG_NEWLIB_LIBC=y absent (conflicts with MINIMAL_LIBC)",
            actual="absent" if not has_newlib_conflict else "PRESENT (conflict!)",
            check_type="constraint",
        )
    )

    has_heap_size = scoped_contains(generated_code, 'CONFIG_HEAP_MEM_POOL_SIZE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="heap_pool_size_set",
            passed=has_heap_size,
            expected="CONFIG_HEAP_MEM_POOL_SIZE defined",
            actual="present" if has_heap_size else "missing",
            check_type="exact_match",
        )
    )

    return details
