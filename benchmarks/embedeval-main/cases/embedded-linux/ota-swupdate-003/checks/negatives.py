"""Negative tests for ota-swupdate-003 (signed update)."""

import re


def _swap_sha256_to_sha1(code: str) -> str:
    return code.replace("sha256 =", "sha1 =")


def _swap_sha256_to_md5(code: str) -> str:
    return code.replace("sha256 =", "md5 =")


def _shorten_sha256_to_md5_length(code: str) -> str:
    """Replace each 64-hex value with a 32-hex value. Still assigned
    to the sha256 key, but the length is wrong."""
    return re.sub(
        r'sha256\s*=\s*"[0-9a-f]{64}"',
        'sha256 = "deadbeefdeadbeefdeadbeefdeadbeef"',
        code,
    )


def _uppercase_sha256_values(code: str) -> str:
    def up(m: re.Match) -> str:
        return f'sha256 = "{m.group(1).upper()}"'

    return re.sub(r'sha256\s*=\s*"([0-9a-f]{64})"', up, code)


def _drop_sha256_on_one_image(code: str) -> str:
    """Drop the sha256 line from the FIRST image entry."""
    return re.sub(r'^\s*sha256\s*=.*\n', "", code, count=1, flags=re.MULTILINE)


def _drop_encrypted_on_one_image(code: str) -> str:
    return re.sub(
        r'^\s*encrypted\s*=.*\n', "", code, count=1, flags=re.MULTILINE
    )


def _encrypted_as_string(code: str) -> str:
    return code.replace("encrypted = true", 'encrypted = "true"')


def _drop_build_field(code: str) -> str:
    return re.sub(
        r'^\s*build\s*=.*\n', "", code, count=1, flags=re.MULTILINE
    )


def _add_plaintext_password(code: str) -> str:
    """Leak a plaintext password into the descriptor."""
    return code.replace(
        'description = "',
        'password = "hunter2";\n    description = "',
        1,
    )


def _add_private_key_field(code: str) -> str:
    return code.replace(
        'description = "',
        'pkey = "-----BEGIN RSA PRIVATE KEY-----\\nAAAA\\n";\n    description = "',
        1,
    )


def _add_aes_key_field(code: str) -> str:
    return code.replace(
        'description = "',
        'aes-key = "00112233445566778899aabbccddeeff";\n    description = "',
        1,
    )


def _drop_hw_compat(code: str) -> str:
    return re.sub(
        r'^\s*hardware-compatibility\s*=.*\n',
        "",
        code,
        count=1,
        flags=re.MULTILINE,
    )


def _only_one_image(code: str) -> str:
    """Remove the second image entry (rootfs)."""
    return re.sub(
        r",\s*\{[^{}]*?rootfs\.ext4[^{}]*?\}",
        "",
        code,
        flags=re.DOTALL,
    )


NEGATIVES = [
    {
        "name": "swap_sha256_to_sha1",
        "description": "Swap integrity algorithm to SHA-1. Broken for firmware verification since the 2017 SHAttered collision work.",
        "mutation": _swap_sha256_to_sha1,
        "must_fail": [
            "all_images_have_sha256",
            "no_sha1_digest",
            "sha256_keyword_present",
        ],
        "factor_id": "E7.1",
    },
    {
        "name": "swap_sha256_to_md5",
        "description": "Swap integrity algorithm to MD5. Cryptographically broken since 2004.",
        "mutation": _swap_sha256_to_md5,
        "must_fail": [
            "all_images_have_sha256",
            "no_md5_digest",
            "sha256_keyword_present",
        ],
        "factor_id": "E7.1",
    },
    {
        "name": "shorten_sha256_to_md5_length",
        "description": "Keep sha256 key but assign 32-hex (md5-length) values. Passes naive keyword checks but fails any length-aware hash validator.",
        "mutation": _shorten_sha256_to_md5_length,
        "must_fail": [
            "sha256_values_64_lowercase_hex",
            "no_md5_length_sha256_values",
        ],
        "factor_id": "E7.1",
    },
    {
        "name": "uppercase_sha256_values",
        "description": "Uppercase hex values in sha256. Strict validators (and OpenSSL sha256sum output) expect lowercase.",
        "mutation": _uppercase_sha256_values,
        "must_fail": ["sha256_values_64_lowercase_hex"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_sha256_on_one_image",
        "description": "Remove sha256 from one image entry — installer writes unverified bytes on that partition.",
        "mutation": _drop_sha256_on_one_image,
        "must_fail": ["all_images_have_sha256"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_encrypted_on_one_image",
        "description": "Remove encrypted flag from one image — installer may write ciphertext to disk or decryption may be skipped silently.",
        "mutation": _drop_encrypted_on_one_image,
        "must_fail": ["encrypted_flag_per_image"],
        "factor_id": "F6.2",
    },
    {
        "name": "encrypted_as_string",
        "description": "Swap ``encrypted = true`` bool for string ``\"true\"``. libconfig type-mismatches; SWUpdate rejects the descriptor or accepts it and skips decryption.",
        "mutation": _encrypted_as_string,
        "must_fail": ["encrypted_is_boolean_not_string"],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_build_field",
        "description": "Remove build identifier. Post-incident forensics cannot map the bundle back to a CI run.",
        "mutation": _drop_build_field,
        "must_fail": ["build_field_present", "build_keyword_present"],
        "factor_id": "F6.2",
    },
    {
        "name": "plaintext_password_in_descriptor",
        "description": "Leak a plaintext password into the descriptor. Descriptor is unencrypted before signature verification; bundles sit on build servers and CI logs.",
        "mutation": _add_plaintext_password,
        "must_fail": ["no_plaintext_secret_in_descriptor"],
        "factor_id": "E7.1",
    },
    {
        "name": "private_key_in_descriptor",
        "description": "Embed an RSA private key in the descriptor. Keys must stay on the device; anyone with the .swu gets to forge updates.",
        "mutation": _add_private_key_field,
        "must_fail": ["no_plaintext_secret_in_descriptor"],
        "factor_id": "E7.1",
    },
    {
        "name": "aes_key_in_descriptor",
        "description": "Embed an AES key in the descriptor. Same problem class — key travels with the ciphertext.",
        "mutation": _add_aes_key_field,
        "must_fail": ["no_plaintext_secret_in_descriptor"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_hw_compatibility",
        "description": "Remove hardware-compatibility. Installer applies signed update on incompatible silicon revisions.",
        "mutation": _drop_hw_compat,
        "must_fail": [
            "hardware_compatibility_present",
            "hardware_compatibility_keyword_present",
        ],
        "factor_id": "E6.1",
    },
    {
        "name": "only_one_image",
        "description": "Drop rootfs image entry; only bootloader remains. Update is semantically broken (new kernel with old rootfs).",
        "mutation": _only_one_image,
        "must_fail": ["at_least_two_images"],
        "factor_id": "F6.2",
    },
]
