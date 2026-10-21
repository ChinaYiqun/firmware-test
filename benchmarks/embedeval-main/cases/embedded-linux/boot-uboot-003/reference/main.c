default linux
timeout 10

label linux
    kernel /boot/Image
    fdt /boot/imx8mp.dtb
    initrd /boot/initramfs.cpio.gz
    append root=/dev/mmcblk1p2 rootwait console=ttymxc1,115200
