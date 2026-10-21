software = {
    version = "1.0.0";
    description = "Minimal three-image update for embedded Linux device";
    hardware-compatibility = [ "1.0" ];

    stable = {
        single = {
            images: (
                {
                    filename = "u-boot.imx";
                    device = "/dev/mmcblk0boot0";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000001";
                },
                {
                    filename = "Image";
                    device = "/dev/mmcblk0p1";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000002";
                },
                {
                    filename = "rootfs.ext4";
                    device = "/dev/mmcblk0p2";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000003";
                }
            );
        };
    };
};
