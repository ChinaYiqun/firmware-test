"""Static analysis checks for Linux IIO ADC driver skeleton."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate IIO driver code structure."""
    details: list[CheckDetail] = []

    has_module_h = scoped_contains(generated_code, 'linux/module.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="module_header",
            passed=has_module_h,
            expected="linux/module.h included",
            actual="present" if has_module_h else "missing",
            check_type="exact_match",
        )
    )

    has_iio_h = scoped_contains(generated_code, 'linux/iio/iio.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="iio_header",
            passed=has_iio_h,
            expected="linux/iio/iio.h included",
            actual="present" if has_iio_h else "missing",
            check_type="exact_match",
        )
    )

    has_license = scoped_contains(generated_code, 'MODULE_LICENSE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="module_license",
            passed=has_license,
            expected="MODULE_LICENSE defined",
            actual="present" if has_license else "missing",
            check_type="exact_match",
        )
    )

    has_chan_spec = scoped_contains(generated_code, 'iio_chan_spec', scope='code_only')
    details.append(
        CheckDetail(
            check_name="iio_chan_spec_defined",
            passed=has_chan_spec,
            expected="struct iio_chan_spec array defined",
            actual="present" if has_chan_spec else "missing",
            check_type="exact_match",
        )
    )

    has_iio_voltage = scoped_contains(generated_code, 'IIO_VOLTAGE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="iio_voltage_type",
            passed=has_iio_voltage,
            expected="IIO_VOLTAGE channel type set",
            actual="present" if has_iio_voltage else "missing",
            check_type="exact_match",
        )
    )

    has_read_raw = scoped_contains(generated_code, 'read_raw', scope='code_only')
    details.append(
        CheckDetail(
            check_name="read_raw_callback",
            passed=has_read_raw,
            expected="read_raw callback defined in iio_info",
            actual="present" if has_read_raw else "missing",
            check_type="exact_match",
        )
    )

    has_iio_info = scoped_contains(generated_code, 'iio_info', scope='code_only')
    details.append(
        CheckDetail(
            check_name="iio_info_struct",
            passed=has_iio_info,
            expected="struct iio_info defined",
            actual="present" if has_iio_info else "missing",
            check_type="exact_match",
        )
    )

    return details
