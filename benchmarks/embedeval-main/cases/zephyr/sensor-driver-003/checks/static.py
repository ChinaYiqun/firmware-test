"""Static analysis checks for multi-channel accelerometer read."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate multi-channel sensor read code structure."""
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

    has_fetch = scoped_contains(generated_code, 'sensor_sample_fetch', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sample_fetch",
            passed=has_fetch,
            expected="sensor_sample_fetch() called",
            actual="present" if has_fetch else "missing",
            check_type="exact_match",
        )
    )

    has_accel_x = scoped_contains(generated_code, 'SENSOR_CHAN_ACCEL_X', scope='code_only')
    details.append(
        CheckDetail(
            check_name="accel_x_channel",
            passed=has_accel_x,
            expected="SENSOR_CHAN_ACCEL_X used",
            actual="present" if has_accel_x else "missing",
            check_type="exact_match",
        )
    )

    has_accel_y = scoped_contains(generated_code, 'SENSOR_CHAN_ACCEL_Y', scope='code_only')
    details.append(
        CheckDetail(
            check_name="accel_y_channel",
            passed=has_accel_y,
            expected="SENSOR_CHAN_ACCEL_Y used",
            actual="present" if has_accel_y else "missing",
            check_type="exact_match",
        )
    )

    has_accel_z = scoped_contains(generated_code, 'SENSOR_CHAN_ACCEL_Z', scope='code_only')
    details.append(
        CheckDetail(
            check_name="accel_z_channel",
            passed=has_accel_z,
            expected="SENSOR_CHAN_ACCEL_Z used",
            actual="present" if has_accel_z else "missing",
            check_type="exact_match",
        )
    )

    has_sensor_value = scoped_contains(generated_code, 'sensor_value', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_value_struct",
            passed=has_sensor_value,
            expected="struct sensor_value used",
            actual="present" if has_sensor_value else "missing",
            check_type="exact_match",
        )
    )

    has_channel_get = scoped_contains(generated_code, 'sensor_channel_get', scope='code_only')
    details.append(
        CheckDetail(
            check_name="channel_get",
            passed=has_channel_get,
            expected="sensor_channel_get() called",
            actual="present" if has_channel_get else "missing",
            check_type="exact_match",
        )
    )

    return details
