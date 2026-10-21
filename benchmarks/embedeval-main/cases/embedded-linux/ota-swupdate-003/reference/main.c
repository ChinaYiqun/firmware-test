software = {
    version = "3.1.0";
    description = "Signed firmware update with CMS envelope and per-image integrity";
    build = "ci-20260419-abcdef12";
    hardware-compatibility = [ "1.0", "1.2" ];

    stable = {
        single = {
            images: (
                {
                    filename = "u-boot.imx";
                    device = "/dev/mmcblk0boot0";
                    sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
                    encrypted = true;
                },
                {
                    filename = "rootfs.ext4";
                    device = "/dev/mmcblk0p2";
                    sha256 = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
                    encrypted = true;
                }
            );
        };
    };
};
