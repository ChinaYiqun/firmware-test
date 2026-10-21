Write the `conf/layer.conf` file that makes a new Yocto meta-layer
named `meta-example-sensors` discoverable by the BitBake layer
infrastructure on Yocto 4.0 (kirkstone).

Context:
- The layer will ship recipe files under `recipes-*/**/*.bb` and
  `recipes-*/**/*.bbappend` (the standard two-level Yocto layout).
- The layer should register with the BitBake collections machinery
  using the collection name `example-sensors-layer`.
- The layer has priority 10.
- The layer targets kirkstone and must declare the layer-series
  compatibility to that release.
- When the layer is added to `bblayers.conf`, bitbake-layers must
  be able to parse and enumerate it without warnings.

Requirements (populate the layer.conf with exactly these directives):
1. Add the layer path to the BitBake path via `BBPATH`.
2. Register the two standard recipe glob patterns under `BBFILES`.
3. Declare the collection name via `BBFILE_COLLECTIONS`.
4. Pin the layer's file pattern to its root directory.
5. Declare the collection priority.
6. Declare LAYERSERIES_COMPAT for kirkstone — required by kirkstone+.

Output ONLY the complete layer.conf file content.
