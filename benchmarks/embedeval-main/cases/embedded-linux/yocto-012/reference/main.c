SUMMARY = "Networked app demonstrating PACKAGECONFIG"
DESCRIPTION = "Example package with ssl and examples feature flags"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING;md5=aabbccddeeff"

SRC_URI = "file://netapp-1.0.tar.gz"

S = "${WORKDIR}/netapp-1.0"

inherit autotools

PACKAGECONFIG ??= "ssl"

PACKAGECONFIG[ssl] = "--with-ssl,--without-ssl,openssl,openssl-bin,"
PACKAGECONFIG[examples] = "--enable-examples,--disable-examples,,,"

EXTRA_OECONF += "${PACKAGECONFIG_CONFARGS}"
