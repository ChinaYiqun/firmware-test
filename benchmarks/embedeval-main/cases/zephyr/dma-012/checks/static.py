"""Static checks for dma-010: DMA cache coherence handling."""

import re

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    has_dma_h = scoped_contains(generated_code, 'drivers/dma.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_header_included",
            passed=has_dma_h,
            expected="zephyr/drivers/dma.h included",
            actual="present" if has_dma_h else "missing",
            check_type="exact_match",
        )
    )

    has_dma_config = (
        scoped_contains(generated_code, 'dma_config', scope='code_only') and scoped_contains(generated_code, 'dma_block_config', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="dma_structs_used",
            passed=has_dma_config,
            expected="dma_config and dma_block_config structs used",
            actual="present" if has_dma_config else "missing",
            check_type="constraint",
        )
    )

    has_start = scoped_contains(generated_code, 'dma_start', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_start_called",
            passed=has_start,
            expected="dma_start() called",
            actual="present" if has_start else "missing",
            check_type="exact_match",
        )
    )

    has_flush = bool(
        re.search(
            r"sys_cache_data_flush_range|"
            r"sys_cache_data_flush_all|"
            r"cache_data_flush",
            generated_code,
        )
    )
    details.append(
        CheckDetail(
            check_name="cache_flush_before_dma",
            passed=has_flush,
            expected=(
                "sys_cache_data_flush_range() called before DMA start so the "
                "DMA engine reads the CPU's latest stores"
            ),
            actual="present"
            if has_flush
            else "missing — DMA may read stale cached data",
            check_type="constraint",
        )
    )

    has_aligned = bool(re.search(r"__aligned\s*\(\s*\d+\s*\)", generated_code))
    details.append(
        CheckDetail(
            check_name="buffer_alignment",
            passed=has_aligned,
            expected="Buffers declared with __aligned() for cache-line alignment",
            actual="present" if has_aligned else "missing — cache line split risk",
            check_type="constraint",
        )
    )

    has_mem_to_mem = scoped_contains(generated_code, 'MEMORY_TO_MEMORY', scope='code_only')
    details.append(
        CheckDetail(
            check_name="direction_memory_to_memory",
            passed=has_mem_to_mem,
            expected="channel_direction = MEMORY_TO_MEMORY",
            actual="present" if has_mem_to_mem else "missing",
            check_type="exact_match",
        )
    )

    return details
