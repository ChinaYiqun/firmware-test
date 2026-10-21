"""Static analysis checks for HTTP client with TLS."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate HTTPS client code structure."""
    details: list[CheckDetail] = []

    has_http_h = scoped_contains(generated_code, 'zephyr/net/http/client.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="http_client_header",
            passed=has_http_h,
            expected="zephyr/net/http/client.h included",
            actual="present" if has_http_h else "missing",
            check_type="exact_match",
        )
    )

    has_tls_cred_h = scoped_contains(generated_code, 'zephyr/net/tls_credentials.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="tls_credentials_header",
            passed=has_tls_cred_h,
            expected="zephyr/net/tls_credentials.h included",
            actual="present" if has_tls_cred_h else "missing",
            check_type="exact_match",
        )
    )

    has_tls_cred_add = scoped_contains(generated_code, 'tls_credential_add', scope='code_only')
    details.append(
        CheckDetail(
            check_name="tls_credential_add_called",
            passed=has_tls_cred_add,
            expected="tls_credential_add() called to register CA cert",
            actual="present" if has_tls_cred_add else "missing",
            check_type="exact_match",
        )
    )

    has_tls_socket = scoped_contains(generated_code, 'IPPROTO_TLS_1_2', scope='code_only') or scoped_contains(generated_code, 'IPPROTO_TLS_1_3', scope='code_only')
    details.append(
        CheckDetail(
            check_name="tls_socket_protocol",
            passed=has_tls_socket,
            expected="IPPROTO_TLS_1_2 or IPPROTO_TLS_1_3 used for TLS socket",
            actual="present" if has_tls_socket else "missing — plain TCP socket used",
            check_type="exact_match",
        )
    )

    has_sec_tag_list = scoped_contains(generated_code, 'TLS_SEC_TAG_LIST', scope='code_only')
    details.append(
        CheckDetail(
            check_name="tls_sec_tag_list_set",
            passed=has_sec_tag_list,
            expected="TLS_SEC_TAG_LIST socket option set",
            actual="present" if has_sec_tag_list else "missing",
            check_type="exact_match",
        )
    )

    has_hostname = scoped_contains(generated_code, 'TLS_HOSTNAME', scope='code_only')
    details.append(
        CheckDetail(
            check_name="tls_hostname_set",
            passed=has_hostname,
            expected="TLS_HOSTNAME socket option set for SNI",
            actual="present" if has_hostname else "missing",
            check_type="exact_match",
        )
    )

    has_http_req = scoped_contains(generated_code, 'http_client_req', scope='code_only')
    details.append(
        CheckDetail(
            check_name="http_client_req_called",
            passed=has_http_req,
            expected="http_client_req() called",
            actual="present" if has_http_req else "missing",
            check_type="exact_match",
        )
    )

    has_ca_cert = scoped_contains(generated_code, 'TLS_CREDENTIAL_CA_CERTIFICATE', scope='code_only')
    details.append(
        CheckDetail(
            check_name="ca_certificate_type",
            passed=has_ca_cert,
            expected="TLS_CREDENTIAL_CA_CERTIFICATE type used",
            actual="present" if has_ca_cert else "missing",
            check_type="exact_match",
        )
    )

    return details
