"""Negative tests for yocto-009 (meta-layer conf/layer.conf)."""


def _drop_layerseries_compat(code: str) -> str:
    return code.replace(
        'LAYERSERIES_COMPAT_example-sensors-layer = "kirkstone"\n', ""
    )


def _swap_kirkstone_to_dunfell(code: str) -> str:
    """Pre-kirkstone compat — fails on kirkstone parse."""
    return code.replace('"kirkstone"', '"dunfell"')


def _drop_bbpath(code: str) -> str:
    return code.replace('BBPATH .= ":${LAYERDIR}"\n\n', "")


def _swap_bbpath_append_to_overwrite(code: str) -> str:
    return code.replace('BBPATH .= ":${LAYERDIR}"', 'BBPATH = "${LAYERDIR}"')


def _drop_bbfile_collections(code: str) -> str:
    return code.replace(
        'BBFILE_COLLECTIONS += "example-sensors-layer"\n', ""
    )


def _drop_bbfile_pattern(code: str) -> str:
    return code.replace(
        'BBFILE_PATTERN_example-sensors-layer = "^${LAYERDIR}/"\n', ""
    )


def _drop_caret_anchor(code: str) -> str:
    return code.replace(
        '"^${LAYERDIR}/"', '"${LAYERDIR}/"'
    )


def _drop_priority(code: str) -> str:
    return code.replace(
        'BBFILE_PRIORITY_example-sensors-layer = "10"\n', ""
    )


def _priority_non_numeric(code: str) -> str:
    return code.replace('"10"', '"high"')


def _drop_bbappend_pattern(code: str) -> str:
    return code.replace("\n            ${LAYERDIR}/recipes-*/*/*.bbappend", "")


def _drop_bb_pattern(code: str) -> str:
    return code.replace("${LAYERDIR}/recipes-*/*/*.bb \\\n", "")


def _rename_collection_to_mismatch(code: str) -> str:
    """Collection name mismatch — BBFILE_COLLECTIONS says one thing but
    BBFILE_PATTERN_/_PRIORITY_ use another. BitBake errors out."""
    return code.replace(
        'BBFILE_COLLECTIONS += "example-sensors-layer"',
        'BBFILE_COLLECTIONS += "other-layer-name"',
    )


NEGATIVES = [
    {
        "name": "drop_layerseries_compat",
        "description": "Remove LAYERSERIES_COMPAT_* — kirkstone refuses to parse the layer.",
        "mutation": _drop_layerseries_compat,
        "must_fail": ["layerseries_compat_defined", "layerseries_compat_kirkstone"],
        "factor_id": "F6.1",
    },
    {
        "name": "wrong_layerseries_dunfell",
        "description": "LAYERSERIES_COMPAT set to dunfell — build system refuses layer on kirkstone.",
        "mutation": _swap_kirkstone_to_dunfell,
        "must_fail": ["layerseries_compat_kirkstone"],
        "factor_id": "F4.1",
    },
    {
        "name": "drop_bbpath",
        "description": "Remove BBPATH — layer's conf/ and classes/ directories unreachable.",
        "mutation": _drop_bbpath,
        "must_fail": ["bbpath_defined", "bbpath_uses_append_form"],
        "factor_id": "F6.1",
    },
    {
        "name": "overwrite_bbpath",
        "description": "Use BBPATH = ... (overwrite) instead of .= — clobbers parent BBPATH.",
        "mutation": _swap_bbpath_append_to_overwrite,
        "must_fail": ["bbpath_uses_append_form"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_bbfile_collections",
        "description": "Remove BBFILE_COLLECTIONS — layer is not registered with bitbake-layers.",
        "mutation": _drop_bbfile_collections,
        "must_fail": [
            "bbfile_collections_defined",
            "collection_name_declared",
        ],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_bbfile_pattern",
        "description": "Remove BBFILE_PATTERN_* — BitBake cannot match files to this collection.",
        "mutation": _drop_bbfile_pattern,
        "must_fail": ["bbfile_pattern_defined", "bbfile_pattern_anchored"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_caret_anchor",
        "description": "BBFILE_PATTERN_ without the caret — matches all .bb files, not just this layer's.",
        "mutation": _drop_caret_anchor,
        "must_fail": ["bbfile_pattern_anchored"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_priority",
        "description": "Remove BBFILE_PRIORITY_ — layer parse warning; collisions resolve unpredictably.",
        "mutation": _drop_priority,
        "must_fail": ["bbfile_priority_defined", "bbfile_priority_is_numeric"],
        "factor_id": "F6.1",
    },
    {
        "name": "priority_non_numeric",
        "description": "Set BBFILE_PRIORITY_ to a string instead of a number — parse error.",
        "mutation": _priority_non_numeric,
        "must_fail": ["bbfile_priority_is_numeric"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_bbappend_pattern",
        "description": "Drop *.bbappend from BBFILES — bbappends in this layer are invisible to bitbake.",
        "mutation": _drop_bbappend_pattern,
        "must_fail": ["bbfiles_covers_bb_and_bbappend"],
        "factor_id": "F6.1",
    },
    {
        "name": "drop_bb_pattern",
        "description": "Drop *.bb from BBFILES — recipes in this layer are invisible.",
        "mutation": _drop_bb_pattern,
        "must_fail": ["bbfiles_covers_bb_and_bbappend"],
        "factor_id": "F6.1",
    },
    {
        "name": "collection_name_mismatch",
        "description": "BBFILE_COLLECTIONS declares one name but BBFILE_PATTERN_ / _PRIORITY_ use another — BitBake errors out on collection name mismatch.",
        "mutation": _rename_collection_to_mismatch,
        "must_fail": ["collection_name_declared"],
        "factor_id": "F6.2",
    },
]
