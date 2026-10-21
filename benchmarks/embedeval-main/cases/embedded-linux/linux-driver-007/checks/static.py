"""Static analysis checks for Linux DMA buffer driver."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate DMA buffer driver code structure."""
    details: list[CheckDetail] = []

    has_dma_h = scoped_contains(generated_code, 'linux/dma-mapping.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_mapping_header",
            passed=has_dma_h,
            expected="linux/dma-mapping.h included",
            actual="present" if has_dma_h else "missing",
            check_type="exact_match",
        )
    )

    has_dma_addr = scoped_contains(generated_code, 'dma_addr_t', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_addr_t_used",
            passed=has_dma_addr,
            expected="dma_addr_t type used for DMA handle",
            actual="present" if has_dma_addr else "missing",
            check_type="exact_match",
        )
    )

    has_alloc = scoped_contains(generated_code, 'dma_alloc_coherent', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_alloc_coherent_used",
            passed=has_alloc,
            expected="dma_alloc_coherent() called for buffer allocation",
            actual="present" if has_alloc else "MISSING (wrong DMA allocation API!)",
            check_type="exact_match",
        )
    )

    has_free = scoped_contains(generated_code, 'dma_free_coherent', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_free_coherent_in_cleanup",
            passed=has_free,
            expected="dma_free_coherent() called in remove/cleanup",
            actual="present" if has_free else "MISSING (DMA memory leak!)",
            check_type="exact_match",
        )
    )

    has_gfp = scoped_contains(generated_code, 'GFP_KERNEL', scope='code_only')
    details.append(
        CheckDetail(
            check_name="gfp_kernel_flags",
            passed=has_gfp,
            expected="GFP_KERNEL flags used in dma_alloc_coherent",
            actual="present" if has_gfp else "missing",
            check_type="exact_match",
        )
    )

    return details
