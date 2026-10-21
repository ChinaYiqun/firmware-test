SUBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="1d6b", ATTRS{idProduct}=="0002", TAG+="systemd", ENV{SYSTEMD_WANTS}="vendor-example-daemon.service"
