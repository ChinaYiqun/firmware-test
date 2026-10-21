[Unit]
Description=Vendor log cleanup timer

[Timer]
OnBootSec=15min
OnUnitActiveSec=7d
Persistent=true
Unit=vendor-cleanup.service

[Install]
WantedBy=timers.target

# === vendor-cleanup.service ===

[Unit]
Description=Vendor log cleanup (one-shot)

[Service]
Type=oneshot
ExecStart=/usr/bin/vendor-cleanup.sh
