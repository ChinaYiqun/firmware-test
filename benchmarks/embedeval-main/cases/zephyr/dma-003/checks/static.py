"""Static analysis checks for DMA circular buffer."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate DMA circular buffer code structure and required elements."""
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

    # Check 2: cyclic flag set in block config
    has_cyclic = scoped_contains(generated_code, 'cyclic', scope='code_only')
    details.append(
        CheckDetail(
            check_name="cyclic_flag_set",
            passed=has_cyclic,
            expected="cyclic field set in dma_block_config",
            actual="present" if has_cyclic else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: dma_reload() called
    has_reload = scoped_contains(generated_code, 'dma_reload', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_reload_called",
            passed=has_reload,
            expected="dma_reload() called in callback for continuous operation",
            actual="present" if has_reload else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: dma_stop() called
    has_stop = scoped_contains(generated_code, 'dma_stop', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_stop_called",
            passed=has_stop,
            expected="dma_stop() called to terminate circular transfer",
            actual="present" if has_stop else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: dma_config() and dma_start() present
    has_config = scoped_contains(generated_code, 'dma_config(', scope='code_only')
    has_start = scoped_contains(generated_code, 'dma_start(', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_config_and_start",
            passed=has_config and has_start,
            expected="dma_config() and dma_start() both called",
            actual=f"config={has_config}, start={has_start}",
            check_type="exact_match",
        )
    )

    return details
