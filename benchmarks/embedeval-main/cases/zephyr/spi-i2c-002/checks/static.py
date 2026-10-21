"""Static analysis checks for SPI loopback test."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate SPI loopback code structure and required elements."""
    details: list[CheckDetail] = []

    # Check 1: SPI header included
    has_spi_h = scoped_contains(generated_code, 'zephyr/drivers/spi.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spi_header_included",
            passed=has_spi_h,
            expected="zephyr/drivers/spi.h included",
            actual="present" if has_spi_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: Device obtained via DT
    has_dev_get = (
        scoped_contains(generated_code, 'DEVICE_DT_GET', scope='code_only')
        or scoped_contains(generated_code, 'device_get_binding', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="device_binding",
            passed=has_dev_get,
            expected="DEVICE_DT_GET or device_get_binding used",
            actual="present" if has_dev_get else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: spi_transceive called
    has_transceive = scoped_contains(generated_code, 'spi_transceive', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spi_transceive_called",
            passed=has_transceive,
            expected="spi_transceive() called",
            actual="present" if has_transceive else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: spi_buf_set structures used
    has_buf_set = scoped_contains(generated_code, 'spi_buf_set', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spi_buf_set_used",
            passed=has_buf_set,
            expected="struct spi_buf_set defined",
            actual="present" if has_buf_set else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: spi_config struct used
    has_spi_cfg = scoped_contains(generated_code, 'spi_config', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spi_config_used",
            passed=has_spi_cfg,
            expected="struct spi_config defined",
            actual="present" if has_spi_cfg else "missing",
            check_type="exact_match",
        )
    )

    return details
