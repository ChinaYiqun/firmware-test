"""Negative tests for ota-swupdate-001 (SWUpdate minimal triple).

Each mutation targets a specific grammar failure the reference must
surface via a named check. Covers libconfig-vs-YAML/JSON drift, missing
image fields, missing hardware-compatibility list, and duplicate device
paths.
"""

import re


def _yamlify_top_level(code: str) -> str:
    """Replace libconfig top-level with YAML-style ``software:`` header."""
    # Drop the libconfig ``software = { ... };`` framing and leave a
    # top-level ``software:`` marker instead. The rest of the content
    # is still invalid YAML, but the discriminator is the header form.
    return "---\nsoftware:\n" + code


def _jsonify_top_level(code: str) -> str:
    return '{"software": ' + code + "}"


def _drop_version(code: str) -> str:
    return re.sub(r'^\s*version\s*=.*\n', "", code, count=1, flags=re.MULTILINE)


def _drop_hw_compat(code: str) -> str:
    # Removes the whole ``hardware-compatibility = [ ... ];`` line
    # (array is single-line in the reference).
    return re.sub(
        r'^\s*hardware-compatibility\s*=.*$\n',
        "",
        code,
        count=1,
        flags=re.MULTILINE,
    )


def _drop_sha256_on_second_image(code: str) -> str:
    # Remove the sha256 line from the SECOND image entry only. Split on
    # image-entry opening braces so we can surgically edit one entry.
    lines = code.splitlines(keepends=True)
    sha_count = 0
    out: list[str] = []
    for line in lines:
        if re.match(r"\s*sha256\s*=", line):
            sha_count += 1
            if sha_count == 2:
                continue  # drop
        out.append(line)
    return "".join(out)


def _drop_device_on_first_image(code: str) -> str:
    lines = code.splitlines(keepends=True)
    dev_count = 0
    out: list[str] = []
    for line in lines:
        if re.match(r"\s*device\s*=", line):
            dev_count += 1
            if dev_count == 1:
                continue
        out.append(line)
    return "".join(out)


def _drop_filename_on_third_image(code: str) -> str:
    lines = code.splitlines(keepends=True)
    fn_count = 0
    out: list[str] = []
    for line in lines:
        if re.match(r"\s*filename\s*=", line):
            fn_count += 1
            if fn_count == 3:
                continue
        out.append(line)
    return "".join(out)


def _same_device_all_three(code: str) -> str:
    """Collapse three distinct device paths to the same one."""
    return re.sub(
        r'device\s*=\s*"[^"]+"',
        'device = "/dev/mmcblk0p1"',
        code,
    )


def _drop_images_list(code: str) -> str:
    """Remove the ``images: ( ... );`` block entirely."""
    return re.sub(
        r"images:\s*\([\s\S]*?\)\s*;",
        "",
        code,
    )


def _only_two_images(code: str) -> str:
    """Drop the third image entry."""
    # Match the last ``{ ... },?`` inside images: (...). Works because
    # our reference has exactly three entries.
    return re.sub(
        r",\s*\{[^{}]*?rootfs\.ext4[^{}]*?\}\s*(?=\);)",
        "",
        code,
        flags=re.DOTALL,
    )


def _sha256_wrong_length(code: str) -> str:
    """Replace sha256 values with md5-length (32 hex chars). Helper
    tolerates the value but a stricter per-entry check could flag it;
    the oracle expects ``sha256`` presence-keyword to still pass while
    the semantic sha256_64_hex check (not currently in TC 001) would
    fail. Here it's a soft negative — used to demonstrate that length
    isn't enforced; tagged with a check the mutation actually breaks."""
    return re.sub(
        r'sha256\s*=\s*"[0-9a-f]{64}"',
        'sha256 = "deadbeefdeadbeefdeadbeefdeadbeef"',
        code,
    )


def _images_as_dict_not_list(code: str) -> str:
    """``images = { ... };`` dict form instead of ``images: ( ... );``
    list form — reads as a block, images entries no longer parse."""
    return re.sub(
        r"images:\s*\(",
        "images = {",
        code,
        count=1,
    ).replace(");", "};", 1)


def _rename_sha256_to_hash(code: str) -> str:
    """Swap ``sha256`` to ``hash`` — accidental foreign-grammar drift
    (from FIT image .its idiom)."""
    return code.replace("sha256 =", "hash =")


def _drop_software_block_framing(code: str) -> str:
    """Remove ``software = {`` top-level block while keeping the inner
    content. This is the classic ``just a list of images with no
    software wrapper`` drift."""
    # Drop opening ``software = {`` and matching trailing ``};``.
    code = re.sub(r"^\s*software\s*=\s*\{\s*\n", "", code, count=1, flags=re.MULTILINE)
    # Drop the last ``};`` which closes software.
    return re.sub(r"};\s*$", "", code, count=1)


NEGATIVES = [
    {
        "name": "yamlify_top_level",
        "description": "Swap libconfig to YAML top-level form (``---\\nsoftware:\\n``). Classic cross-grammar drift — LLM may default to YAML since SWUpdate nominally supports it but the kirkstone default parser is libconfig.",
        "mutation": _yamlify_top_level,
        "must_fail": ["no_yaml_syntax"],
        "factor_id": "F6.1",
    },
    {
        "name": "jsonify_top_level",
        "description": "Wrap content in ``{\"software\": ... }`` JSON. Same class as YAML drift.",
        "mutation": _jsonify_top_level,
        "must_fail": ["no_json_syntax"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_version",
        "description": "Remove ``version = ...`` from software block. Updates without version are indistinguishable for bookkeeping.",
        "mutation": _drop_version,
        "must_fail": ["version_field_present"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_hw_compatibility",
        "description": "Remove hardware-compatibility list. SWUpdate will apply the update on any hardware revision, including incompatible ones.",
        "mutation": _drop_hw_compat,
        "must_fail": [
            "hardware_compatibility_list_nonempty",
            "hardware_compatibility_keyword_present",
        ],
        "factor_id": "E6.1",
    },
    {
        "name": "drop_sha256_on_second_image",
        "description": "Remove sha256 from one image entry. Installer writes unverified bytes — classic supply-chain-attack vector.",
        "mutation": _drop_sha256_on_second_image,
        "must_fail": ["each_image_has_sha256"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_device_on_first_image",
        "description": "Remove device= from first image entry. SWUpdate cannot determine the target partition.",
        "mutation": _drop_device_on_first_image,
        "must_fail": ["each_image_has_device"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_filename_on_third_image",
        "description": "Remove filename= from third image entry. Installer cannot locate the bundled image bytes.",
        "mutation": _drop_filename_on_third_image,
        "must_fail": ["each_image_has_filename"],
        "factor_id": "F6.2",
    },
    {
        "name": "same_device_all_three",
        "description": "All three images point to the same device. Installer races itself writing to /dev/mmcblk0p1 three times; final state is indeterminate.",
        "mutation": _same_device_all_three,
        "must_fail": ["distinct_device_paths"],
        "factor_id": "E4.1",
    },
    {
        "name": "drop_images_list",
        "description": "Remove the entire images list. Nothing will be installed.",
        "mutation": _drop_images_list,
        "must_fail": [
            "images_list_present",
            "three_images_declared",
            "each_image_has_sha256",
        ],
        "factor_id": "F6.1",
    },
    {
        "name": "only_two_images",
        "description": "Keep only two image entries. Count mismatches the prompt requirement.",
        "mutation": _only_two_images,
        "must_fail": ["three_images_declared"],
        "factor_id": "F6.2",
    },
    {
        "name": "images_as_dict_not_list",
        "description": "Swap images: ( ... ); list form to images = { ... }; dict form. Entries no longer parse as a list; SWUpdate rejects the descriptor.",
        "mutation": _images_as_dict_not_list,
        "must_fail": ["images_list_present", "three_images_declared"],
        "factor_id": "F1.1",
    },
    {
        "name": "rename_sha256_to_hash",
        "description": "Swap sha256 key to ``hash`` (foreign grammar from FIT image .its). SWUpdate reads no integrity hash and accepts arbitrary bytes.",
        "mutation": _rename_sha256_to_hash,
        "must_fail": ["each_image_has_sha256", "sha256_keyword_present"],
        "factor_id": "F2.1",
    },
    {
        "name": "drop_software_block_framing",
        "description": "Remove the software = { ... }; outer block, leaving images at top level. SWUpdate expects a software block to bind hardware-compatibility + selection groups.",
        "mutation": _drop_software_block_framing,
        "must_fail": ["software_block_top_level", "software_keyword_present"],
        "factor_id": "F6.1",
    },
]
