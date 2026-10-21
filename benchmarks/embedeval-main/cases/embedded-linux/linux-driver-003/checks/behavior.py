"""Behavioral checks for Linux IIO ADC driver skeleton."""

import re

from embedeval.check_utils import (
    check_no_cross_platform_apis,
    extract_error_blocks,
    scoped_contains,
    strip_comments,
)
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate IIO driver behavioral properties."""
    details: list[CheckDetail] = []

    stripped = strip_comments(generated_code)

    # Check 1: read_raw returns IIO_VAL_INT (not 0 or 1)
    has_iio_val_int = scoped_contains(generated_code, 'IIO_VAL_INT', scope='code_only')
    details.append(
        CheckDetail(
            check_name="read_raw_returns_iio_val_int",
            passed=has_iio_val_int,
            expected="read_raw returns IIO_VAL_INT for RAW channel reads",
            actual="present" if has_iio_val_int else "MISSING (sysfs shows empty!)",
            check_type="constraint",
        )
    )

    # Check 2: IIO_CHAN_INFO_RAW handled in read_raw switch/if
    has_raw_mask = scoped_contains(generated_code, 'IIO_CHAN_INFO_RAW', scope='code_only')
    details.append(
        CheckDetail(
            check_name="iio_chan_info_raw_handled",
            passed=has_raw_mask,
            expected="IIO_CHAN_INFO_RAW case handled in read_raw",
            actual="present" if has_raw_mask else "missing",
            check_type="constraint",
        )
    )

    # Check 3: Uses devm_ prefixed alloc (not manual iio_device_alloc)
    has_devm_alloc = scoped_contains(generated_code, 'devm_iio_device_alloc', scope='code_only')
    details.append(
        CheckDetail(
            check_name="devm_iio_device_alloc_used",
            passed=has_devm_alloc,
            expected="devm_iio_device_alloc() for automatic cleanup",
            actual="present" if has_devm_alloc else "missing (manual alloc needs matching free)",
            check_type="constraint",
        )
    )

    # Check 4: devm_iio_device_register or iio_device_register called
    has_register = (
        scoped_contains(generated_code, 'devm_iio_device_register', scope='code_only')
        or scoped_contains(generated_code, 'iio_device_register', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="iio_device_registered",
            passed=has_register,
            expected="iio_device_register() or devm_iio_device_register() called",
            actual="present" if has_register else "MISSING (device not visible!)",
            check_type="constraint",
        )
    )

    # Check 5: indio_dev->info assigned (links read_raw to device)
    has_info_assign = scoped_contains(generated_code, '->info', scope='code_only') or scoped_contains(generated_code, '.info', scope='code_only')
    details.append(
        CheckDetail(
            check_name="iio_info_assigned",
            passed=has_info_assign,
            expected="indio_dev->info assigned to iio_info struct",
            actual="present" if has_info_assign else "MISSING (read_raw never called!)",
            check_type="constraint",
        )
    )

    # Check 6: num_channels set (otherwise IIO reports 0 channels)
    has_num_channels = scoped_contains(generated_code, 'num_channels', scope='code_only')
    details.append(
        CheckDetail(
            check_name="num_channels_set",
            passed=has_num_channels,
            expected="indio_dev->num_channels set",
            actual="present" if has_num_channels else "missing (0 channels exported)",
            check_type="constraint",
        )
    )

    # Check 7: Error path handles allocation failure (-ENOMEM)
    # LLM failure: calling devm_iio_device_alloc, not checking NULL, proceeding to crash
    error_blocks = extract_error_blocks(generated_code)
    has_enomem_check = (
        scoped_contains(generated_code, 'ENOMEM', scope='code_only')
        or scoped_contains(generated_code, '!indio_dev', scope='code_only')
        or bool(re.search(r'if\s*\(\s*!\s*\w+\s*\)', generated_code))
    )
    details.append(
        CheckDetail(
            check_name="allocation_failure_handled",
            passed=has_enomem_check,
            expected="-ENOMEM returned when devm_iio_device_alloc fails",
            actual="present" if has_enomem_check else "allocation failure not handled",
            check_type="constraint",
        )
    )

    # Check 8: No Zephyr API contamination
    zephyr_apis = ["k_work_submit", "k_thread_create", "K_THREAD_DEFINE",
                   "k_mutex_lock", "k_sleep("]
    has_zephyr = any(api in generated_code for api in zephyr_apis)
    details.append(
        CheckDetail(
            check_name="no_zephyr_apis",
            passed=not has_zephyr,
            expected="No Zephyr RTOS APIs in Linux IIO driver",
            actual="clean" if not has_zephyr else "WRONG PLATFORM: Zephyr APIs found",
            check_type="constraint",
        )
    )

    # Check: No cross-platform API contamination
    cross_plat = check_no_cross_platform_apis(generated_code, skip_platforms=["Linux_Userspace", "POSIX"])
    details.append(CheckDetail(
        check_name="no_cross_platform_apis",
        passed=len(cross_plat) == 0,
        expected="No FreeRTOS/Arduino/STM32_HAL APIs (Linux/POSIX is expected)",
        actual="clean" if not cross_plat else f"found: {[a for a, _ in cross_plat]}",
        check_type="constraint",
    ))

    return details
