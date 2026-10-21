"""Static analysis checks for OTA image hash verification."""

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate OTA hash verification code structure."""
    details: list[CheckDetail] = []

    has_psa_crypto = scoped_contains(generated_code, 'psa/crypto.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_crypto_header",
            passed=has_psa_crypto,
            expected="psa/crypto.h included",
            actual="present" if has_psa_crypto else "missing",
            check_type="exact_match",
        )
    )

    has_dfu_target = scoped_contains(generated_code, 'dfu/dfu_target.h', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dfu_target_header",
            passed=has_dfu_target,
            expected="zephyr/dfu/dfu_target.h included",
            actual="present" if has_dfu_target else "missing",
            check_type="exact_match",
        )
    )

    has_psa_hash = scoped_contains(generated_code, 'psa_hash_compute', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_hash_compute_used",
            passed=has_psa_hash,
            expected="psa_hash_compute() used for SHA-256 (not custom algorithm)",
            actual="present" if has_psa_hash else "missing (custom SHA-256 or wrong API)",
            check_type="exact_match",
        )
    )

    has_sha256_alg = scoped_contains(generated_code, 'PSA_ALG_SHA_256', scope='code_only')
    details.append(
        CheckDetail(
            check_name="sha256_algorithm_constant",
            passed=has_sha256_alg,
            expected="PSA_ALG_SHA_256 used as algorithm identifier",
            actual="present" if has_sha256_alg else "missing",
            check_type="exact_match",
        )
    )

    has_memcmp = scoped_contains(generated_code, 'memcmp', scope='code_only')
    details.append(
        CheckDetail(
            check_name="hash_comparison_memcmp",
            passed=has_memcmp,
            expected="memcmp used to compare computed and expected hash",
            actual="present" if has_memcmp else "missing",
            check_type="exact_match",
        )
    )

    has_dfu_write = scoped_contains(generated_code, 'dfu_target_write', scope='code_only')
    details.append(
        CheckDetail(
            check_name="dfu_target_write_present",
            passed=has_dfu_write,
            expected="dfu_target_write() called to write flash after hash passes",
            actual="present" if has_dfu_write else "missing",
            check_type="exact_match",
        )
    )

    has_expected_hash = scoped_contains(generated_code, 'expected_hash', scope='code_only')
    details.append(
        CheckDetail(
            check_name="expected_hash_defined",
            passed=has_expected_hash,
            expected="expected_hash array defined for comparison",
            actual="present" if has_expected_hash else "missing",
            check_type="exact_match",
        )
    )

    return details
