software = {
    version = "2.0.0";
    description = "Dual-bank A/B update with bootcnt failback";
    hardware-compatibility = [ "1.0", "1.2" ];

    stable = {
        copy-1 = {
            images: (
                {
                    filename = "u-boot.imx";
                    device = "/dev/mmcblk0boot0";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000001";
                },
                {
                    filename = "Image.a";
                    device = "/dev/mmcblk0p2";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000002";
                },
                {
                    filename = "rootfs.a.ext4";
                    device = "/dev/mmcblk0p3";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000003";
                }
            );
        };

        copy-2 = {
            images: (
                {
                    filename = "u-boot.imx";
                    device = "/dev/mmcblk0boot1";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000001";
                },
                {
                    filename = "Image.b";
                    device = "/dev/mmcblk0p4";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000004";
                },
                {
                    filename = "rootfs.b.ext4";
                    device = "/dev/mmcblk0p5";
                    sha256 = "0000000000000000000000000000000000000000000000000000000000000005";
                }
            );
        };
    };

    bootenv: (
        {
            name = "bootcount_enable";
            value = "1";
        },
        {
            name = "upgrade_available";
            value = "1";
        }
    );
};
