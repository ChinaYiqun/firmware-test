"""Static analysis checks for Device Tree DMA channel assignment overlay."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate Device Tree DMA assignment syntax and structure."""
    details: list[CheckDetail] = []

    # Check 1: Braces balanced
    open_count = generated_code.count("{")
    close_count = generated_code.count("}")
    braces_match = open_count == close_count and open_count > 0
    details.append(
        CheckDetail(
            check_name="braces_balanced",
            passed=braces_match,
            expected="Matching opening/closing braces",
            actual=f"open={open_count}, close={close_count}",
            check_type="syntax",
        )
    )

    # Check 2: dmas property present
    has_dmas = scoped_contains(generated_code, 'dmas = ', scope='code_only') or scoped_contains(generated_code, 'dmas=', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dmas_property_present",
            passed=has_dmas,
            expected="dmas property present",
            actual="present" if has_dmas else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: dma-names property present
    has_dma_names = scoped_contains(generated_code, 'dma-names', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_names_property_present",
            passed=has_dma_names,
            expected="dma-names property present",
            actual="present" if has_dma_names else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: uart0 node referenced
    has_uart0 = scoped_contains(generated_code, '&uart0', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uart0_node_referenced",
            passed=has_uart0,
            expected="&uart0 node reference present",
            actual="present" if has_uart0 else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: DMA phandle reference format (uses &dma)
    has_dma_phandle = scoped_contains(generated_code, '<&dma', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dma_phandle_format",
            passed=has_dma_phandle,
            expected="DMA phandle reference format <&dma...>",
            actual="present" if has_dma_phandle else "missing - must use phandle format",
            check_type="exact_match",
        )
    )

    return details
