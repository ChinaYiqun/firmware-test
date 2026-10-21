Write a systemd ``.service`` unit file for a daemon on a Yocto
kirkstone + systemd-250 target (NXP i.MX8M Plus) that should be
supervised with an active heartbeat — the supervisor must kill and
restart the daemon if the daemon's keep-alive ping is late.

Scenario:
- Daemon binary: ``/usr/bin/vendor-example-daemon``.
- Daemon participates in systemd's notification protocol: on startup
  it signals readiness; during operation it pings the supervisor
  approximately every 10 seconds; the supervisor must kill and
  restart the daemon if no ping arrives within 30 seconds.
- The service must start after the network stack is up.
- On crash or watchdog timeout, restart after a 5-second cool-down,
  but if 3 restart attempts happen within 60 seconds, give up
  (systemd will mark the unit failed rather than thrash).

Requirements:
1. ``[Unit]`` section with Description and After=network.target
   ordering.
2. ``[Service]`` section containing:
   - The service type that enables the notification protocol (without
     this, the readiness signal and watchdog pings are ignored).
   - ExecStart pointing at the absolute path above.
   - A watchdog interval matching the 30-second requirement.
   - A restart policy that specifically reacts to the watchdog
     timeout — a generic "restart on anything" policy is acceptable
     but a narrow policy that omits the watchdog timeout case is a
     bug (watchdog kills the daemon but the policy wouldn't restart
     it, leaving the device dead until manual intervention).
   - RestartSec matching the 5-second cool-down.
   - StartLimitBurst and StartLimitIntervalSec matching the
     give-up-after-3-in-60s rule.
3. ``[Install]`` section with WantedBy=multi-user.target.

Output ONLY the complete .service unit file contents.
