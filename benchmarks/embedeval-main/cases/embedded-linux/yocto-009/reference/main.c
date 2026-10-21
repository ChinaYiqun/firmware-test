BBPATH .= ":${LAYERDIR}"

BBFILES += "${LAYERDIR}/recipes-*/*/*.bb \
            ${LAYERDIR}/recipes-*/*/*.bbappend"

BBFILE_COLLECTIONS += "example-sensors-layer"
BBFILE_PATTERN_example-sensors-layer = "^${LAYERDIR}/"
BBFILE_PRIORITY_example-sensors-layer = "10"

LAYERSERIES_COMPAT_example-sensors-layer = "kirkstone"
