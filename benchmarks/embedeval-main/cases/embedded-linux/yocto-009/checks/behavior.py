"""Behavioral checks for yocto-009 (meta-layer conf/layer.conf)."""

import re

from embedeval.check_utils import strip_yocto_comments, yocto_contains
from embedeval.models import CheckDetail


def run_checks(generated_code: str) -> list[CheckDetail]:
    details: list[CheckDetail] = []
    body = strip_yocto_comments(generated_code)

    # 1. Collection name is example-sensors-layer — must appear in
    # BBFILE_COLLECTIONS specifically (not just in PATTERN/PRIORITY).
    has_collection = bool(
        re.search(
            r'BBFILE_COLLECTIONS\s*\+?=\s*"[^"]*\bexample-sensors-layer\b',
            body,
        )
    )
    details.append(
        CheckDetail(
            check_name="collection_name_declared",
            passed=has_collection,
            expected='BBFILE_COLLECTIONS += "example-sensors-layer"',
            actual="present" if has_collection else "missing",
            check_type="constraint",
        )
    )

    # 2. LAYERSERIES_COMPAT set to kirkstone. Collection names may
    # contain hyphens, so allow any non-whitespace suffix after the
    # directive prefix.
    has_kirkstone = bool(
        re.search(r"LAYERSERIES_COMPAT\S*\s*=\s*\"[^\"]*kirkstone", body)
    )
    details.append(
        CheckDetail(
            check_name="layerseries_compat_kirkstone",
            passed=has_kirkstone,
            expected="LAYERSERIES_COMPAT_* includes kirkstone",
            actual="kirkstone" if has_kirkstone else "missing / wrong release",
            check_type="constraint",
        )
    )

    # 3. BBFILE_PATTERN_ is anchored to ${LAYERDIR} with a caret regex
    # (required by BitBake — otherwise it matches everything).
    has_anchored_pattern = bool(
        re.search(r"BBFILE_PATTERN_\S+\s*=\s*\"\^\$\{LAYERDIR\}", body)
    )
    details.append(
        CheckDetail(
            check_name="bbfile_pattern_anchored",
            passed=has_anchored_pattern,
            expected='BBFILE_PATTERN_* = "^${LAYERDIR}/"',
            actual="present" if has_anchored_pattern else "missing caret anchor",
            check_type="constraint",
        )
    )

    # 4. Priority set numerically.
    has_priority = bool(
        re.search(r"BBFILE_PRIORITY_\S+\s*=\s*\"\d+\"", body)
    )
    details.append(
        CheckDetail(
            check_name="bbfile_priority_is_numeric",
            passed=has_priority,
            expected='BBFILE_PRIORITY_* = "<number>"',
            actual="present" if has_priority else "missing or non-numeric",
            check_type="constraint",
        )
    )

    # 5. BBFILES covers both .bb and .bbappend (two-level layout).
    # ``*.bb`` must match as a standalone glob, not as a prefix of
    # ``*.bbappend``. Use the explicit glob shape.
    has_bb = bool(re.search(r"\*\.bb(?:\b|\"|\s|\\)", body))
    has_bbappend = "*.bbappend" in body
    details.append(
        CheckDetail(
            check_name="bbfiles_covers_bb_and_bbappend",
            passed=has_bb and has_bbappend,
            expected="BBFILES patterns include *.bb and *.bbappend",
            actual=f"bb={has_bb}, bbappend={has_bbappend}",
            check_type="constraint",
        )
    )

    # 6. BBPATH uses `.=` append form so the parent BBPATH is preserved.
    has_bbpath_append = bool(
        re.search(r"BBPATH\s*\.=\s*\"", body)
    )
    details.append(
        CheckDetail(
            check_name="bbpath_uses_append_form",
            passed=has_bbpath_append,
            expected='BBPATH .= ":${LAYERDIR}" (append, not overwrite)',
            actual="present" if has_bbpath_append else "WRONG: BBPATH = ...",
            check_type="constraint",
        )
    )

    return details
