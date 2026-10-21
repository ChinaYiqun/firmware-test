"""Static analysis checks for DMA with buffer alignment requirements."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate DMA aligned buffer code structure and required elements."""
    details: list[CheckDetail] = []

    # Check 1: DMA header included
    has_dma_h = scoped_contains(generated_code, 'zephyr/drivers/dma.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_header_included",
            passed=has_dma_h,
            expected="zephyr/drivers/dma.h included",
            actual="present" if has_dma_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: __aligned attribute used
    has_aligned = scoped_contains(generated_code, '__aligned', scope='code_only')
    details.append(
        CheckDetail(
            check_name="aligned_attribute_present",
            passed=has_aligned,
            expected="__aligned() attribute used for buffer declarations",
            actual="present" if has_aligned else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: No memalign() (not available in Zephyr RTOS)
    has_memalign = scoped_contains(generated_code, 'memalign(', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_memalign",
            passed=not has_memalign,
            expected="No memalign() — not available in Zephyr RTOS",
            actual="clean" if not has_memalign else "memalign() used — not a Zephyr API",
            check_type="hallucination",
        )
    )

    # Check 4: No posix_memalign() (POSIX, not Zephyr)
    has_posix_memalign = scoped_contains(generated_code, 'posix_memalign', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_posix_memalign",
            passed=not has_posix_memalign,
            expected="No posix_memalign() — POSIX API, not available in Zephyr RTOS",
            actual="clean" if not has_posix_memalign else "posix_memalign() used — POSIX API not in Zephyr",
            check_type="hallucination",
        )
    )

    # Check 5: dma_config and dma_start present
    has_dma_api = scoped_contains(generated_code, 'dma_config', scope='code_only') and scoped_contains(generated_code, 'dma_start', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_config_and_start_present",
            passed=has_dma_api,
            expected="dma_config() and dma_start() called",
            actual="present" if has_dma_api else "missing one or both DMA calls",
            check_type="exact_match",
        )
    )

    return details
