Write a U-Boot FIT image source (.its) that packages three
sub-images — a kernel, a device tree, and an initramfs — and declares
a single default configuration selecting all three.

Context:
- Target: NXP i.MX8M Plus (ARM64).
- U-Boot: u-boot-imx 2022.04.
- The FIT image is produced by ``mkimage -f <this.its> image.itb``.
- When the board executes ``bootm <addr>``, U-Boot will pick the
  configuration named ``default`` (by convention), then load the
  referenced kernel / fdt / ramdisk sub-images by reference.

Requirements:
1. Device-tree-source header: ``/dts-v1/;`` + root node ``/ { ... };``.
2. Root node properties:
   - ``description`` — any human-readable string.
   - A version property, e.g. ``#address-cells = <1>;``.
3. ``images { ... };`` node containing three sub-images:
   a. A kernel sub-image with ``description``, ``data``, ``type = "kernel"``,
      ``arch = "arm64"``, ``os = "linux"``, ``compression``, plus
      ``load`` and ``entry`` address properties, and a ``hash``
      sub-node selecting algorithm ``sha256``.
   b. A device-tree sub-image with ``type = "flat_dt"`` and a
      matching ``hash`` sub-node with ``sha256``.
   c. A ramdisk sub-image with ``type = "ramdisk"``, ``compression``,
      ``os = "linux"``, and a ``hash`` sub-node with ``sha256``.
4. ``configurations { ... };`` node that declares ``default =
   "config-1"`` and contains a ``config-1`` sub-node referencing the
   three sub-images via ``kernel``, ``fdt``, and ``ramdisk``
   properties.
5. Every sub-image that ships bytes has a ``hash`` sub-node, because
   U-Boot refuses to boot a FIT sub-image that lacks an integrity
   hash when the board is configured for hash checking.

Output ONLY the complete .its source.
