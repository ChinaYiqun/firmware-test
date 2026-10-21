"""Static analysis checks for BLE advertising with manufacturer data."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate BLE manufacturer data advertising structure."""
    details: list[CheckDetail] = []

    has_bt_h = scoped_contains(generated_code, 'zephyr/bluetooth/bluetooth.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="bluetooth_header",
            passed=has_bt_h,
            expected="zephyr/bluetooth/bluetooth.h included",
            actual="present" if has_bt_h else "missing",
            check_type="exact_match",
        )
    )

    has_manufacturer_data = scoped_contains(generated_code, 'BT_DATA_MANUFACTURER_DATA', scope='code_only')
    details.append(
        CheckDetail(
            check_name="manufacturer_data_type_used",
            passed=has_manufacturer_data,
            expected="BT_DATA_MANUFACTURER_DATA type used in ad[]",
            actual="present" if has_manufacturer_data else "missing — manufacturer data not set",
            check_type="exact_match",
        )
    )

    has_bt_data_bytes = scoped_contains(generated_code, 'BT_DATA_BYTES', scope='code_only')
    details.append(
        CheckDetail(
            check_name="bt_data_bytes_macro_used",
            passed=has_bt_data_bytes,
            expected="BT_DATA_BYTES macro used to build advertising data",
            actual="present" if has_bt_data_bytes else "missing",
            check_type="exact_match",
        )
    )

    has_bt_enable = scoped_contains(generated_code, 'bt_enable', scope='code_only')
    details.append(
        CheckDetail(
            check_name="bt_enable_called",
            passed=has_bt_enable,
            expected="bt_enable() called",
            actual="present" if has_bt_enable else "missing",
            check_type="exact_match",
        )
    )

    has_adv_start = scoped_contains(generated_code, 'bt_le_adv_start', scope='code_only')
    details.append(
        CheckDetail(
            check_name="bt_le_adv_start_called",
            passed=has_adv_start,
            expected="bt_le_adv_start() called",
            actual="present" if has_adv_start else "missing",
            check_type="exact_match",
        )
    )

    return details
