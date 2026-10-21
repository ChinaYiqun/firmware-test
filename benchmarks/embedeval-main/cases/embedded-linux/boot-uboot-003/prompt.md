Write a ``/boot/extlinux/extlinux.conf`` file for U-Boot's
``distro_boot`` scanning mechanism to find and boot a Linux image on
an i.MX8M Plus target.

Context:
- U-Boot 2022.04 with distro_boot scans boot media for
  ``/boot/extlinux/extlinux.conf`` in a BLS/syslinux-compatible
  format.
- Rootfs is on the second partition of the SD card, mounted as
  ``/dev/mmcblk1p2``.
- The kernel Image, device-tree blob, and initramfs all live under
  ``/boot/`` on the first partition.

Requirements:
1. First directive: ``default <label>`` naming the default boot entry.
2. ``timeout`` set to a low value (e.g. 10 deciseconds).
3. A ``label`` block named ``linux`` (matching the default) containing:
   - ``kernel /boot/Image``
   - ``fdt /boot/imx8mp.dtb``
   - ``initrd /boot/initramfs.cpio.gz``
   - ``append`` line with ``root=/dev/mmcblk1p2 rootwait console=ttymxc1,115200``

Do NOT include PXE-style ``menu title`` or multiple labels — keep the
file minimal.

Output ONLY the complete extlinux.conf content.
