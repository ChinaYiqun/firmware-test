Write a RAUC bundle manifest (``manifest.raucm``) covering an A/B
rootfs layout with an install-check hook.

Context:
- Target: embedded Linux device on Yocto kirkstone with RAUC 1.7.
- A/B layout: two rootfs partitions. At install time RAUC writes to
  the currently inactive slot, then flips the boot selector — an
  atomic switchover. Slots share a class (``rootfs``) but have
  distinct indices (0 and 1).
- Per-slot hooks or a global install-check hook run at defined points
  in the install pipeline. The ``[hooks]`` section registers a hook
  filename that exists inside the bundle.

Requirements:
1. ``[update]`` section with ``compatible=<vendor,product>``,
   ``version=<semver>``, and ``description=<string>``.
2. ``[bundle]`` section with ``format=<plain|verity|crypt>``.
3. Two rootfs slot sections:
   - ``[image.rootfs.0]`` — index 0.
   - ``[image.rootfs.1]`` — index 1.
   Each has ``filename``, ``sha256``, and ``size`` directives. The
   filenames AND sha256 values across the two slots are distinct
   (different images per slot); sharing either would mean both slots
   point at the same bytes, breaking the A/B invariant.
4. ``[hooks]`` section registering a global hook:
   ``filename=<hook-script-name>`` — the executable that RAUC runs for
   the install lifecycle.
5. Slot class naming follows ``image.<class>.<index>`` — index is a
   non-negative integer. NOT ``image.rootfs.a`` / ``image.rootfs.b``.

Directive surface: ``[update]``, ``[bundle]``, ``[image.rootfs.0]``,
``[image.rootfs.1]``, ``[hooks]``, ``compatible``, ``version``,
``description``, ``format``, ``filename``, ``sha256``, ``size``.

Do NOT reference the ``rauc`` CLI, and do NOT wrap content in YAML /
TOML / libconfig / JSON.

Output ONLY the complete manifest.raucm content.
