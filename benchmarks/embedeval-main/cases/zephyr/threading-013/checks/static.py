"""Static analysis checks for shared memory IPC with producer-consumer handshake."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate shared memory IPC code structure."""
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

    # No FreeRTOS/Arduino contamination
    freertos_apis = [
        "xTaskCreate", "vTaskDelay", "xQueueCreate", "xSemaphoreCreate",
        "vTaskStartScheduler", "pdTRUE", "pdFALSE", "portMAX_DELAY",
    ]
    has_freertos = any(api in generated_code for api in freertos_apis)
    details.append(
        CheckDetail(
            check_name="no_freertos_contamination",
            passed=not has_freertos,
            expected="No FreeRTOS APIs present",
            actual="clean" if not has_freertos else "FreeRTOS API found",
            check_type="exact_match",
        )
    )

    # Has main function
    has_main = scoped_contains(generated_code, 'int main(', scope='code_only') or scoped_contains(generated_code, 'void main(', scope='code_only')
    details.append(
        CheckDetail(
            check_name="main_function_present",
            passed=has_main,
            expected="main() function defined",
            actual="present" if has_main else "missing",
            check_type="exact_match",
        )
    )

    # Has struct definition (shared memory layout)
    has_struct = scoped_contains(generated_code, 'struct ', scope='code_only') and scoped_contains(generated_code, '{', scope='code_only')
    details.append(
        CheckDetail(
            check_name="struct_definition_present",
            passed=has_struct,
            expected="struct definition for shared memory layout",
            actual="present" if has_struct else "missing",
            check_type="exact_match",
        )
    )

    return details
