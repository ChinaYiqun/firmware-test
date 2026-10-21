"""Static analysis checks for sensor attribute configuration before read."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate sensor attribute configuration code structure."""
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

    has_attr_set = scoped_contains(generated_code, 'sensor_attr_set', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_attr_set",
            passed=has_attr_set,
            expected="sensor_attr_set() called",
            actual="present" if has_attr_set else "missing",
            check_type="exact_match",
        )
    )

    has_sampling_freq = scoped_contains(generated_code, 'SENSOR_ATTR_SAMPLING_FREQUENCY', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sampling_frequency_attr",
            passed=has_sampling_freq,
            expected="SENSOR_ATTR_SAMPLING_FREQUENCY used",
            actual="present" if has_sampling_freq else "wrong or missing attribute",
            check_type="exact_match",
        )
    )

    has_full_scale = scoped_contains(generated_code, 'SENSOR_ATTR_FULL_SCALE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="full_scale_attr",
            passed=has_full_scale,
            expected="SENSOR_ATTR_FULL_SCALE used",
            actual="present" if has_full_scale else "wrong or missing attribute",
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

    has_sensor_value = scoped_contains(generated_code, 'sensor_value', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_value_struct",
            passed=has_sensor_value,
            expected="struct sensor_value used for attribute and reading",
            actual="present" if has_sensor_value else "missing",
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
