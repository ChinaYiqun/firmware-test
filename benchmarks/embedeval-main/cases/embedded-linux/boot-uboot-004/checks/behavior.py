"""Behavioral checks for boot-uboot-004 (signed FIT)."""

import re

from embedeval.check_utils import strip_comments
from embedeval.models import CheckDetail


def _extract_brace_block(text: str, anchor: str) -> str:
    """Return the ``{ ... }`` body following ``anchor`` in ``text``
    via brace counting. Whitespace-tolerant — does not rely on a
    specific closing pattern (``\\n};`` or ``}`` inline both work)."""
    start = text.find(anchor)
    if start == -1:
        return ""
    brace = text.find("{", start)
    if brace == -1:
        return ""
    depth = 1
    i = brace + 1
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[brace + 1 : i - 1] if depth == 0 else ""


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    body = strip_comments(generated_code)

    # 1. A signature sub-node exists INSIDE the configurations block
    # (not in images — signing the configuration is what gates boot).
    # Use brace-counter extraction so single-line config blocks and
    # missing trailing semicolons don't trip the check.
    config_text = _extract_brace_block(body, "config-1")
    sig_in_config = bool(re.search(r"signature[-\w]*\s*\{", config_text))
    details.append(
        CheckDetail(
            check_name="signature_node_in_configuration",
            passed=sig_in_config,
            expected="signature sub-node inside config-1",
            actual="present" if sig_in_config else "missing — unsigned FIT would boot",
            check_type="constraint",
        )
    )

    # 2. algo = "sha256,rsa<bits>" — combined hash and RSA algo.
    algo_match = re.search(
        r'algo\s*=\s*"sha256,rsa(\d+)"', body
    )
    algo_ok = bool(algo_match) and int(algo_match.group(1)) >= 2048
    details.append(
        CheckDetail(
            check_name="signature_algo_sha256_rsa_2048_or_stronger",
            passed=algo_ok,
            expected='algo = "sha256,rsa<2048|4096>" (combined hash + RSA)',
            actual=(
                f"sha256,rsa{algo_match.group(1)}"
                if algo_match
                else "missing or weak algo"
            ),
            check_type="constraint",
        )
    )

    # 3. rsa4096 specifically (prompt requirement).
    has_rsa4096 = bool(re.search(r'algo\s*=\s*"sha256,rsa4096"', body))
    details.append(
        CheckDetail(
            check_name="signature_uses_rsa4096",
            passed=has_rsa4096,
            expected='algo = "sha256,rsa4096"',
            actual="present" if has_rsa4096 else "missing or different RSA size",
            check_type="constraint",
        )
    )

    # 4. key-name-hint set to boot-key.
    key_hint = bool(re.search(r'key-name-hint\s*=\s*"boot-key"', body))
    details.append(
        CheckDetail(
            check_name="key_name_hint_boot_key",
            passed=key_hint,
            expected='key-name-hint = "boot-key"',
            actual="present" if key_hint else "missing or wrong hint",
            check_type="constraint",
        )
    )

    # 5. sign-images declares which sub-images are covered.
    has_sign_images = bool(re.search(r'sign-images\s*=\s*"[^"]*kernel', body))
    details.append(
        CheckDetail(
            check_name="sign_images_property_set",
            passed=has_sign_images,
            expected='sign-images = "kernel"',
            actual="present" if has_sign_images else "missing — signature covers nothing",
            check_type="constraint",
        )
    )

    # 6. Kernel sub-image has hash node with sha256. Find the kernel
    # sub-image's hash block specifically.
    kernel_block = re.search(
        r'type\s*=\s*"kernel"[^{]*.*?hash[-\w]*\s*\{[^}]*algo\s*=\s*"(\w+)"',
        body,
        re.DOTALL,
    )
    kernel_sha256 = bool(kernel_block) and kernel_block.group(1) == "sha256"
    details.append(
        CheckDetail(
            check_name="kernel_hash_sha256",
            passed=kernel_sha256,
            expected='kernel sub-image has hash { algo = "sha256"; }',
            actual="present" if kernel_sha256 else "missing",
            check_type="constraint",
        )
    )

    # 7. Kernel load + entry addresses.
    kernel_region_full = re.search(
        r'type\s*=\s*"kernel"[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}', body, re.DOTALL
    )
    # simpler: find load/entry anywhere in body for reference quick-check
    has_load = bool(re.search(r"\bload\s*=\s*<0x", body))
    has_entry = bool(re.search(r"\bentry\s*=\s*<0x", body))
    details.append(
        CheckDetail(
            check_name="kernel_load_and_entry",
            passed=has_load and has_entry,
            expected="kernel sub-image has load and entry addresses",
            actual=f"load={has_load}, entry={has_entry}",
            check_type="constraint",
        )
    )

    # 8. arch = "arm64".
    kernel_arm64 = bool(
        re.search(
            r'type\s*=\s*"kernel"[^}]*arch\s*=\s*"arm64"', body, re.DOTALL
        )
    )
    details.append(
        CheckDetail(
            check_name="kernel_arch_arm64",
            passed=kernel_arm64,
            expected='arch = "arm64"',
            actual="present" if kernel_arm64 else "missing or wrong",
            check_type="constraint",
        )
    )

    # 9. No weak algos (sha1, md5) in signature or hashes.
    has_weak = bool(re.search(r'algo\s*=\s*"(md5|sha1)"', body))
    details.append(
        CheckDetail(
            check_name="no_weak_hash_algorithms",
            passed=not has_weak,
            expected="No md5 or sha1 in algo = ... entries",
            actual="clean" if not has_weak else "weak algo found",
            check_type="constraint",
        )
    )

    return details
