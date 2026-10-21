"""Static analysis checks for BLE peripheral with notifications."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate BLE notify peripheral code structure."""
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

    has_gatt_h = scoped_contains(generated_code, 'zephyr/bluetooth/gatt.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="gatt_header",
            passed=has_gatt_h,
            expected="zephyr/bluetooth/gatt.h included",
            actual="present" if has_gatt_h else "missing",
            check_type="exact_match",
        )
    )

    has_notify_flag = scoped_contains(generated_code, 'BT_GATT_CHRC_NOTIFY', scope='code_only')
    details.append(
        CheckDetail(
            check_name="chrc_notify_flag",
            passed=has_notify_flag,
            expected="BT_GATT_CHRC_NOTIFY property set on characteristic",
            actual="present" if has_notify_flag else "missing",
            check_type="exact_match",
        )
    )

    has_ccc = scoped_contains(generated_code, 'BT_GATT_CCC', scope='code_only')
    details.append(
        CheckDetail(
            check_name="ccc_descriptor",
            passed=has_ccc,
            expected="BT_GATT_CCC descriptor added to service",
            actual="present" if has_ccc else "missing — client cannot enable notifications",
            check_type="exact_match",
        )
    )

    has_notify = scoped_contains(generated_code, 'bt_gatt_notify', scope='code_only')
    details.append(
        CheckDetail(
            check_name="bt_gatt_notify_called",
            passed=has_notify,
            expected="bt_gatt_notify() called",
            actual="present" if has_notify else "missing",
            check_type="exact_match",
        )
    )

    has_svc_define = scoped_contains(generated_code, 'BT_GATT_SERVICE_DEFINE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="gatt_service_defined",
            passed=has_svc_define,
            expected="BT_GATT_SERVICE_DEFINE macro used",
            actual="present" if has_svc_define else "missing",
            check_type="exact_match",
        )
    )

    has_conn_ref = scoped_contains(generated_code, 'bt_conn_ref', scope='code_only')
    details.append(
        CheckDetail(
            check_name="conn_ref_called",
            passed=has_conn_ref,
            expected="bt_conn_ref() called to hold connection reference",
            actual="present" if has_conn_ref else "missing",
            check_type="exact_match",
        )
    )

    return details
