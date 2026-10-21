Write a Linux userspace CLI program in C that toggles a GPIO line.

Target: NXP i.MX8M Plus running kernel 5.15 + glibc with libgpiod
v2.x. The 2017-era libgpiod v1 API is considered obsolete on this
stack; use the post-2020 character-device-first API generation.

Program invocation: ``gpio_toggle <chip-path> <line-offset> <value>``
where:
- ``<chip-path>``: absolute path like ``/dev/gpiochip0``.
- ``<line-offset>``: non-negative integer line offset on that chip.
- ``<value>``: either ``0`` or ``1``.

Requirements:
1. argv sanity: print usage and exit non-zero if argc != 4 or if
   line offset / value fail to parse as the right type and range.
2. Open the GPIO chip via the modern ``gpiod_chip_open(path)``
   entry point (this function still exists in v2, only its
   partner lookups such as ``gpiod_chip_open_by_name`` /
   ``gpiod_chip_open_by_number`` are gone).
3. Build a line request using the v2 config composition pattern:
   - allocate a line-settings object,
   - set its direction to output and its initial output value to
     the requested one,
   - allocate a line-config object and add the settings to it
     against the single requested line offset,
   - allocate a request-config object and set its consumer string
     to ``gpio_toggle``,
   - call the chip's request-lines function with the two configs.
4. On request success: release the request handle, close the chip,
   free both configs and the settings, return 0.
5. On ANY failure (open, allocate, request): print a perror-style
   error message to stderr and return a non-zero exit code; still
   release every already-allocated resource to avoid leaks.
6. Do NOT fall back to sysfs (``/sys/class/gpio/export``) — that
   interface is deprecated and may be absent on this kernel.
7. Do NOT use the v1 entry points: ``gpiod_chip_get_line``,
   ``gpiod_line_request_output``, ``gpiod_line_set_value``,
   ``gpiod_line_release``.

Output ONLY the complete C source file.
