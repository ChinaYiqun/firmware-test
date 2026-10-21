"""Static analysis checks for CoAP client GET request."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate CoAP client code structure."""
    details: list[CheckDetail] = []

    has_coap_h = scoped_contains(generated_code, 'zephyr/net/coap.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="coap_header",
            passed=has_coap_h,
            expected="zephyr/net/coap.h included",
            actual="present" if has_coap_h else "missing",
            check_type="exact_match",
        )
    )

    has_socket_h = scoped_contains(generated_code, 'zephyr/net/socket.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="socket_header",
            passed=has_socket_h,
            expected="zephyr/net/socket.h included",
            actual="present" if has_socket_h else "missing",
            check_type="exact_match",
        )
    )

    has_packet_init = scoped_contains(generated_code, 'coap_packet_init', scope='code_only')
    details.append(
        CheckDetail(
            check_name="coap_packet_init_called",
            passed=has_packet_init,
            expected="coap_packet_init() called",
            actual="present" if has_packet_init else "missing",
            check_type="exact_match",
        )
    )

    has_append_option = scoped_contains(generated_code, 'coap_packet_append_option', scope='code_only')
    details.append(
        CheckDetail(
            check_name="coap_append_option_called",
            passed=has_append_option,
            expected="coap_packet_append_option() called",
            actual="present" if has_append_option else "missing",
            check_type="exact_match",
        )
    )

    has_uri_path = scoped_contains(generated_code, 'COAP_OPTION_URI_PATH', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uri_path_option",
            passed=has_uri_path,
            expected="COAP_OPTION_URI_PATH used",
            actual="present" if has_uri_path else "missing",
            check_type="exact_match",
        )
    )

    has_get_method = scoped_contains(generated_code, 'COAP_METHOD_GET', scope='code_only')
    details.append(
        CheckDetail(
            check_name="coap_get_method",
            passed=has_get_method,
            expected="COAP_METHOD_GET used",
            actual="present" if has_get_method else "missing",
            check_type="exact_match",
        )
    )

    has_parse = scoped_contains(generated_code, 'coap_packet_parse', scope='code_only')
    details.append(
        CheckDetail(
            check_name="coap_packet_parse_called",
            passed=has_parse,
            expected="coap_packet_parse() called to parse response",
            actual="present" if has_parse else "missing",
            check_type="exact_match",
        )
    )

    has_get_code = scoped_contains(generated_code, 'coap_header_get_code', scope='code_only')
    details.append(
        CheckDetail(
            check_name="coap_header_get_code_called",
            passed=has_get_code,
            expected="coap_header_get_code() called to read response code",
            actual="present" if has_get_code else "missing",
            check_type="exact_match",
        )
    )

    return details
