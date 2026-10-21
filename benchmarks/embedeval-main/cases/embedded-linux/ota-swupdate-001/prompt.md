Write a SWUpdate ``sw-description`` that installs three partition
images (bootloader, kernel, rootfs) onto a single-bank eMMC layout.

Context:
- Target: embedded Linux device on Yocto kirkstone with SWUpdate ~2022.12.
- The daemon reads ``sw-description`` from inside the ``.swu`` bundle at
  update time.
- Hardware compatibility is declared as a list of acceptable hardware
  revisions; the installer refuses to apply on revisions outside the list.

Requirements:
1. Top-level ``software = { ... };`` block.
2. Inside the ``software`` block, declare:
   - a ``version`` string (semver).
   - a human-readable ``description`` string.
   - a ``hardware-compatibility`` list with at least one entry.
3. A single selection group (any name) containing an ``images: ( ... );``
   list with three entries. Each entry is a ``{ ... }`` dict with:
   - ``filename`` — the in-bundle image name (e.g. ``u-boot.imx``).
   - ``device`` — the target block device (e.g. ``/dev/mmcblk0p1``).
   - ``sha256`` — a 64-character lowercase hex digest.
4. All three images are on distinct ``device`` paths.
5. No YAML / JSON syntax — this is libconfig (``key = value;`` +
   ``{ ... };`` + ``( ... );`` + ``#`` line comments).

Directive surface — these names are mandatory and belong to libconfig:
``software``, ``version``, ``description``, ``hardware-compatibility``,
``images``, ``filename``, ``device``, ``sha256``.

Do NOT reference the SWUpdate command-line (``swupdate -v``, ``-k``,
``-K``), the systemd service, or the update-bundle format. Only emit
the ``sw-description`` body.

Output ONLY the complete sw-description content.
