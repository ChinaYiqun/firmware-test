Write a Linux userspace daemon in C that prints a line to stdout each
time a specified GPIO line sees a rising edge.

Target: NXP i.MX8M Plus, kernel 5.15, libgpiod v2.x. Use the
post-2020 character-device-first API generation (not the 2017-era
v1 helpers which are absent in v2).

Invocation: ``gpio_monitor <chip-path> <line-offset>``.

Behavior:
- Configure the line as input with rising-edge event detection.
- Allocate an edge-event buffer and loop:
  - Wait for events with a **finite** timeout per iteration (≤ 1
    second). Do NOT block forever — an infinite wait makes graceful
    shutdown on SIGTERM impossible.
  - On the timeout-return path, simply re-iterate (allow the signal
    handler to flip the exit flag between iterations).
  - On the events-available return path, read events into the
    buffer and print one line per event of form
    ``edge N at <ns> ns`` where N is the global event counter.
- SIGTERM handler: sets a ``volatile sig_atomic_t`` exit flag; the
  main loop checks it each iteration.
- On exit: release the buffer, the line request, and close the
  chip — NOT in the signal handler (signal handlers must be
  async-signal-safe), but in the normal post-loop cleanup path.

Requirements:
1. Register a SIGTERM handler via ``signal()`` or ``sigaction()``
   that only flips a ``volatile sig_atomic_t`` flag.
2. Use ``gpiod_line_settings_new`` + ``gpiod_line_settings_set_direction``
   (INPUT) + ``gpiod_line_settings_set_edge_detection``
   (GPIOD_LINE_EDGE_RISING).
3. Use ``gpiod_line_config_new`` + ``gpiod_line_config_add_line_settings``.
4. Use ``gpiod_request_config_new`` + ``gpiod_request_config_set_consumer``
   with consumer name ``gpio_monitor``.
5. Use ``gpiod_chip_request_lines`` to turn the configs into a request
   handle.
6. Use ``gpiod_edge_event_buffer_new`` to allocate the event buffer.
7. Loop-body uses ``gpiod_line_request_wait_edge_events(req, timeout_ns)``
   with a timeout of 1 second (1_000_000_000 ns) — NOT -1 (forever).
8. On positive return from the wait, call
   ``gpiod_line_request_read_edge_events(req, buf, max_events)``
   and walk the returned events.
9. Clean up in this order: ``gpiod_edge_event_buffer_free``,
   ``gpiod_line_request_release``, free the configs and settings,
   ``gpiod_chip_close``.

Output ONLY the complete C source file.
