[Unit]
Description=Vendor Example Daemon (systemd-supervised)
After=network.target

[Service]
Type=notify
ExecStart=/usr/bin/vendor-example-daemon
WatchdogSec=30
Restart=on-watchdog
RestartSec=5
StartLimitBurst=3
StartLimitIntervalSec=60

[Install]
WantedBy=multi-user.target
