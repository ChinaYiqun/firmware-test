"""Static checks for ESP-IDF high-resolution periodic timer."""
from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    details.append(CheckDetail(
        check_name="esp_timer_header",
        passed=scoped_contains(generated_code, 'esp_timer.h', scope='code_only'),
        expected="esp_timer.h included",
        actual="present" if scoped_contains(generated_code, 'esp_timer.h', scope='code_only') else "missing",
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
        check_name="esp_timer_create_called",
        passed=scoped_contains(generated_code, 'esp_timer_create', scope='code_only'),
        expected="esp_timer_create() called",
        actual="present" if scoped_contains(generated_code, 'esp_timer_create', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    details.append(CheckDetail(
        check_name="esp_timer_start_periodic_called",
        passed=scoped_contains(generated_code, 'esp_timer_start_periodic', scope='code_only'),
        expected="esp_timer_start_periodic() called",
        actual="present" if scoped_contains(generated_code, 'esp_timer_start_periodic', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    details.append(CheckDetail(
        check_name="esp_timer_delete_called",
        passed=scoped_contains(generated_code, 'esp_timer_delete', scope='code_only'),
        expected="esp_timer_delete() called for cleanup",
        actual="present" if scoped_contains(generated_code, 'esp_timer_delete', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    details.append(CheckDetail(
        check_name="callback_defined",
        passed=scoped_contains(generated_code, 'esp_timer_create_args_t', scope='code_only'),
        expected="esp_timer_create_args_t with .callback field",
        actual="present" if scoped_contains(generated_code, 'esp_timer_create_args_t', scope='code_only') else "missing",
        check_type="exact_match",
    ))

    # Cross-platform hallucination checks
    zephyr_apis = ["k_timer_start", "k_timer_init", "k_sleep", "K_MSEC"]
    found_zephyr = [api for api in zephyr_apis if api in generated_code]
    details.append(CheckDetail(
        check_name="no_zephyr_timer_apis",
        passed=not found_zephyr,
        expected="No Zephyr timer APIs in ESP-IDF code",
        actual="clean" if not found_zephyr else f"found Zephyr APIs: {found_zephyr}",
        check_type="hallucination",
    ))

    stm32_apis = ["HAL_TIM_Base_Start", "TIM_HandleTypeDef", "HAL_Init"]
    found_stm32 = [api for api in stm32_apis if api in generated_code]
    details.append(CheckDetail(
        check_name="no_stm32_hal_apis",
        passed=not found_stm32,
        expected="No STM32 HAL timer APIs",
        actual="clean" if not found_stm32 else f"found STM32 HAL: {found_stm32}",
        check_type="hallucination",
    ))

    return details
