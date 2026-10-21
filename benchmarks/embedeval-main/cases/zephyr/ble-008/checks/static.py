"""Static analysis checks for BLE central (scanner + connect)."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate BLE central code structure."""
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

    has_conn_h = scoped_contains(generated_code, 'zephyr/bluetooth/conn.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="conn_header",
            passed=has_conn_h,
            expected="zephyr/bluetooth/conn.h included",
            actual="present" if has_conn_h else "missing",
            check_type="exact_match",
        )
    )

    has_scan_start = scoped_contains(generated_code, 'bt_le_scan_start', scope='code_only')
    details.append(
        CheckDetail(
            check_name="scan_started",
            passed=has_scan_start,
            expected="bt_le_scan_start() called",
            actual="present" if has_scan_start else "missing",
            check_type="exact_match",
        )
    )

    has_conn_create = scoped_contains(generated_code, 'bt_conn_le_create', scope='code_only')
    details.append(
        CheckDetail(
            check_name="bt_conn_le_create_called",
            passed=has_conn_create,
            expected="bt_conn_le_create() called to initiate connection",
            actual="present" if has_conn_create else "missing",
            check_type="exact_match",
        )
    )

    has_gatt_discover = scoped_contains(generated_code, 'bt_gatt_discover', scope='code_only')
    details.append(
        CheckDetail(
            check_name="bt_gatt_discover_called",
            passed=has_gatt_discover,
            expected="bt_gatt_discover() called after connecting",
            actual="present" if has_gatt_discover else "missing",
            check_type="exact_match",
        )
    )

    # Hallucination: BLEDevice.connect() is Python/bleak, not Zephyr C
    uses_bledevice = scoped_contains(generated_code, 'BLEDevice', scope='code_only') or scoped_contains(generated_code, 'BLEDevice.connect', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_bledevice_connect",
            passed=not uses_bledevice,
            expected="BLEDevice.connect() NOT used (Python API, not Zephyr C)",
            actual="clean" if not uses_bledevice else "HALLUCINATION: BLEDevice is Python, not C",
            check_type="exact_match",
        )
    )

    # Hallucination: gap_connect does not exist in Zephyr
    uses_gap_connect = scoped_contains(generated_code, 'gap_connect', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_gap_connect",
            passed=not uses_gap_connect,
            expected="gap_connect() NOT used (does not exist in Zephyr)",
            actual="clean" if not uses_gap_connect else "HALLUCINATION: gap_connect() does not exist",
            check_type="exact_match",
        )
    )

    return details
