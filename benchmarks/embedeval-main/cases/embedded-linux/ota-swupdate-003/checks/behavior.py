"""Behavioral checks for ota-swupdate-003 (signed update).

Asserts cryptographic hygiene: sha256 is the ONLY integrity digest,
every image has one, values are 64 lowercase hex, ``encrypted = true``
is a boolean (not a string), and no plaintext secrets leak into the
descriptor.
"""

import re

from embedeval.check_utils import (
    libconfig_list_body,
    libconfig_list_entries,
    scoped_contains,
    strip_systemd_comments,
    swupdate_hardware_compatibility_list,
    swupdate_images_has_sha256,
    swupdate_libconfig_has,
)
from embedeval.models import CheckDetail

_SHA256_VALUE_RE = re.compile(r'sha256\s*=\s*"([0-9a-fA-F]+)"')
_SECRET_KEY_PATTERNS = (
    r'\bpassword\s*=',
    r'\bpkey\s*=',
    r'\bprivate[-_]key\s*=',
    r'\baes[-_]key\s*=',
    r'\baes[-_]?iv\s*=',
    r'\bsecret\s*=',
)


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []

    # 1. version field (semver).
    version = swupdate_libconfig_has(generated_code, "software", "version")
    version_ok = bool(version) and re.match(r"^\d+\.\d+", version.strip())
    details.append(
        CheckDetail(
            check_name="version_semver_format",
            passed=bool(version_ok),
            expected="version in semver form",
            actual=f"{version!r}",
            check_type="constraint",
        )
    )

    # 2. build field present (traceability).
    build = swupdate_libconfig_has(generated_code, "software", "build")
    details.append(
        CheckDetail(
            check_name="build_field_present",
            passed=bool(build),
            expected='build = "..." inside software block',
            actual=f"{build!r}" if build else "missing",
            check_type="constraint",
        )
    )

    # 3. hardware-compatibility non-empty.
    hw = swupdate_hardware_compatibility_list(generated_code)
    details.append(
        CheckDetail(
            check_name="hardware_compatibility_present",
            passed=len(hw) >= 1,
            expected="hardware-compatibility with ≥1 entry",
            actual=f"{hw}",
            check_type="constraint",
        )
    )

    # 4. Every image has sha256 key.
    details.append(
        CheckDetail(
            check_name="all_images_have_sha256",
            passed=swupdate_images_has_sha256(generated_code),
            expected="every images entry has sha256 =",
            actual="yes" if swupdate_images_has_sha256(generated_code) else "no",
            check_type="constraint",
        )
    )

    # 5. No MD5 / SHA-1 digest keys anywhere.
    stripped = strip_systemd_comments(generated_code)
    has_md5 = bool(re.search(r"\bmd5\s*=", stripped))
    has_sha1 = bool(re.search(r"\bsha1\s*=", stripped))
    details.append(
        CheckDetail(
            check_name="no_md5_digest",
            passed=not has_md5,
            expected="no md5 = ... digest key",
            actual="detected" if has_md5 else "clean",
            check_type="constraint",
        )
    )
    details.append(
        CheckDetail(
            check_name="no_sha1_digest",
            passed=not has_sha1,
            expected="no sha1 = ... digest key",
            actual="detected" if has_sha1 else "clean",
            check_type="constraint",
        )
    )

    # 6. All sha256 values are 64 lowercase hex chars.
    values = _SHA256_VALUE_RE.findall(generated_code)
    all_ok = len(values) >= 1 and all(
        len(v) == 64 and v == v.lower() and re.match(r"^[0-9a-f]+$", v)
        for v in values
    )
    details.append(
        CheckDetail(
            check_name="sha256_values_64_lowercase_hex",
            passed=all_ok,
            expected="all sha256 values 64 lowercase hex chars",
            actual=f"values={[(len(v), v[:12] + '...') for v in values]}",
            check_type="constraint",
        )
    )

    # 7. No 32-char hex strings assigned to sha256 (md5 length).
    bad_short = [v for v in values if len(v) == 32]
    details.append(
        CheckDetail(
            check_name="no_md5_length_sha256_values",
            passed=not bad_short,
            expected="no 32-char hex values assigned to sha256 (md5 length)",
            actual=f"short={bad_short}",
            check_type="constraint",
        )
    )

    # 8. Every image entry has an ``encrypted`` flag.
    images_body = libconfig_list_body(generated_code, "images")
    entries = libconfig_list_entries(images_body) if images_body else []
    encrypted_per_entry = [
        bool(re.search(r"\bencrypted\s*=", e)) for e in entries
    ]
    details.append(
        CheckDetail(
            check_name="encrypted_flag_per_image",
            passed=bool(encrypted_per_entry) and all(encrypted_per_entry),
            expected="every images entry has encrypted = ...",
            actual=f"{sum(encrypted_per_entry)}/{len(entries)} entries",
            check_type="constraint",
        )
    )

    # 9. encrypted value is a bool (true / false), not a string.
    # libconfig distinguishes ``encrypted = true`` (bool) from
    # ``encrypted = "true"`` (string) — the latter is a type error.
    string_bools = re.findall(
        r'encrypted\s*=\s*"(?:true|false)"',
        stripped,
    )
    details.append(
        CheckDetail(
            check_name="encrypted_is_boolean_not_string",
            passed=not string_bools,
            expected='encrypted = true  (bool, no quotes)',
            actual=f"string-bool occurrences={len(string_bools)}",
            check_type="constraint",
        )
    )

    # 10. No plaintext secrets in descriptor.
    hits = []
    for pat in _SECRET_KEY_PATTERNS:
        if re.search(pat, stripped):
            hits.append(pat)
    details.append(
        CheckDetail(
            check_name="no_plaintext_secret_in_descriptor",
            passed=not hits,
            expected="no password / pkey / private-key / aes-key / secret keys",
            actual=f"matched={hits}",
            check_type="constraint",
        )
    )

    # 11. At least two image entries (bootloader + rootfs minimum).
    details.append(
        CheckDetail(
            check_name="at_least_two_images",
            passed=len(entries) >= 2,
            expected="≥2 image entries",
            actual=f"{len(entries)} entries",
            check_type="constraint",
        )
    )

    # 12. description field present.
    desc = swupdate_libconfig_has(generated_code, "software", "description")
    details.append(
        CheckDetail(
            check_name="top_level_description_present",
            passed=bool(desc),
            expected='description = "..." inside software block',
            actual=f"{desc!r}" if desc else "missing",
            check_type="constraint",
        )
    )

    # 13. No YAML/JSON syntax leaks.
    yaml_head = bool(
        re.search(r"^\s*---\s*$|^\s*software\s*:\s*$", stripped, re.MULTILINE)
    )
    details.append(
        CheckDetail(
            check_name="no_yaml_syntax",
            passed=not yaml_head,
            expected="no YAML top-level header",
            actual="detected" if yaml_head else "clean",
            check_type="constraint",
        )
    )
    json_start = scoped_contains(generated_code, '{"software"', scope="raw")
    details.append(
        CheckDetail(
            check_name="no_json_syntax",
            passed=not json_start,
            expected="no JSON envelope",
            actual="detected" if json_start else "clean",
            check_type="constraint",
        )
    )

    return details
