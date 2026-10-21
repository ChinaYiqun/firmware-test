Write a SWUpdate ``sw-description`` for a signed firmware update.

Context:
- Target: embedded Linux device on Yocto kirkstone with SWUpdate ~2022.12.
- The build system signs the ``.swu`` bundle with a CMS envelope; the
  device refuses to install a bundle whose envelope signature does not
  match its provisioned public key.
- Each payload image additionally carries its own per-image integrity
  digest so corruption after envelope verification (e.g. during
  streaming copy) is still caught.

Requirements:
1. Top-level ``software = { ... };`` block containing:
   - ``version`` (semver).
   - ``description`` (human-readable).
   - ``hardware-compatibility`` list with at least one entry.
   - ``build`` string — a traceable build identifier (e.g. a git hash
     or a CI job id).
2. A single selection group containing an ``images: ( ... );`` list
   with at least two image entries (bootloader + rootfs is fine).
3. Every image entry has:
   - ``filename``, ``device``.
   - ``sha256`` — a 64-character lowercase hex digest (the per-image
     integrity check).
   - an ``encrypted = true;`` boolean flag indicating the payload will
     be decrypted before it's written.
4. NOWHERE in the document may there be an MD5 (``md5 = ...``) or
   SHA-1 (``sha1 = ...``) digest key. SWUpdate accepts these historically
   but both are cryptographically broken for firmware verification.
5. NOWHERE may there be a plaintext password, AES key, or RSA private
   key string — keys live on the device, not in the descriptor. Do not
   include keys like ``password = "..."`` or ``aes-key = "..."`` or
   ``pkey`` / ``private-key``.
6. All sha256 values are 64 lowercase hex characters (not 32 — that
   would be md5 length — and not uppercase).

Directive surface: ``software``, ``version``, ``description``, ``build``,
``hardware-compatibility``, ``images``, ``filename``, ``device``,
``sha256``, ``encrypted``.

Do NOT reference the CLI flags (``-k`` ``-K``) or the signing script.

Output ONLY the complete sw-description content.
