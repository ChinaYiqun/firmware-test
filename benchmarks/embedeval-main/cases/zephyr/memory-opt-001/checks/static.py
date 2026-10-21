"""Static analysis checks for memory slab allocation."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate memory slab code structure."""
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

    # Check 2: K_MEM_SLAB_DEFINE used
    has_slab = scoped_contains(generated_code, 'K_MEM_SLAB_DEFINE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mem_slab_defined",
            passed=has_slab,
            expected="K_MEM_SLAB_DEFINE macro used",
            actual="present" if has_slab else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: k_mem_slab_alloc used
    has_alloc = scoped_contains(generated_code, 'k_mem_slab_alloc', scope='code_only')
    details.append(
        CheckDetail(
            check_name="slab_alloc_called",
            passed=has_alloc,
            expected="k_mem_slab_alloc() called",
            actual="present" if has_alloc else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: k_mem_slab_free used
    has_free = scoped_contains(generated_code, 'k_mem_slab_free', scope='code_only')
    details.append(
        CheckDetail(
            check_name="slab_free_called",
            passed=has_free,
            expected="k_mem_slab_free() called",
            actual="present" if has_free else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: NO heap allocation (malloc, calloc, k_malloc)
    heap_funcs = ["malloc(", "calloc(", "k_malloc(", "k_calloc("]
    has_heap = any(f in generated_code for f in heap_funcs)
    details.append(
        CheckDetail(
            check_name="no_heap_allocation",
            passed=not has_heap,
            expected="No malloc/calloc/k_malloc (heap-free)",
            actual="heap alloc found" if has_heap else "heap-free",
            check_type="constraint",
        )
    )

    return details
