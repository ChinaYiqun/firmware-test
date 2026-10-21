"""Static analysis checks for sensor data-ready trigger."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate sensor trigger code structure."""
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

    has_trigger_set = scoped_contains(generated_code, 'sensor_trigger_set', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_trigger_set",
            passed=has_trigger_set,
            expected="sensor_trigger_set() called",
            actual="present" if has_trigger_set else "missing",
            check_type="exact_match",
        )
    )

    has_data_ready = scoped_contains(generated_code, 'SENSOR_TRIG_DATA_READY', scope='code_only')
    details.append(
        CheckDetail(
            check_name="data_ready_trigger_type",
            passed=has_data_ready,
            expected="SENSOR_TRIG_DATA_READY trigger type used",
            actual="present" if has_data_ready else "wrong or missing trigger type",
            check_type="exact_match",
        )
    )

    has_sensor_trigger_struct = scoped_contains(generated_code, 'sensor_trigger', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_trigger_struct",
            passed=has_sensor_trigger_struct,
            expected="struct sensor_trigger declared",
            actual="present" if has_sensor_trigger_struct else "missing",
            check_type="exact_match",
        )
    )

    has_callback = (
        scoped_contains(generated_code, 'const struct device *dev', scope='code_only')
        and scoped_contains(generated_code, 'const struct sensor_trigger *trig', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="callback_signature",
            passed=has_callback,
            expected="Callback with correct Zephyr trigger signature",
            actual="correct" if has_callback else "missing or wrong signature",
            check_type="exact_match",
        )
    )

    has_device_ready = scoped_contains(generated_code, 'device_is_ready', scope='code_only')
    details.append(
        CheckDetail(
            check_name="device_ready_check",
            passed=has_device_ready,
            expected="device_is_ready() called",
            actual="present" if has_device_ready else "missing",
            check_type="exact_match",
        )
    )

    return details
