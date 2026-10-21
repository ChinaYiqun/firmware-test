"""Static analysis checks for custom sensor driver registration."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate custom sensor driver code structure."""
    details: list[CheckDetail] = []

    has_sensor_h = scoped_contains(generated_code, 'zephyr/drivers/sensor.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_header",
            passed=has_sensor_h,
            expected="zephyr/drivers/sensor.h included",
            actual="present" if has_sensor_h else "missing",
            check_type="exact_match",
        )
    )

    has_register_macro = scoped_contains(generated_code, 'SENSOR_DEVICE_DT_INST_DEFINE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_device_dt_inst_define",
            passed=has_register_macro,
            expected="SENSOR_DEVICE_DT_INST_DEFINE macro used",
            actual="present" if has_register_macro else "missing (wrong registration method)",
            check_type="exact_match",
        )
    )

    has_driver_api = scoped_contains(generated_code, 'sensor_driver_api', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_driver_api_struct",
            passed=has_driver_api,
            expected="struct sensor_driver_api used for API table",
            actual="present" if has_driver_api else "wrong struct name or missing",
            check_type="exact_match",
        )
    )

    has_sample_fetch = scoped_contains(generated_code, 'sample_fetch', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sample_fetch_implemented",
            passed=has_sample_fetch,
            expected="sample_fetch callback implemented",
            actual="present" if has_sample_fetch else "missing",
            check_type="exact_match",
        )
    )

    has_channel_get = scoped_contains(generated_code, 'channel_get', scope='code_only')
    details.append(
        CheckDetail(
            check_name="channel_get_implemented",
            passed=has_channel_get,
            expected="channel_get callback implemented",
            actual="present" if has_channel_get else "missing",
            check_type="exact_match",
        )
    )

    has_correct_init_sig = (
        scoped_contains(generated_code, 'const struct device *dev', scope='code_only')
        and scoped_contains(generated_code, 'my_sensor_init', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="init_function_signature",
            passed=has_correct_init_sig,
            expected="Init function with (const struct device *dev) signature",
            actual="correct" if has_correct_init_sig else "wrong or missing",
            check_type="exact_match",
        )
    )

    has_enotsup = scoped_contains(generated_code, 'ENOTSUP', scope='code_only')
    details.append(
        CheckDetail(
            check_name="unsupported_channel_error",
            passed=has_enotsup,
            expected="-ENOTSUP returned for unsupported channels",
            actual="present" if has_enotsup else "missing",
            check_type="exact_match",
        )
    )

    return details
