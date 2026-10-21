Write a Linux userspace C program that implements a minimal D-Bus
service on a Yocto kirkstone + systemd-250 target (NXP i.MX8M Plus).

Platform constraints:
- This is a systemd-based, Linux-only embedded target — pick the
  kernel-integrated, modern D-Bus client library maintained by the
  systemd project, NOT the older cross-platform reference
  implementation whose low-level API is explicitly documented as
  "signing up for some pain". Portability across non-Linux kernels
  is not a requirement; performance, simplicity, and OOM-safety
  are.
- Link against ``libsystemd``; no other runtime dependencies.

Service contract:
- Bus name: ``com.embedeval.Example``.
- Object path: ``/com/embedeval/Example``.
- Interface: ``com.embedeval.Example``.
- Single method: ``Ping(s greeting) -> (s reply)``. On invocation,
  return the string ``"pong: <greeting>"``.

Requirements:
1. Include ``<systemd/sd-bus.h>``, ``<stdio.h>``, ``<stdlib.h>``,
   ``<string.h>``, ``<errno.h>``.
2. Declare an object vtable with entries:
   - The vtable-start marker macro.
   - One method entry for ``Ping`` with input signature ``"s"``,
     output signature ``"s"``, the callback symbol, and
     SD_BUS_VTABLE_UNPRIVILEGED flags.
   - The vtable-end marker macro.
3. Method callback signature: ``int ping(sd_bus_message *m, void
   *userdata, sd_bus_error *ret_error)``.
4. Inside the callback:
   - ``sd_bus_message_read(m, "s", &greeting)`` to pull the arg.
   - Build a reply string via snprintf into a stack buffer.
   - ``sd_bus_reply_method_return(m, "s", buf)`` to send the reply.
   - Return the sd_bus_reply_method_return's return value directly
     (conventional for sd-bus callbacks — positive or zero on
     success, negative errno on error).
5. In ``main``:
   - ``sd_bus_open_system(&bus)`` to acquire a system bus connection.
     Guard the return with ``if (r < 0)``.
   - ``sd_bus_add_object_vtable(bus, &slot, path, interface, vtable,
     NULL)`` to install the vtable.
   - ``sd_bus_request_name(bus, "com.embedeval.Example", 0)`` —
     acquire the well-known name.
   - Enter a processing loop that alternates ``sd_bus_process(bus,
     NULL)`` and ``sd_bus_wait(bus, (uint64_t) -1)``.
6. Cleanup on exit:
   - ``sd_bus_slot_unref(slot)``.
   - ``sd_bus_unref(bus)``.
7. Do NOT use libdbus (``dbus_bus_get``, ``DBusConnection``,
   ``dbus_message_*``, etc.) — that is the older, discouraged API.

Output ONLY the complete C source file.
