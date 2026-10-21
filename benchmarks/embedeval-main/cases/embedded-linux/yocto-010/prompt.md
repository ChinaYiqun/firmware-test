Write a Yocto 4.0 (kirkstone) ``.bbappend`` that extends the upstream
``openssh`` recipe with an extra sshd configuration file and an extra
runtime dependency.

Context:
- The layer places the additional sshd config at
  ``files/sshd_config_harden``.
- The appended behavior must use the modern colon-form override
  syntax (``:append`` and ``FILESEXTRAPATHS:prepend``). The legacy
  underscore-form (``_append``, ``FILESEXTRAPATHS_prepend``) parses
  on kirkstone but is the older, deprecated idiom — do NOT use it.

Requirements:
1. Prepend FILESEXTRAPATHS with ``${THISDIR}/files`` (so the new
   config file is findable) — use the colon override form.
2. Append to SRC_URI the ``file://sshd_config_harden`` entry — colon form.
3. Append ``audit`` to the runtime dependencies of the main package
   via RDEPENDS:${PN} — colon form.
4. In a do_install:append() function body, install the new config
   file under ``${D}${sysconfdir}/ssh/sshd_config.d/`` with mode 0644.

Do NOT declare SUMMARY / LICENSE / LIC_FILES_CHKSUM — the .bbappend
inherits those from the base recipe. Do NOT use underscore-form
overrides.

Output ONLY the complete .bbappend file content.
