Write a U-Boot FIT image source (.its) that is signed for
verified-boot: an unsigned FIT must be rejected by the board at boot
time.

Context:
- Target: NXP i.MX8M Plus (ARM64), u-boot-imx 2022.04.
- The signing key pair lives in the build system; the public key is
  baked into U-Boot's control FDT out of band.
- Key identifier (``key-name-hint``): ``boot-key``.
- Signature parameters: RSA 4096 + SHA-256.
- For verified boot to work, the configuration node (not the
  individual images) must carry a ``signature`` sub-node that covers
  the configuration — U-Boot will then refuse to boot the FIT unless
  the signature is valid and the configuration node declares the
  properties the signature covers as "required".

Requirements:
1. Standard FIT preamble: ``/dts-v1/;`` and root node with
   ``description`` + ``#address-cells``.
2. ``images { ... }`` with at least one kernel sub-image carrying
   ``type = "kernel"``, ``arch = "arm64"``, ``os = "linux"``,
   ``data = /incbin/("./Image");``, ``load``, ``entry``, and a
   ``hash`` sub-node using ``sha256``.
3. ``configurations { ... }`` with:
   - ``default = "config-1"``.
   - A ``config-1`` sub-node that:
     - References the kernel sub-image.
     - Contains a ``signature`` sub-node (any name, e.g.
       ``signature-1``) with:
       - ``algo = "sha256,rsa4096"``
       - ``key-name-hint = "boot-key"``
       - ``sign-images = "kernel"`` — declares WHICH sub-image
         properties the signature covers.
4. The ``signature`` sub-node's ``sign-images`` property is required;
   without it U-Boot's mkimage will sign but U-Boot at boot won't
   know which images the signature was meant to cover.

Output ONLY the complete .its source.
