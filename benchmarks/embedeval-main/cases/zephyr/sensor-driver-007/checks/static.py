"""Static analysis checks for sensor FIFO batch read."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate sensor FIFO batch read code structure."""
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

    has_watermark = (
        scoped_contains(generated_code, 'SENSOR_ATTR_FIFO_WATERMARK', scope='code_only')
        or "watermark" in generated_code.lower()
        or "fifo_watermark" in generated_code.lower()
    )
    details.append(
        CheckDetail(
            check_name="watermark_check",
            passed=has_watermark,
            expected="FIFO watermark checked before burst read",
            actual="present" if has_watermark else "missing (reading fixed count without checking watermark)",
            check_type="exact_match",
        )
    )

    has_sensor_attr_get = scoped_contains(generated_code, 'sensor_attr_get', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sensor_attr_get_called",
            passed=has_sensor_attr_get,
            expected="sensor_attr_get() used to read watermark level",
            actual="present" if has_sensor_attr_get else "missing",
            check_type="exact_match",
        )
    )

    has_accel_chan = (
        scoped_contains(generated_code, 'SENSOR_CHAN_ACCEL_X', scope='code_only')
        or scoped_contains(generated_code, 'SENSOR_CHAN_ACCEL_XYZ', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="accel_channel_used",
            passed=has_accel_chan,
            expected="Accelerometer channel (SENSOR_CHAN_ACCEL_X/XYZ) used",
            actual="present" if has_accel_chan else "missing",
            check_type="exact_match",
        )
    )

    has_fifo_max = (
        scoped_contains(generated_code, 'FIFO_MAX_DEPTH', scope='code_only')
        or scoped_contains(generated_code, 'FIFO_SIZE', scope='code_only')
        or "fifo_max" in generated_code.lower()
    )
    details.append(
        CheckDetail(
            check_name="fifo_max_depth_defined",
            passed=has_fifo_max,
            expected="Maximum FIFO depth constant defined for buffer sizing",
            actual="present" if has_fifo_max else "missing",
            check_type="exact_match",
        )
    )

    has_buffer_guard = (
        scoped_contains(generated_code, 'FIFO_MAX_DEPTH', scope='code_only')
        and (scoped_contains(generated_code, '> FIFO_MAX_DEPTH', scope='code_only') or scoped_contains(generated_code, '>= FIFO_MAX_DEPTH', scope='code_only')
             or scoped_contains(generated_code, 'count > ', scope='code_only') or scoped_contains(generated_code, 'count >= ', scope='code_only'))
    )
    details.append(
        CheckDetail(
            check_name="buffer_overflow_guard",
            passed=has_buffer_guard,
            expected="Guard preventing burst read beyond buffer capacity",
            actual="present" if has_buffer_guard else "missing (potential buffer overflow)",
            check_type="exact_match",
        )
    )

    return details
