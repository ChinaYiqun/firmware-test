Write a SWUpdate ``sw-description`` that installs one image and runs
two lifecycle scripts — a pre-install shell script and a post-install
Lua handler — around the image write.

Context:
- Target: embedded Linux device on Yocto kirkstone with SWUpdate ~2022.12.
- Scripts inside a ``.swu`` bundle run at well-defined points:
  preinstall runs before any image writes; postinstall runs after the
  last image write completes.
- SWUpdate supports these script types only:
  ``preinstall``, ``postinstall``, ``shellscript``, ``lua``, ``swupdate``.
  Other values are rejected by the parser.
- Two script entries must not share a filename — SWUpdate uses the
  filename as the handler identity.

Requirements:
1. Top-level ``software = { ... };`` block with ``version``,
   ``description``, and a non-empty ``hardware-compatibility`` list.
2. A selection group with an ``images: ( ... );`` list containing at
   least one image entry (filename + device + sha256).
3. A ``scripts: ( ... );`` list at the ``software`` level, containing
   exactly two entries:
   - a shell script with ``filename = "..."``, ``type = "preinstall"``,
     and a ``sha256 = "..."`` field (64-hex integrity digest).
   - a Lua handler with ``filename = "..."``, ``type = "lua"``, and a
     ``sha256 = "..."`` field.
4. The two script entries have distinct ``filename`` values.
5. Every script entry's ``type`` is one of the five allowed values listed
   above — no custom or misspelled types.

Directive surface: ``software``, ``version``, ``hardware-compatibility``,
``images``, ``filename``, ``device``, ``sha256``, ``scripts``, ``type``.
Values of ``type`` — ``preinstall``, ``postinstall``, ``shellscript``,
``lua``, ``swupdate`` — are grammar surface and may be referenced
literally.

Do NOT reference the SWUpdate CLI, the systemd service, or the
``.swu`` bundle format. Do NOT inline shell commands inside
``description``.

Output ONLY the complete sw-description content.
