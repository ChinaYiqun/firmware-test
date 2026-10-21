"""Behavioral checks for MQTT with Last Will and Testament."""

from embedeval.models import CheckDetail
from embedeval.check_utils import check_no_cross_platform_apis, strip_comments
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate MQTT LWT ordering and completeness."""
    details: list[CheckDetail] = []

    # Check 1: LWT configured BEFORE mqtt_connect (critical ordering)
    # Use comment-stripped code to avoid matching "mqtt_connect" in comments
    stripped = strip_comments(generated_code)
    will_topic_pos = stripped.find("will_topic")
    connect_pos = stripped.find("mqtt_connect")
    will_before_connect = (
        will_topic_pos != -1
        and connect_pos != -1
        and will_topic_pos < connect_pos
    )
    details.append(
        CheckDetail(
            check_name="will_configured_before_connect",
            passed=will_before_connect,
            expected="will_topic configured before mqtt_connect()",
            actual="correct" if will_before_connect else "wrong order — LWT must be set before connecting",
            check_type="constraint",
        )
    )

    # Check 2: Will topic is not empty (non-trivial string)
    has_nonempty_will_topic = (
        scoped_contains(generated_code, '"devices/', scope='code_only')
        or scoped_contains(generated_code, '"status"', scope='code_only')
        or scoped_contains(generated_code, 'WILL_TOPIC', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="will_topic_not_empty",
            passed=has_nonempty_will_topic,
            expected="Will topic is a non-empty string",
            actual="present" if has_nonempty_will_topic else "missing or empty will topic",
            check_type="constraint",
        )
    )

    # Check 3: MQTT_EVT_CONNACK handled in event callback
    has_connack = scoped_contains(generated_code, 'MQTT_EVT_CONNACK', scope='code_only')
    details.append(
        CheckDetail(
            check_name="connack_handled",
            passed=has_connack,
            expected="MQTT_EVT_CONNACK event handled",
            actual="present" if has_connack else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: MQTT_EVT_DISCONNECT handled
    has_disconnect = scoped_contains(generated_code, 'MQTT_EVT_DISCONNECT', scope='code_only')
    details.append(
        CheckDetail(
            check_name="disconnect_handled",
            passed=has_disconnect,
            expected="MQTT_EVT_DISCONNECT event handled",
            actual="present" if has_disconnect else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: mqtt_input and mqtt_live in main loop
    has_input = scoped_contains(generated_code, 'mqtt_input', scope='code_only')
    has_live = scoped_contains(generated_code, 'mqtt_live', scope='code_only')
    details.append(
        CheckDetail(
            check_name="protocol_loop",
            passed=has_input and has_live,
            expected="mqtt_input() and mqtt_live() called in main loop",
            actual=f"input={has_input}, live={has_live}",
            check_type="constraint",
        )
    )

    # Check 6: Error handling on mqtt_connect
    has_conn_err = scoped_contains(generated_code, '< 0', scope='code_only')
    details.append(
        CheckDetail(
            check_name="connect_error_handling",
            passed=has_conn_err,
            expected="Error check on mqtt_connect return value",
            actual="present" if has_conn_err else "missing — connect errors ignored",
            check_type="constraint",
        )
    )

    # Check: No cross-platform API contamination
    cross_plat = check_no_cross_platform_apis(generated_code, skip_platforms=["Linux_Userspace"])
    details.append(CheckDetail(
        check_name="no_cross_platform_apis",
        passed=len(cross_plat) == 0,
        expected="No FreeRTOS/Arduino/STM32_HAL/POSIX APIs",
        actual="clean" if not cross_plat else f"found: {[a for a, _ in cross_plat]}",
        check_type="constraint",
    ))

    return details
