"""Static analysis checks for K_HEAP vs K_MEM_SLAB selection."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate heap and slab allocator usage code structure."""
    details: list[CheckDetail] = []

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

    has_heap_define = scoped_contains(generated_code, 'K_HEAP_DEFINE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="heap_defined",
            passed=has_heap_define,
            expected="K_HEAP_DEFINE macro used for variable-size allocator",
            actual="present" if has_heap_define else "missing",
            check_type="exact_match",
        )
    )

    has_slab_define = scoped_contains(generated_code, 'K_MEM_SLAB_DEFINE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="slab_defined",
            passed=has_slab_define,
            expected="K_MEM_SLAB_DEFINE macro used for fixed-size allocator",
            actual="present" if has_slab_define else "missing",
            check_type="exact_match",
        )
    )

    has_heap_alloc = scoped_contains(generated_code, 'k_heap_alloc', scope='code_only')
    details.append(
        CheckDetail(
            check_name="heap_alloc_called",
            passed=has_heap_alloc,
            expected="k_heap_alloc() called for variable-size allocation",
            actual="present" if has_heap_alloc else "missing",
            check_type="exact_match",
        )
    )

    has_slab_alloc = scoped_contains(generated_code, 'k_mem_slab_alloc', scope='code_only')
    details.append(
        CheckDetail(
            check_name="slab_alloc_called",
            passed=has_slab_alloc,
            expected="k_mem_slab_alloc() called for fixed-size allocation",
            actual="present" if has_slab_alloc else "missing",
            check_type="exact_match",
        )
    )

    has_heap_free = scoped_contains(generated_code, 'k_heap_free', scope='code_only')
    details.append(
        CheckDetail(
            check_name="heap_free_called",
            passed=has_heap_free,
            expected="k_heap_free() called to release heap memory",
            actual="present" if has_heap_free else "missing",
            check_type="exact_match",
        )
    )

    has_slab_free = scoped_contains(generated_code, 'k_mem_slab_free', scope='code_only')
    details.append(
        CheckDetail(
            check_name="slab_free_called",
            passed=has_slab_free,
            expected="k_mem_slab_free() called to release slab block",
            actual="present" if has_slab_free else "missing",
            check_type="exact_match",
        )
    )

    return details
