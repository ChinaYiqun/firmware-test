"""Static analysis checks for MQTT client."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate MQTT code structure."""
    details: list[CheckDetail] = []

    has_mqtt_h = scoped_contains(generated_code, 'zephyr/net/mqtt.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mqtt_header",
            passed=has_mqtt_h,
            expected="zephyr/net/mqtt.h included",
            actual="present" if has_mqtt_h else "missing",
            check_type="exact_match",
        )
    )

    has_init = scoped_contains(generated_code, 'mqtt_client_init', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mqtt_client_init",
            passed=has_init,
            expected="mqtt_client_init() called",
            actual="present" if has_init else "missing",
            check_type="exact_match",
        )
    )

    has_connect = scoped_contains(generated_code, 'mqtt_connect', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mqtt_connect_called",
            passed=has_connect,
            expected="mqtt_connect() called",
            actual="present" if has_connect else "missing",
            check_type="exact_match",
        )
    )

    has_publish = scoped_contains(generated_code, 'mqtt_publish', scope='code_only')
    details.append(
        CheckDetail(
            check_name="mqtt_publish_called",
            passed=has_publish,
            expected="mqtt_publish() called",
            actual="present" if has_publish else "missing",
            check_type="exact_match",
        )
    )

    has_evt_handler = scoped_contains(generated_code, 'mqtt_evt', scope='code_only') or scoped_contains(generated_code, 'evt_cb', scope='code_only')
    details.append(
        CheckDetail(
            check_name="event_handler_defined",
            passed=has_evt_handler,
            expected="MQTT event handler defined",
            actual="present" if has_evt_handler else "missing",
            check_type="exact_match",
        )
    )

    return details
