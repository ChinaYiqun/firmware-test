"""Static checks for ESP-IDF SPI master half-duplex write."""
from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    details.append(CheckDetail(
        check_name="spi_master_header",
        passed=scoped_contains(generated_code, 'driver/spi_master.h', scope='code_only'),
        expected="driver/spi_master.h included",
        actual="present" if scoped_contains(generated_code, 'driver/spi_master.h', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    details.append(CheckDetail(
        check_name="app_main_defined",
        passed=scoped_contains(generated_code, 'app_main', scope='code_only'),
        expected="app_main() entry point",
        actual="present" if scoped_contains(generated_code, 'app_main', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    details.append(CheckDetail(
        check_name="spi_bus_initialize_called",
        passed=scoped_contains(generated_code, 'spi_bus_initialize', scope='code_only'),
        expected="spi_bus_initialize() called",
        actual="present" if scoped_contains(generated_code, 'spi_bus_initialize', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    details.append(CheckDetail(
        check_name="spi_bus_add_device_called",
        passed=scoped_contains(generated_code, 'spi_bus_add_device', scope='code_only'),
        expected="spi_bus_add_device() called",
        actual="present" if scoped_contains(generated_code, 'spi_bus_add_device', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    details.append(CheckDetail(
        check_name="spi_device_transmit_called",
        passed=scoped_contains(generated_code, 'spi_device_transmit', scope='code_only'),
        expected="spi_device_transmit() called",
        actual="present" if scoped_contains(generated_code, 'spi_device_transmit', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    details.append(CheckDetail(
        check_name="spi_bus_config_struct",
        passed=scoped_contains(generated_code, 'spi_bus_config_t', scope='code_only'),
        expected="spi_bus_config_t struct for bus configuration",
        actual="present" if scoped_contains(generated_code, 'spi_bus_config_t', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    # Cross-platform hallucination checks
    zephyr_apis = ["spi_transceive", "k_sleep", "DEVICE_DT_GET", "struct spi_config"]
    found_zephyr = [api for api in zephyr_apis if api in generated_code]
    details.append(CheckDetail(
        check_name="no_zephyr_apis",
        passed=not found_zephyr,
        expected="No Zephyr SPI APIs in ESP-IDF code",
        actual="clean" if not found_zephyr else f"found Zephyr APIs: {found_zephyr}",
        check_type="hallucination",
    ))

    stm32_apis = ["HAL_SPI_Transmit", "SPI_HandleTypeDef", "HAL_Init"]
    found_stm32 = [api for api in stm32_apis if api in generated_code]
    details.append(CheckDetail(
        check_name="no_stm32_hal_apis",
        passed=not found_stm32,
        expected="No STM32 HAL APIs",
        actual="clean" if not found_stm32 else f"found STM32 HAL: {found_stm32}",
        check_type="hallucination",
    ))

    return details
