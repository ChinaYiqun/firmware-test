"""Tests for OTA helpers (Phase C-1).

Covers the five helpers used by ota-swupdate-* and ota-rauc-* TCs:
swupdate_libconfig_has, swupdate_images_has_sha256,
swupdate_hardware_compatibility_list, rauc_manifest_section_has,
rauc_image_slots.

Each helper has ≥3 tests: happy path, false-positive trap
(grammar that looks similar but isn't the target), and grammar-variant
acceptance (different-but-valid spelling).
"""

from __future__ import annotations

from embedeval.check_utils import (
    rauc_image_slots,
    rauc_manifest_section_has,
    swupdate_hardware_compatibility_list,
    swupdate_images_has_sha256,
    swupdate_libconfig_has,
)

# ---------------------------------------------------------------------------
# swupdate_libconfig_has
# ---------------------------------------------------------------------------


def test_swupdate_libconfig_has_top_level_key() -> None:
    sw = """
    software = {
        version = "1.0.0";
        description = "Example firmware";
    };
    """
    assert swupdate_libconfig_has(sw, "software", "version") == "1.0.0"
    assert (
        swupdate_libconfig_has(sw, "software", "description") == "Example firmware"
    )


def test_swupdate_libconfig_has_nested_section() -> None:
    sw = """
    software = {
        stable = {
            copy-1 = {
                description = "first bank";
            };
            copy-2 = {
                description = "second bank";
            };
        };
    };
    """
    # Dashes in section names must be supported.
    assert (
        swupdate_libconfig_has(sw, "software.stable.copy-1", "description")
        == "first bank"
    )
    assert (
        swupdate_libconfig_has(sw, "software.stable.copy-2", "description")
        == "second bank"
    )


def test_swupdate_libconfig_has_ignores_comments() -> None:
    """``#`` line comments inside a section must not hide valid directives."""
    sw = """
    software = {
        # This comment looks like version = "fake";
        version = "2.5.1";
        description = "real value";
    };
    """
    assert swupdate_libconfig_has(sw, "software", "version") == "2.5.1"


def test_swupdate_libconfig_has_missing_returns_none() -> None:
    sw = "software = { version = \"1.0\"; };"
    assert swupdate_libconfig_has(sw, "software", "absent") is None
    assert swupdate_libconfig_has(sw, "missing.section", "version") is None


def test_swupdate_libconfig_has_accepts_bool_and_numeric() -> None:
    """libconfig accepts ``encrypted = true;`` (bool) and ``size = 1024;``
    (int) alongside quoted strings. Helper preserves raw value."""
    sw = """
    software = {
        encrypted = true;
        size = 1024;
        hw = "imx8mp";
    };
    """
    assert swupdate_libconfig_has(sw, "software", "encrypted") == "true"
    assert swupdate_libconfig_has(sw, "software", "size") == "1024"
    assert swupdate_libconfig_has(sw, "software", "hw") == "imx8mp"


# ---------------------------------------------------------------------------
# swupdate_images_has_sha256
# ---------------------------------------------------------------------------


def test_swupdate_images_has_sha256_happy() -> None:
    sw = """
    images: (
        {
            filename = "u-boot.imx";
            device = "/dev/mmcblk0boot0";
            sha256 = "aa";
        },
        {
            filename = "Image";
            device = "/dev/mmcblk0p1";
            sha256 = "bb";
        }
    );
    """
    assert swupdate_images_has_sha256(sw) is True


def test_swupdate_images_has_sha256_missing_on_one_entry() -> None:
    sw = """
    images: (
        { filename = "u-boot.imx"; device = "/dev/a"; sha256 = "aa"; },
        { filename = "Image";      device = "/dev/b";                 }
    );
    """
    assert swupdate_images_has_sha256(sw) is False


def test_swupdate_images_has_sha256_no_list_returns_false() -> None:
    # No images list at all.
    sw = 'software = { version = "1.0"; };'
    assert swupdate_images_has_sha256(sw) is False


def test_swupdate_images_has_sha256_empty_list_returns_false() -> None:
    """An empty ``images: ( );`` is vacuously covered but practically
    useless; return False to flag it."""
    sw = "images: ( );"
    assert swupdate_images_has_sha256(sw) is False


# ---------------------------------------------------------------------------
# swupdate_hardware_compatibility_list
# ---------------------------------------------------------------------------


def test_swupdate_hardware_compatibility_list_happy() -> None:
    sw = 'hardware-compatibility = [ "1.0", "1.2" ];'
    assert swupdate_hardware_compatibility_list(sw) == ["1.0", "1.2"]


def test_swupdate_hardware_compatibility_list_single_entry() -> None:
    sw = 'hardware-compatibility = [ "1.0" ];'
    assert swupdate_hardware_compatibility_list(sw) == ["1.0"]


def test_swupdate_hardware_compatibility_list_missing() -> None:
    sw = 'software = { version = "1.0"; };'
    assert swupdate_hardware_compatibility_list(sw) == []


def test_swupdate_hardware_compatibility_list_multiline() -> None:
    """Upstream SWUpdate examples often multi-line the array."""
    sw = """
    hardware-compatibility = [
        "1.0",
        "1.2",
        "2.0"
    ];
    """
    assert swupdate_hardware_compatibility_list(sw) == ["1.0", "1.2", "2.0"]


# ---------------------------------------------------------------------------
# rauc_manifest_section_has
# ---------------------------------------------------------------------------


def test_rauc_manifest_section_has_flat_section() -> None:
    m = """
    [update]
    compatible=vendor,example-device
    version=1.0.0
    description=Example
    """
    assert (
        rauc_manifest_section_has(m, "update", "compatible")
        == "vendor,example-device"
    )
    assert rauc_manifest_section_has(m, "update", "version") == "1.0.0"


def test_rauc_manifest_section_has_dotted_section() -> None:
    """RAUC uses dotted section names — `configparser` would choke; our
    helper must accept them as opaque section names."""
    m = """
    [image.rootfs.0]
    filename=rootfs.0.ext4
    sha256=deadbeef

    [image.rootfs.1]
    filename=rootfs.1.ext4
    sha256=cafebabe
    """
    assert (
        rauc_manifest_section_has(m, "image.rootfs.0", "filename")
        == "rootfs.0.ext4"
    )
    assert (
        rauc_manifest_section_has(m, "image.rootfs.1", "filename")
        == "rootfs.1.ext4"
    )
    # Same key in a different section must not cross-contaminate.
    assert rauc_manifest_section_has(m, "image.rootfs.0", "sha256") == "deadbeef"


def test_rauc_manifest_section_has_missing_returns_none() -> None:
    m = "[update]\ncompatible=x\n"
    assert rauc_manifest_section_has(m, "update", "absent") is None
    assert rauc_manifest_section_has(m, "nosection", "key") is None


def test_rauc_manifest_section_has_ignores_comments() -> None:
    """``#`` line comments must not shadow real directives."""
    m = """
    [update]
    # compatible=fake
    compatible=real,value
    """
    assert (
        rauc_manifest_section_has(m, "update", "compatible") == "real,value"
    )


# ---------------------------------------------------------------------------
# rauc_image_slots
# ---------------------------------------------------------------------------


def test_rauc_image_slots_single_slot() -> None:
    m = """
    [update]
    compatible=x

    [image.rootfs]
    filename=rootfs.ext4
    """
    assert rauc_image_slots(m) == ["rootfs"]


def test_rauc_image_slots_ab_slots() -> None:
    m = """
    [image.rootfs.0]
    filename=rootfs.0.ext4

    [image.rootfs.1]
    filename=rootfs.1.ext4
    """
    assert rauc_image_slots(m) == ["rootfs.0", "rootfs.1"]


def test_rauc_image_slots_ignores_non_image_sections() -> None:
    m = """
    [update]
    compatible=x
    [bundle]
    format=plain
    [image.rootfs]
    filename=a
    [hooks]
    filename=hook.sh
    """
    assert rauc_image_slots(m) == ["rootfs"]


def test_rauc_image_slots_preserves_order() -> None:
    m = """
    [image.bootloader]
    filename=b
    [image.rootfs]
    filename=r
    [image.appfs]
    filename=a
    """
    assert rauc_image_slots(m) == ["bootloader", "rootfs", "appfs"]
