"""Static analysis checks for SPI full-duplex transfer."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate SPI full-duplex code structure and required elements."""
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

    # Check 2: spi_transceive used (full-duplex API)
    has_transceive = scoped_contains(generated_code, 'spi_transceive', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spi_transceive_used",
            passed=has_transceive,
            expected="spi_transceive() used for full-duplex transfer",
            actual="present" if has_transceive else "missing - must use spi_transceive for simultaneous TX/RX",
            check_type="exact_match",
        )
    )

    # Check 3: spi_config with frequency
    has_config_freq = scoped_contains(generated_code, 'frequency', scope='code_only') and scoped_contains(generated_code, 'spi_config', scope='code_only')
    details.append(
        CheckDetail(
            check_name="spi_config_with_frequency",
            passed=has_config_freq,
            expected="spi_config struct with frequency field",
            actual="present" if has_config_freq else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: No cross-platform APIs (hallucination guards)
    has_hal_spi = scoped_contains(generated_code, 'HAL_SPI_TransmitReceive', scope='code_only')
    has_arduino_spi = scoped_contains(generated_code, 'SPI.transfer', scope='code_only')
    no_cross_platform = not has_hal_spi and not has_arduino_spi
    details.append(
        CheckDetail(
            check_name="no_cross_platform_spi_api",
            passed=no_cross_platform,
            expected="No HAL_SPI_TransmitReceive() or SPI.transfer() — use Zephyr spi_transceive()",
            actual="clean" if no_cross_platform else f"HAL={has_hal_spi}, Arduino={has_arduino_spi}",
            check_type="hallucination",
        )
    )

    # Check 5: DEVICE_DT_GET used
    has_dev_get = scoped_contains(generated_code, 'DEVICE_DT_GET', scope='code_only')
    details.append(
        CheckDetail(
            check_name="device_dt_get_used",
            passed=has_dev_get,
            expected="DEVICE_DT_GET used to obtain SPI device",
            actual="present" if has_dev_get else "missing",
            check_type="exact_match",
        )
    )

    return details
