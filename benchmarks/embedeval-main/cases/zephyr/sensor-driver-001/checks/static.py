"""Static analysis checks for Zephyr sensor API temperature read."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate sensor code structure."""
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

    has_get = scoped_contains(generated_code, 'sensor_channel_get', scope='code_only')
    details.append(
        CheckDetail(
            check_name="channel_get",
            passed=has_get,
            expected="sensor_channel_get() called",
            actual="present" if has_get else "missing",
            check_type="exact_match",
        )
    )

    has_sv = scoped_contains(generated_code, 'sensor_value', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_value_struct",
            passed=has_sv,
            expected="struct sensor_value used",
            actual="present" if has_sv else "missing",
            check_type="exact_match",
        )
    )

    has_chan = scoped_contains(generated_code, 'SENSOR_CHAN', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_channel_enum",
            passed=has_chan,
            expected="SENSOR_CHAN_* enum used",
            actual="present" if has_chan else "missing",
            check_type="exact_match",
        )
    )

    return details
