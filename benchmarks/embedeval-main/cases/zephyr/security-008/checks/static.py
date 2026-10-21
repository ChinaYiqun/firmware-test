"""Static analysis checks for HMAC-SHA256 Message Authentication."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate HMAC-SHA256 PSA MAC code structure."""
    details: list[CheckDetail] = []

    # Check 1: psa/crypto.h included
    has_psa_h = scoped_contains(generated_code, 'psa/crypto.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_crypto_header",
            passed=has_psa_h,
            expected="psa/crypto.h included",
            actual="present" if has_psa_h else "missing",
            check_type="exact_match",
        )
    )

    # Check 2: psa_crypto_init called
    has_init = scoped_contains(generated_code, 'psa_crypto_init', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_crypto_init_called",
            passed=has_init,
            expected="psa_crypto_init() called before MAC operations",
            actual="present" if has_init else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: psa_mac_sign_setup called (NOT psa_hash_setup — LLM failure)
    has_mac_setup = scoped_contains(generated_code, 'psa_mac_sign_setup', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_mac_sign_setup_called",
            passed=has_mac_setup,
            expected="psa_mac_sign_setup() called (not psa_hash_setup)",
            actual="present" if has_mac_setup else "missing (LLM may have used psa_hash_setup)",
            check_type="exact_match",
        )
    )

    # Check 4: psa_mac_update called
    has_mac_update = scoped_contains(generated_code, 'psa_mac_update', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_mac_update_called",
            passed=has_mac_update,
            expected="psa_mac_update() called",
            actual="present" if has_mac_update else "missing",
            check_type="exact_match",
        )
    )

    # Check 5: psa_mac_sign_finish called
    has_mac_finish = scoped_contains(generated_code, 'psa_mac_sign_finish', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_mac_sign_finish_called",
            passed=has_mac_finish,
            expected="psa_mac_sign_finish() called",
            actual="present" if has_mac_finish else "missing",
            check_type="exact_match",
        )
    )

    # Check 6: Correct algorithm PSA_ALG_HMAC(PSA_ALG_SHA_256)
    has_hmac_sha256 = (
        scoped_contains(generated_code, 'PSA_ALG_HMAC', scope='code_only') and scoped_contains(generated_code, 'PSA_ALG_SHA_256', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="hmac_sha256_algorithm",
            passed=has_hmac_sha256,
            expected="PSA_ALG_HMAC(PSA_ALG_SHA_256) used as algorithm",
            actual="present" if has_hmac_sha256 else "missing (wrong algorithm)",
            check_type="exact_match",
        )
    )

    # Check 7: Not using psa_hash_* instead of psa_mac_* (LLM failure pattern)
    uses_hash_instead = (
        scoped_contains(generated_code, 'psa_hash_setup', scope='code_only')
        or scoped_contains(generated_code, 'psa_hash_update', scope='code_only')
        or scoped_contains(generated_code, 'psa_hash_finish', scope='code_only')
    )
    details.append(
        CheckDetail(
            check_name="no_hash_api_for_hmac",
            passed=not uses_hash_instead,
            expected="psa_mac_* API used (not psa_hash_* which computes plain hash, not HMAC)",
            actual="hash API misused for HMAC!" if uses_hash_instead else "correct MAC API used",
            check_type="constraint",
        )
    )

    return details
