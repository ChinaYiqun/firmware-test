"""Static analysis checks for PSA Crypto random number generation."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate PSA Crypto RNG code structure."""
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

    # Check 2: psa_crypto_init called (LLM failure: omitted)
    has_init = scoped_contains(generated_code, 'psa_crypto_init', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_crypto_init_called",
            passed=has_init,
            expected="psa_crypto_init() called",
            actual="present" if has_init else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: psa_generate_random used (not rand()/srand())
    has_psa_rng = scoped_contains(generated_code, 'psa_generate_random', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_generate_random_used",
            passed=has_psa_rng,
            expected="psa_generate_random() used",
            actual="present" if has_psa_rng else "missing",
            check_type="exact_match",
        )
    )

    # Check 4: No forbidden rand()/srand() usage (LLM failure: uses C stdlib)
    has_stdlib_rand = scoped_contains(generated_code, 'rand()', scope='code_only') or scoped_contains(generated_code, 'srand(', scope='code_only')
    details.append(
        CheckDetail(
            check_name="no_stdlib_rand",
            passed=not has_stdlib_rand,
            expected="No rand()/srand() (must use PSA API)",
            actual="bad rand found" if has_stdlib_rand else "clean",
            check_type="constraint",
        )
    )

    # Check 5: PSA_SUCCESS checked
    has_psa_success = scoped_contains(generated_code, 'PSA_SUCCESS', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_success_checked",
            passed=has_psa_success,
            expected="PSA_SUCCESS used for return value checks",
            actual="present" if has_psa_success else "missing",
            check_type="exact_match",
        )
    )

    return details
