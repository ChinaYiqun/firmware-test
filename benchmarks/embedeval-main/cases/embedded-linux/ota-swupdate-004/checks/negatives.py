"""Negative tests for ota-swupdate-004 (scripts + lifecycle)."""

import re


def _drop_scripts_list(code: str) -> str:
    return re.sub(
        r"scripts:\s*\([\s\S]*?\)\s*;",
        "",
        code,
        count=1,
    )


def _only_one_script(code: str) -> str:
    """Remove the second script entry (post-install.lua)."""
    return re.sub(
        r",\s*\{[^{}]*?post-install\.lua[^{}]*?\}",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_preinstall_type(code: str) -> str:
    """Drop the preinstall entry entirely."""
    return re.sub(
        r"\{[^{}]*?pre-install\.sh[^{}]*?\}\s*,?\s*",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _drop_lua_type(code: str) -> str:
    return re.sub(
        r",?\s*\{[^{}]*?post-install\.lua[^{}]*?\}",
        "",
        code,
        count=1,
        flags=re.DOTALL,
    )


def _custom_script_type(code: str) -> str:
    return code.replace('type = "preinstall"', 'type = "custom"')


def _misspell_preinstall(code: str) -> str:
    return code.replace('type = "preinstall"', 'type = "preinstal"')


def _duplicate_filenames(code: str) -> str:
    """Make both scripts share the same filename."""
    return code.replace("post-install.lua", "pre-install.sh")


def _drop_sha256_on_one_script(code: str) -> str:
    """Drop the first script's sha256 line only."""
    # First sha256 inside scripts: ( ... ) is the preinstall one.
    m = re.search(r"scripts:\s*\(", code)
    if not m:
        return code
    start = m.end()
    return (
        code[:start]
        + re.sub(r'^\s*sha256\s*=.*\n', "", code[start:], count=1, flags=re.MULTILINE)
    )


def _drop_filename_on_one_script(code: str) -> str:
    return re.sub(
        r'^\s*filename\s*=\s*"pre-install\.sh".*\n',
        "",
        code,
        count=1,
        flags=re.MULTILINE,
    )


def _drop_hw_compat(code: str) -> str:
    return re.sub(
        r'^\s*hardware-compatibility\s*=.*\n',
        "",
        code,
        count=1,
        flags=re.MULTILINE,
    )


def _drop_images_list(code: str) -> str:
    return re.sub(
        r"images:\s*\([\s\S]*?\)\s*;",
        "",
        code,
        count=1,
    )


def _inline_shell_in_description(code: str) -> str:
    return code.replace(
        'description = "Update with pre-install and post-install lifecycle handlers"',
        'description = "Update; rm -rf /var/lib/app-state"',
    )


def _scripts_as_dict_not_list(code: str) -> str:
    return re.sub(
        r"scripts:\s*\(",
        "scripts = {",
        code,
        count=1,
    ).replace(");", "};", 1)


NEGATIVES = [
    {
        "name": "drop_scripts_list",
        "description": "Remove the scripts list entirely. Lifecycle hooks never run — pre-state capture and post-state signalling disappear.",
        "mutation": _drop_scripts_list,
        "must_fail": [
            "scripts_list_present",
            "two_script_entries",
            "scripts_keyword_present",
        ],
        "factor_id": "F6.1",
    },
    {
        "name": "only_one_script",
        "description": "Keep only the preinstall entry. Post-install Lua handler is missing — post-state signalling never happens.",
        "mutation": _only_one_script,
        "must_fail": ["two_script_entries", "has_postinstall_or_lua_script"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_preinstall_type",
        "description": "Drop the preinstall entry. Pre-state capture before image write is gone.",
        "mutation": _drop_preinstall_type,
        "must_fail": ["has_preinstall_script", "two_script_entries"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_lua_postinstall",
        "description": "Drop the Lua post-install entry. Post-state signalling gone.",
        "mutation": _drop_lua_type,
        "must_fail": ["has_postinstall_or_lua_script", "two_script_entries"],
        "factor_id": "F6.2",
    },
    {
        "name": "custom_script_type",
        "description": "Swap type = \"preinstall\" for a non-whitelisted ``custom`` value. SWUpdate parser rejects unknown type strings.",
        "mutation": _custom_script_type,
        "must_fail": ["script_types_from_allowed_set", "has_preinstall_script"],
        "factor_id": "F1.1",
    },
    {
        "name": "misspell_preinstall",
        "description": "Typo preinstall → preinstal. Same class of parser rejection.",
        "mutation": _misspell_preinstall,
        "must_fail": ["script_types_from_allowed_set", "has_preinstall_script"],
        "factor_id": "F1.1",
    },
    {
        "name": "duplicate_filenames",
        "description": "Two script entries share the same filename. SWUpdate treats filename as handler identity — the second entry overwrites the first silently.",
        "mutation": _duplicate_filenames,
        "must_fail": ["distinct_script_filenames"],
        "factor_id": "E3.1",
    },
    {
        "name": "drop_sha256_on_one_script",
        "description": "Remove sha256 from one script entry. Untrusted handler bytes can execute on the device.",
        "mutation": _drop_sha256_on_one_script,
        "must_fail": ["each_script_has_sha256"],
        "factor_id": "E7.1",
    },
    {
        "name": "drop_filename_on_one_script",
        "description": "Remove filename= from one script entry. Handler cannot be located in the bundle.",
        "mutation": _drop_filename_on_one_script,
        "must_fail": ["each_script_has_filename"],
        "factor_id": "F6.2",
    },
    {
        "name": "drop_hw_compatibility",
        "description": "Remove hardware-compatibility. Scripts run on incompatible hardware.",
        "mutation": _drop_hw_compat,
        "must_fail": ["hardware_compatibility_list_nonempty"],
        "factor_id": "E6.1",
    },
    {
        "name": "drop_images_list",
        "description": "Remove the images list. Scripts run but no image is actually written — pointless update.",
        "mutation": _drop_images_list,
        "must_fail": ["at_least_one_image", "images_keyword_present"],
        "factor_id": "F6.1",
    },
    {
        "name": "inline_shell_in_description",
        "description": "Embed ``rm -rf /var/lib/app-state`` in description= field. Idempotency red flag — destructive inline commands suggest the LLM inlined logic instead of using script entries.",
        "mutation": _inline_shell_in_description,
        "must_fail": ["no_inline_shell_in_description"],
        "factor_id": "E6.1",
    },
    {
        "name": "scripts_as_dict_not_list",
        "description": "Swap scripts: ( ... ); list form to scripts = { ... }; dict form. Entries no longer iterate.",
        "mutation": _scripts_as_dict_not_list,
        "must_fail": [
            "scripts_list_present",
            "two_script_entries",
        ],
        "factor_id": "F1.1",
    },
]
