"""Negative tests for boot-uboot-004 (signed FIT)."""

import re


def _drop_signature_node(code: str) -> str:
    """Remove the signature-1 sub-node — FIT becomes unsigned."""
    return re.sub(
        r"\n\s*signature[-\w]*\s*\{[^}]*\};\s*",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _swap_rsa4096_to_rsa1024(code: str) -> str:
    return code.replace('"sha256,rsa4096"', '"sha256,rsa1024"')


def _swap_rsa4096_to_sha1(code: str) -> str:
    return code.replace('"sha256,rsa4096"', '"sha1"')


def _change_key_hint(code: str) -> str:
    return code.replace('"boot-key"', '"other-key"')


def _drop_key_hint(code: str) -> str:
    return re.sub(r'\n\s*key-name-hint\s*=\s*"[^"]*";', "", code, count=1)


def _drop_sign_images(code: str) -> str:
    return re.sub(r'\n\s*sign-images\s*=\s*"[^"]*";', "", code, count=1)


def _move_signature_into_images(code: str) -> str:
    """Put the signature node inside the kernel-1 sub-image block
    instead of the configuration — wrong per FIT verified-boot model."""
    # Remove signature from config
    code = re.sub(
        r"\n\s*signature[-\w]*\s*\{[^}]*\};\s*",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )
    # Insert into kernel-1 before its closing brace
    code = code.replace(
        "\t\t\thash-1 {\n\t\t\t\talgo = \"sha256\";\n\t\t\t};",
        '\t\t\thash-1 {\n\t\t\t\talgo = "sha256";\n\t\t\t};\n'
        "\t\t\tsignature-1 {\n"
        '\t\t\t\talgo = "sha256,rsa4096";\n'
        '\t\t\t\tkey-name-hint = "boot-key";\n'
        "\t\t\t};",
    )
    return code


def _drop_default_configuration(code: str) -> str:
    return code.replace('default = "config-1";\n\n\t\t', "")


def _kernel_hash_md5(code: str) -> str:
    return code.replace(
        'hash-1 {\n\t\t\t\talgo = "sha256"',
        'hash-1 {\n\t\t\t\talgo = "md5"',
    )


def _drop_kernel_hash_node(code: str) -> str:
    return re.sub(
        r"\n\s*hash[-\w]*\s*\{[^}]*\};\s*",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_load_address(code: str) -> str:
    return re.sub(r"\n\s*load\s*=\s*<[^>]*>;", "", code, count=1)


def _drop_entry_address(code: str) -> str:
    return re.sub(r"\n\s*entry\s*=\s*<[^>]*>;", "", code, count=1)


NEGATIVES = [
    {
        "name": "drop_signature_node",
        "description": "Remove the signature sub-node — FIT is unsigned; verified-boot board refuses it but there is no signature to verify against.",
        "mutation": _drop_signature_node,
        "must_fail": [
            "signature_node_in_configuration",
            "signature_uses_rsa4096",
            "key_name_hint_boot_key",
            "sign_images_property_set",
        ],
        "factor_id": "E4.1",
    },
    {
        "name": "weak_rsa_1024",
        "description": "RSA 1024 — below modern secure-boot minimum; board may still accept but it's cryptographically weak.",
        "mutation": _swap_rsa4096_to_rsa1024,
        "must_fail": ["signature_uses_rsa4096"],
        "factor_id": "E7.1",
    },
    {
        "name": "algo_sha1",
        "description": 'algo = "sha1" — weak hash, no RSA coverage; U-Boot rejects.',
        "mutation": _swap_rsa4096_to_sha1,
        "must_fail": [
            "signature_algo_sha256_rsa_2048_or_stronger",
            "signature_uses_rsa4096",
            "no_weak_hash_algorithms",
        ],
        "factor_id": "E7.1",
    },
    {
        "name": "wrong_key_name_hint",
        "description": 'key-name-hint = "other-key" — board control FDT has no such public key, verification fails.',
        "mutation": _change_key_hint,
        "must_fail": ["key_name_hint_boot_key"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_key_name_hint",
        "description": "Remove key-name-hint — U-Boot cannot locate the public key to verify.",
        "mutation": _drop_key_hint,
        "must_fail": ["key_name_hint_boot_key"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_sign_images",
        "description": "Remove sign-images — signature covers no sub-image properties.",
        "mutation": _drop_sign_images,
        "must_fail": ["sign_images_property_set"],
        "factor_id": "E4.1",
    },
    {
        "name": "signature_inside_images_node",
        "description": "Move signature sub-node under kernel-1 (inside images) — FIT-sig model requires config-level signature, not image-level.",
        "mutation": _move_signature_into_images,
        "must_fail": ["signature_node_in_configuration"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_default_config",
        "description": "Remove default = \"config-1\" — bootm has no default configuration to select.",
        "mutation": _drop_default_configuration,
        "must_fail": ["default_configuration_set"],
        "factor_id": "F6.1",
    },
    {
        "name": "kernel_hash_md5",
        "description": 'Kernel hash uses md5 — U-Boot rejects md5 on modern builds.',
        "mutation": _kernel_hash_md5,
        "must_fail": ["kernel_hash_sha256", "no_weak_hash_algorithms"],
        "factor_id": "E4.2",
    },
    {
        "name": "drop_kernel_hash_node",
        "description": "Remove the kernel hash sub-node entirely — integrity check refuses.",
        "mutation": _drop_kernel_hash_node,
        "must_fail": ["kernel_hash_sha256"],
        "factor_id": "E4.1",
    },
    {
        "name": "drop_kernel_load",
        "description": "Remove kernel load address — bootm cannot place the kernel.",
        "mutation": _drop_load_address,
        "must_fail": ["kernel_load_and_entry"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_kernel_entry",
        "description": "Remove kernel entry address — bootm cannot jump to the kernel.",
        "mutation": _drop_entry_address,
        "must_fail": ["kernel_load_and_entry"],
        "factor_id": "F6.2",
    },
]
