Write a minimal RAUC bundle manifest (``manifest.raucm``) for an
embedded Linux device.

Context:
- Target: embedded Linux device on Yocto kirkstone with RAUC 1.7.
- ``manifest.raucm`` is INI-formatted — ``[section]`` headers +
  ``key=value`` lines + ``#`` line comments. NOT YAML, NOT libconfig.
- RAUC validates the ``compatible`` string against the device's
  ``system.conf`` at install time; non-matching bundles are rejected.
- Image slot sections use a compound section name beginning with the
  slot class, separated by dots: ``[image.<slot-class>]`` for a single
  slot, or ``[image.<slot-class>.<index>]`` for an A/B layout.

Requirements:
1. ``[update]`` section with:
   - ``compatible=<vendor,product>`` string identifying the device.
   - ``version=<semver>``.
   - ``description=<string>``.
2. ``[bundle]`` section with:
   - ``format=plain`` (or ``verity`` or ``crypt`` — ``plain`` is fine
     for this TC).
3. A single image-slot section ``[image.rootfs]`` (NOT ``[rootfs]``,
   NOT ``[images.rootfs]``, NOT ``[image rootfs]``). Inside it:
   - ``filename=<in-bundle image name>``.
   - ``sha256=<64-hex digest>``.
   - ``size=<payload byte count>``.

Directive surface: ``[update]``, ``[bundle]``, ``[image.rootfs]``,
``compatible``, ``version``, ``description``, ``format``, ``filename``,
``sha256``, ``size``. These literally appear in the output.

Do NOT reference ``rauc install`` / ``rauc info`` / ``rauc status``
commands, and do NOT wrap the content in YAML, TOML, libconfig, or
JSON.

Output ONLY the complete manifest.raucm content.
