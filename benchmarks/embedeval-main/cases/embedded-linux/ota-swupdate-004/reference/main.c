software = {
    version = "4.0.0";
    description = "Update with pre-install and post-install lifecycle handlers";
    hardware-compatibility = [ "1.0" ];

    stable = {
        single = {
            images: (
                {
                    filename = "rootfs.ext4";
                    device = "/dev/mmcblk0p2";
                    sha256 = "1111111111111111111111111111111111111111111111111111111111111111";
                }
            );
        };
    };

    scripts: (
        {
            filename = "pre-install.sh";
            type = "preinstall";
            sha256 = "2222222222222222222222222222222222222222222222222222222222222222";
        },
        {
            filename = "post-install.lua";
            type = "lua";
            sha256 = "3333333333333333333333333333333333333333333333333333333333333333";
        }
    );
};
