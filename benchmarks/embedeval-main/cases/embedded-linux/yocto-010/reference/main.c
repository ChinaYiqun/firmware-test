FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI:append = " file://sshd_config_harden"

RDEPENDS:${PN}:append = " audit"

do_install:append() {
    install -d ${D}${sysconfdir}/ssh/sshd_config.d
    install -m 0644 ${WORKDIR}/sshd_config_harden \
        ${D}${sysconfdir}/ssh/sshd_config.d/50-harden.conf
}
