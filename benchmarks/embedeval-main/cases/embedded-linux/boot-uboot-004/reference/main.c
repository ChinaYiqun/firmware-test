/dts-v1/;

/ {
	description = "Signed FIT image for imx8mp verified boot";
	#address-cells = <1>;

	images {
		kernel-1 {
			description = "Linux kernel";
			data = /incbin/("./Image");
			type = "kernel";
			arch = "arm64";
			os = "linux";
			compression = "none";
			load = <0x40480000>;
			entry = <0x40480000>;
			hash-1 {
				algo = "sha256";
			};
		};
	};

	configurations {
		default = "config-1";

		config-1 {
			description = "Signed kernel configuration";
			kernel = "kernel-1";

			signature-1 {
				algo = "sha256,rsa4096";
				key-name-hint = "boot-key";
				sign-images = "kernel";
			};
		};
	};
};
