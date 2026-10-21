Write a Yocto 4.0 (kirkstone) ``.bbappend`` file for the
``linux-imx`` kernel recipe that adds a kernel config fragment
to enable debugfs and dynamic-debug without editing the base
defconfig.

Context:
- The .bbappend extends ``linux-imx_%.bbappend`` (version-wildcard,
  so the fragment applies to all linux-imx versions the layer covers).
- The kernel config fragment lives at ``files/debug.cfg`` in this
  layer.
- The contents of the fragment turn on CONFIG_DEBUG_FS=y and
  CONFIG_DYNAMIC_DEBUG=y — but writing that fragment's content is
  out of scope; only the .bbappend is being authored here.
- The standard mechanism on kirkstone is to add the .cfg to SRC_URI
  — linux-yocto.bbclass / kernel-yocto picks it up automatically as
  a config fragment.

Requirements:
1. Prepend FILESEXTRAPATHS with ``${THISDIR}/files`` using the
   kirkstone colon-form override (``:prepend``) so the .cfg file
   is discoverable.
2. Append the fragment to SRC_URI via the colon-form override
   (``:append``). The fragment URI is ``file://debug.cfg``.
3. Do NOT inherit ``module`` or any other class — this is a kernel
   config extension, not a module recipe.
4. Do NOT write do_compile / do_install — the kernel recipe handles
   those.

Output ONLY the complete .bbappend file content.
