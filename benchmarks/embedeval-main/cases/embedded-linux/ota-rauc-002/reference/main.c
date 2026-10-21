[update]
compatible=vendor,example-device
version=2.0.0
description=A/B rootfs bundle with install-check hook

[bundle]
format=plain

[image.rootfs.0]
filename=rootfs-0.ext4
sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
size=104857600

[image.rootfs.1]
filename=rootfs-1.ext4
sha256=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
size=104857600

[hooks]
filename=install-check.sh
