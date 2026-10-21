Write a single-line udev rule (with allowed line continuations via
backslash) that detects when a specific USB device is plugged in
and, as a reaction, restarts a named systemd service.

Scenario:
- Target device: USB device with vendor ID ``0x1d6b`` (Linux
  Foundation, a public ID) and product ID ``0x0002`` (USB 2.0 root
  hub).
- On plug-in, restart the systemd service
  ``vendor-example-daemon.service``.
- Rule should run under the ``systemd`` tagging model (so systemctl
  interaction is handled by systemd itself rather than by spawning
  a plain shell command).

Requirements:
1. Match the subsystem ``usb``.
2. Match the action ``add``.
3. Match the USB vendor ID attribute.
4. Match the USB product ID attribute.
5. Tag the device with ``systemd`` so udev hands off to systemd's
   device integration.
6. Use an ENV assignment that asks systemd to start / wants the
   target service. The environment variable that couples a udev
   device to a systemd unit is the one whose name literally says the
   device "wants" the unit.

Operator discipline:
- ``==`` means match; ``=`` means plain assign; ``+=`` means
  append-assign.
- The match keys (SUBSYSTEM, ACTION, ATTRS) must use ``==``. Writing
  ``SUBSYSTEM="usb"`` is an assignment to a read-only key — udev
  rejects or silently fails to filter.
- The assign keys (TAG, ENV) typically use ``+=`` (for TAG, so it
  coexists with other tags) and ``=`` (for ENV).

Output ONLY the udev rule content — one rule, which may be written
across multiple lines with backslash continuation.
