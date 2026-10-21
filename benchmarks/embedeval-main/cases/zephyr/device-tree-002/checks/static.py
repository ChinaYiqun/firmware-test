"""Static analysis checks for SPI NOR flash Device Tree overlay."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate SPI NOR flash overlay syntax and structure."""
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

    # Check 2: compatible string present and in correct format
    has_compatible = scoped_contains(generated_code, 'compatible = "', scope='code_only')
    details.append(
        CheckDetail(
            check_name="compatible_present",
            passed=has_compatible,
            expected='compatible = "..." property',
            actual="present" if has_compatible else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: reg property present
    has_reg = scoped_contains(generated_code, 'reg = <', scope='code_only')
    details.append(
        CheckDetail(
            check_name="reg_property_present",
            passed=has_reg,
            expected="reg = <...> property",
            actual="present" if has_reg else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: status property present
    has_status = scoped_contains(generated_code, 'status = "', scope='code_only')
    details.append(
        CheckDetail(
            check_name="status_property_present",
            passed=has_status,
            expected='status = "..." property',
            actual="present" if has_status else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: spi-max-frequency property present (AI commonly omits this)
    has_freq = scoped_contains(generated_code, 'spi-max-frequency', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spi_max_frequency_present",
            passed=has_freq,
            expected="spi-max-frequency property",
            actual="present" if has_freq else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: spi0 bus referenced (not direct root node)
    has_spi_bus = scoped_contains(generated_code, 'spi0', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spi_bus_referenced",
            passed=has_spi_bus,
            expected="spi0 bus reference",
            actual="present" if has_spi_bus else "missing",
            check_type="constraint",
        )
    )

    return details
