Write TWO systemd unit files, concatenated into a single output, that
together run a log-cleanup script periodically on a Yocto kirkstone
target.

Scenario:
- Script: ``/usr/bin/vendor-cleanup.sh`` (already exists, no need to
  write it).
- Should run 15 minutes after each boot, then every 7 days thereafter.
- If the device was powered off when a run was due, the missed run
  should execute once the device boots up (drift-free semantics).
- The script is a one-shot: it runs to completion and exits. It is
  NOT a long-lived daemon.

Output format:
- A SINGLE file containing two unit-file bodies, separated by a
  delimiter line. Use the literal delimiter ``# === vendor-cleanup.service ===``
  on its own line between the two unit bodies.
- First body: the ``.timer`` unit.
- Second body: the ``.service`` unit that the timer triggers.

Requirements for the timer body:
1. ``[Unit]`` with Description and (optional) Documentation.
2. ``[Timer]`` with:
   - An on-boot delay matching the 15-minute requirement.
   - A periodic re-fire interval matching the 7-day requirement.
   - The directive that makes systemd remember the last run across
     reboots (this is what prevents drift).
   - ``Unit=`` pointing at the paired service.
3. ``[Install]`` with WantedBy=timers.target.

Requirements for the service body:
1. ``[Unit]`` with Description.
2. ``[Service]`` with:
   - The service type appropriate for a run-to-completion script
     (definitely NOT the type used for long-lived daemons).
   - ExecStart pointing at the absolute path of the cleanup script.
3. NO ``[Install]`` section — the service is triggered by the timer,
   not enabled directly.

Output ONLY the concatenated file contents.
