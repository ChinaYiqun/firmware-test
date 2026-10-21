Write a SWUpdate ``sw-description`` for a dual-bank embedded Linux
device whose bootloader implements an A/B failback mechanism via a
boot counter.

Context:
- Target: embedded Linux device on Yocto kirkstone with SWUpdate ~2022.12.
- Storage layout: eMMC with two equivalent partitions per image (boot,
  kernel, rootfs) — one bank active, the other pending.
- U-Boot bootcnt: after a pending-bank update completes, the bootloader
  increments a counter on each boot attempt. If the new image fails to
  confirm within the configured retry budget, the bootloader falls back
  to the previously-known-good bank.
- The device exposes its bootloader environment through the U-Boot
  fw_env interface, so SWUpdate can write env vars as part of the
  update transaction.

Requirements:
1. Top-level ``software = { ... };`` block with ``version``,
   ``description``, and a non-empty ``hardware-compatibility`` list.
2. Inside ``software``, declare two selection groups named ``copy-1``
   and ``copy-2``. Each group contains an ``images: ( ... );`` list
   that writes bootloader + kernel + rootfs to that bank's partitions.
3. The two groups target distinct block device paths for every image —
   no partition is shared between banks.
4. Every image entry in every group has ``filename``, ``device``, and
   ``sha256`` fields.
5. At the ``software`` level, declare a ``bootenv: ( ... );`` list
   that writes at least these two bootloader environment entries:
   - ``bootcount_enable`` with value ``"1"`` (activates bootcnt).
   - ``upgrade_available`` with value ``"1"`` (tells the bootloader a
     new image is pending).
6. Each bootenv entry is a ``{ name = "..."; value = "..."; }`` dict.

Directive surface — these names belong to libconfig and SWUpdate and
are mandatory: ``software``, ``version``, ``hardware-compatibility``,
``images``, ``filename``, ``device``, ``sha256``, ``bootenv``,
``name``, ``value``. Selection group names ``copy-1`` and ``copy-2``
are convention in SWUpdate examples and ARE part of the mandatory
surface for this TC.

Do NOT reference the ``swupdate`` CLI, the U-Boot ``setenv`` command,
the systemd service, or the .swu bundle format.

Output ONLY the complete sw-description content.
