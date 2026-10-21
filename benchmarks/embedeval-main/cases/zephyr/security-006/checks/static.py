"""Static analysis checks for Secure Key Storage with Anti-Tamper."""

import re

from embedeval.models import CheckDetail
from embedeval.check_utils import scoped_contains


def run_checks(generated_code: str) -> list[CheckDetail]:
    """Validate non-extractable key storage code structure."""
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
            expected="psa_crypto_init() called",
            actual="present" if has_init else "missing",
            check_type="exact_match",
        )
    )

    # Check 3: PSA_KEY_USAGE_EXPORT must NOT be set (LLM failure: always adds it)
    # Strip comments first to avoid matching mentions in comment text
    code_no_comments = re.sub(r"/\*.*?\*/", "", generated_code, flags=re.DOTALL)
    code_no_comments = re.sub(r"//[^\n]*", "", code_no_comments)
    has_export_flag = "PSA_KEY_USAGE_EXPORT" in code_no_comments
    details.append(
        CheckDetail(
            check_name="no_export_usage_flag",
            passed=not has_export_flag,
            expected="PSA_KEY_USAGE_EXPORT must NOT be set (non-extractable key)",
            actual="EXPORT flag present (security violation!)"
            if has_export_flag
            else "EXPORT flag absent (correct)",
            check_type="constraint",
        )
    )

    # Check 4: psa_import_key called
    has_import = scoped_contains(generated_code, 'psa_import_key', scope='code_only')
    details.append(
        CheckDetail(
            check_name="psa_import_key_called",
            passed=has_import,
            expected="psa_import_key() called",
            actual="present" if has_import else "missing",
            check_type="exact_match",
        )
    )

    # Check 7: PSA_SUCCESS checked
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
