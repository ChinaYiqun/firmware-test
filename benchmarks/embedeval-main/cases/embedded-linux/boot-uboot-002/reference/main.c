/dts-v1/;

/ {
	description = "imx8mp FIT image";
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

		fdt-1 {
			description = "Device Tree blob";
			data = /incbin/("./imx8mp.dtb");
			type = "flat_dt";
			arch = "arm64";
			compression = "none";
			hash-1 {
				algo = "sha256";
			};
		};

		ramdisk-1 {
			description = "Initial RAM disk";
			data = /incbin/("./initramfs.cpio.gz");
			type = "ramdisk";
			arch = "arm64";
			os = "linux";
			compression = "gzip";
			hash-1 {
				algo = "sha256";
			};
		};
	};

	configurations {
		default = "config-1";

		config-1 {
			description = "Kernel + FDT + ramdisk";
			kernel = "kernel-1";
			fdt = "fdt-1";
			ramdisk = "ramdisk-1";
		};
	};
};
