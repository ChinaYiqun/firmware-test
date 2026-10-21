"""Static analysis checks for BLE connection callbacks."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate BLE connection callback code structure."""
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

    has_conn_cb = scoped_contains(generated_code, 'bt_conn_cb', scope='code_only')
    details.append(
        CheckDetail(
            check_name="bt_conn_cb_defined",
            passed=has_conn_cb,
            expected="struct bt_conn_cb defined",
            actual="present" if has_conn_cb else "missing",
            check_type="exact_match",
        )
    )

    has_cb_register = scoped_contains(generated_code, 'bt_conn_cb_register', scope='code_only') or scoped_contains(generated_code, 'BT_CONN_CB_DEFINE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="conn_cb_registered",
            passed=has_cb_register,
            expected="bt_conn_cb_register() or BT_CONN_CB_DEFINE() used",
            actual="present" if has_cb_register else "missing — callbacks not registered",
            check_type="exact_match",
        )
    )

    has_connected_cb = scoped_contains(generated_code, '.connected', scope='code_only') or scoped_contains(generated_code, 'connected', scope='code_only')
    has_disconnected_cb = scoped_contains(generated_code, '.disconnected', scope='code_only') or scoped_contains(generated_code, 'disconnected', scope='code_only')
    details.append(
        CheckDetail(
            check_name="both_callbacks_defined",
            passed=has_connected_cb and has_disconnected_cb,
            expected="Both .connected and .disconnected callbacks defined",
            actual=f"connected={has_connected_cb}, disconnected={has_disconnected_cb}",
            check_type="constraint",
        )
    )

    has_addr_print = scoped_contains(generated_code, 'bt_addr_le_to_str', scope='code_only') or scoped_contains(generated_code, 'bt_conn_get_info', scope='code_only')
    details.append(
        CheckDetail(
            check_name="peer_address_printed",
            passed=has_addr_print,
            expected="Peer address retrieved and printed on connect",
            actual="present" if has_addr_print else "missing",
            check_type="exact_match",
        )
    )

    return details
