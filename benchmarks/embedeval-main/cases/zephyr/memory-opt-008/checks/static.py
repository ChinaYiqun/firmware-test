"""Static analysis checks for Zephyr memory footprint Kconfig."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate memory footprint Kconfig options."""
    details: list[CheckDetail] = []

    has_fpu_off = scoped_contains(generated_code, 'CONFIG_FPU=n', scope='code_only')
    details.append(
        CheckDetail(
            check_name="fpu_disabled",
            passed=has_fpu_off,
            expected="CONFIG_FPU=n (saves ~2-4KB)",
            actual="present" if has_fpu_off else "missing or FPU enabled",
            check_type="exact_match",
        )
    )

    has_minimal_libc = scoped_contains(generated_code, 'CONFIG_MINIMAL_LIBC=y', scope='code_only')
    details.append(
        CheckDetail(
            check_name="minimal_libc_enabled",
            passed=has_minimal_libc,
            expected="CONFIG_MINIMAL_LIBC=y (saves ~20KB over newlib)",
            actual="present" if has_minimal_libc else "missing",
            check_type="exact_match",
        )
    )

    has_cbprintf_nano = scoped_contains(generated_code, 'CONFIG_CBPRINTF_NANO=y', scope='code_only')
    details.append(
        CheckDetail(
            check_name="cbprintf_nano_enabled",
            passed=has_cbprintf_nano,
            expected="CONFIG_CBPRINTF_NANO=y (reduces printf size)",
            actual="present" if has_cbprintf_nano else "missing",
            check_type="exact_match",
        )
    )

    has_dynamic_thread_off = scoped_contains(generated_code, 'CONFIG_DYNAMIC_THREAD=n', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dynamic_thread_disabled",
            passed=has_dynamic_thread_off,
            expected="CONFIG_DYNAMIC_THREAD=n",
            actual="present" if has_dynamic_thread_off else "missing",
            check_type="exact_match",
        )
    )

    return details
