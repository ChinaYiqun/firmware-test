"""Negative tests for ota-rauc-001 (minimal RAUC manifest)."""

import re


def _flatten_rootfs_section(code: str) -> str:
    return code.replace("[image.rootfs]", "[rootfs]")


def _pluralize_image_section(code: str) -> str:
    return code.replace("[image.rootfs]", "[images.rootfs]")


def _space_instead_of_dot(code: str) -> str:
    return code.replace("[image.rootfs]", "[image rootfs]")


def _drop_compatible(code: str) -> str:
    return re.sub(r"^\s*compatible=.*\n", "", code, count=1, flags=re.MULTILINE)


def _drop_format(code: str) -> str:
    return re.sub(r"^\s*format=.*\n", "", code, count=1, flags=re.MULTILINE)


def _invalid_format_value(code: str) -> str:
    return code.replace("format=plain", "format=invalid")


def _drop_sha256(code: str) -> str:
    return re.sub(r"^\s*sha256=.*\n", "", code, count=1, flags=re.MULTILINE)


def _drop_filename(code: str) -> str:
    return re.sub(r"^\s*filename=.*\n", "", code, count=1, flags=re.MULTILINE)


def _drop_size(code: str) -> str:
    return re.sub(r"^\s*size=.*\n", "", code, count=1, flags=re.MULTILINE)


def _yamlify(code: str) -> str:
    return "---\n" + code


def _libconfigify(code: str) -> str:
    """Emit ``update = { compatible = "..."; };`` libconfig form."""
    return """update = {
    compatible = "vendor,example-device";
    version = "1.0.0";
};
""" + code


def _compatible_no_comma(code: str) -> str:
    return code.replace("vendor,example-device", "vendor-example-device")


def _drop_update_section(code: str) -> str:
    """Drop the [update] section — works whether it's first, middle, or
    last in the file (``|\\Z`` anchors to end-of-string as a fallback)."""
    return re.sub(r"\[update\][\s\S]*?(?=\n\s*\[|\Z)", "", code, count=1)


NEGATIVES = [
    {
        "name": "flatten_rootfs_section",
        "description": "Use [rootfs] without the image. prefix. RAUC treats this as a non-image section — the rootfs image is not recognised and the slot stays empty.",
        "mutation": _flatten_rootfs_section,
        "must_fail": ["image_slot_section_present", "image_slot_uses_image_prefix"],
        "factor_id": "F6.1",
    },
    {
        "name": "pluralize_image_section",
        "description": "Use [images.rootfs] (plural). RAUC expects singular ``image.``.",
        "mutation": _pluralize_image_section,
        "must_fail": ["image_slot_section_present", "image_slot_uses_image_prefix"],
        "factor_id": "F6.1",
    },
    {
        "name": "space_instead_of_dot",
        "description": "Use [image rootfs] with a space. INI allows spaces in section names but RAUC uses dot-separated hierarchy.",
        "mutation": _space_instead_of_dot,
        "must_fail": ["image_slot_section_present"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_compatible",
        "description": "Remove compatible= from [update]. RAUC refuses to install a bundle with no device pin; system.conf check fails.",
        "mutation": _drop_compatible,
        "must_fail": [
            "update_has_compatible",
            "compatible_uses_vendor_comma_product_convention",
        ],
        "factor_id": "E6.1",
    },
    {
        "name": "drop_format",
        "description": "Remove format= from [bundle]. RAUC cannot decide how to parse the payload.",
        "mutation": _drop_format,
        "must_fail": ["bundle_has_format", "format_value_in_allowed_set"],
        "factor_id": "F6.1",
    },
    {
        "name": "invalid_format_value",
        "description": "format=invalid — not in {plain, verity, crypt}. RAUC rejects.",
        "mutation": _invalid_format_value,
        "must_fail": ["format_value_in_allowed_set"],
        "factor_id": "F1.1",
    },
    {
        "name": "drop_sha256",
        "description": "Remove sha256= from image slot. Integrity check gone; any bytes flow to disk.",
        "mutation": _drop_sha256,
        "must_fail": ["image_slot_has_sha256"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_filename",
        "description": "Remove filename= from image slot. RAUC cannot locate bundled image.",
        "mutation": _drop_filename,
        "must_fail": ["image_slot_has_filename"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_size",
        "description": "Remove size=. RAUC's install progress reporting breaks; streaming copy cannot pre-allocate.",
        "mutation": _drop_size,
        "must_fail": ["image_slot_has_size"],
        "factor_id": "F6.2",
    },
    {
        "name": "yamlify",
        "description": "Prepend YAML ``---`` marker. Bundle manifest is now claimed to be YAML; RAUC parser rejects it.",
        "mutation": _yamlify,
        "must_fail": ["no_non_ini_grammar"],
        "factor_id": "F6.1",
    },
    {
        "name": "libconfigify",
        "description": "Emit libconfig ``update = { ... };`` top form. Classic SWUpdate-vs-RAUC grammar confusion.",
        "mutation": _libconfigify,
        "must_fail": ["no_non_ini_grammar"],
        "factor_id": "F2.1",
    },
    {
        "name": "compatible_no_comma",
        "description": "compatible=vendor-example-device (hyphen, no comma). RAUC's convention is vendor,product; a comma-less string still matches syntactically but fails convention.",
        "mutation": _compatible_no_comma,
        "must_fail": ["compatible_uses_vendor_comma_product_convention"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_update_section",
        "description": "Remove [update] section entirely. RAUC cannot determine the bundle's identity.",
        "mutation": _drop_update_section,
        "must_fail": [
            "update_has_compatible",
            "update_has_version",
            "update_has_description",
            "update_section_header",
        ],
        "factor_id": "F6.1",
    },
]
