Write a Yocto 4.0 (kirkstone) BitBake recipe for a hypothetical
package ``netapp`` (version 1.0) that exposes two feature flags via
``PACKAGECONFIG``: ``ssl`` and ``examples``.

Context:
- ``ssl`` enables OpenSSL-backed TLS. Autoconf flag is
  ``--with-ssl``, build-time dep is ``openssl``, runtime dep is
  ``openssl-bin``.
- ``examples`` installs example applications. Autoconf flag is
  ``--enable-examples`` (disable: ``--disable-examples``), no DEPENDS
  change, no runtime deps.
- ``ssl`` is enabled by default; ``examples`` is disabled by default.
- The recipe uses autotools (inherits ``autotools``) and should pass
  ``${PACKAGECONFIG_CONFARGS}`` into EXTRA_OECONF so the feature
  toggles actually reach configure.

Requirements:
1. Standard recipe preamble: SUMMARY, DESCRIPTION, LICENSE (MIT),
   LIC_FILES_CHKSUM (dummy value ``file://COPYING;md5=aabbccddeeff``),
   and SRC_URI ``file://netapp-1.0.tar.gz``.
2. inherit autotools.
3. PACKAGECONFIG default: ``ssl`` enabled, ``examples`` disabled.
4. PACKAGECONFIG entry for ``ssl`` — 5-field tuple: ``<enable>``,
   ``<disable>``, ``<DEPENDS>``, ``<RDEPENDS>``, ``<RCONFLICTS>``
   (leave RCONFLICTS empty).
5. PACKAGECONFIG entry for ``examples`` — 5-field tuple with the
   autoconf toggle; all dep/rdep/rconflicts fields empty.
6. EXTRA_OECONF must include ``${PACKAGECONFIG_CONFARGS}`` so the
   flags propagate to the configure step.

Output ONLY the complete .bb file content.
