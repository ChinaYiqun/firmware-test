"""Static analysis checks for DNS resolution with timeout."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate DNS resolution code structure."""
    details: list[CheckDetail] = []

    has_dns_h = scoped_contains(generated_code, 'zephyr/net/dns_resolve.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dns_resolve_header",
            passed=has_dns_h,
            expected="zephyr/net/dns_resolve.h included",
            actual="present" if has_dns_h else "missing",
            check_type="exact_match",
        )
    )

    has_dns_resolve_name = scoped_contains(generated_code, 'dns_resolve_name', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dns_resolve_name_called",
            passed=has_dns_resolve_name,
            expected="dns_resolve_name() called",
            actual="present" if has_dns_resolve_name else "missing",
            check_type="exact_match",
        )
    )

    # Hallucination check: gethostbyname is POSIX, not Zephyr
    uses_gethostbyname = scoped_contains(generated_code, 'gethostbyname', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_gethostbyname",
            passed=not uses_gethostbyname,
            expected="gethostbyname() NOT used (POSIX API, not available in Zephyr)",
            actual="clean" if not uses_gethostbyname else "HALLUCINATION: gethostbyname() is not Zephyr API",
            check_type="exact_match",
        )
    )

    # Hallucination check: dns_lookup does not exist in Zephyr
    uses_dns_lookup = scoped_contains(generated_code, 'dns_lookup', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_dns_lookup",
            passed=not uses_dns_lookup,
            expected="dns_lookup() NOT used (does not exist in Zephyr)",
            actual="clean" if not uses_dns_lookup else "HALLUCINATION: dns_lookup() does not exist",
            check_type="exact_match",
        )
    )

    has_callback = scoped_contains(generated_code, 'dns_result_cb', scope='code_only') or scoped_contains(generated_code, 'dns_cb', scope='code_only') or scoped_contains(generated_code, 'dns_resolve_status', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dns_callback_registered",
            passed=has_callback,
            expected="DNS result callback function defined",
            actual="present" if has_callback else "missing",
            check_type="exact_match",
        )
    )

    has_default_ctx = scoped_contains(generated_code, 'dns_get_default_context', scope='code_only')
    details.append(
        CheckDetail(
            check_name="uses_default_context",
            passed=has_default_ctx,
            expected="dns_get_default_context() used to obtain DNS context",
            actual="present" if has_default_ctx else "missing",
            check_type="exact_match",
        )
    )

    return details
