"""Static analysis checks for DMA with cache coherency."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate DMA cache coherency code structure and required elements."""
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

    # Check 2: Cache header included (accept both old and new paths)
    has_cache_h = (
        scoped_contains(generated_code, 'zephyr/cache.h', scope='code_only')
        or scoped_contains(generated_code, 'zephyr/sys/cache.h', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="cache_header_included",
            passed=has_cache_h,
            expected="zephyr/cache.h or zephyr/sys/cache.h included",
            actual="present" if has_cache_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: Cache flush used
    has_flush = scoped_contains(generated_code, 'sys_cache_data_flush_range', scope='code_only')
    details.append(
        CheckDetail(
            check_name="cache_flush_present",
            passed=has_flush,
            expected="sys_cache_data_flush_range() called",
            actual="present" if has_flush else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: Cache invalidate used
    has_invd = scoped_contains(generated_code, 'sys_cache_data_invd_range', scope='code_only')
    details.append(
        CheckDetail(
            check_name="cache_invalidate_present",
            passed=has_invd,
            expected="sys_cache_data_invd_range() called",
            actual="present" if has_invd else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: __aligned attribute on destination buffer
    has_aligned = scoped_contains(generated_code, '__aligned', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dst_buffer_aligned",
            passed=has_aligned,
            expected="Destination buffer cache-line aligned with __aligned()",
            actual="present" if has_aligned else "missing",
            check_type="exact_match",
        )
    )

    return details
