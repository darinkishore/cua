# Dusk native Hyprland integration

Base: trycua/cua 41c34cb0; deployment branch `darinkishore/cua:vendor`.
GitHub Actions is disabled on this fork. The Nix source input is `cua-src` in
Darin's nix-config; `den/vendor/cua.nix` owns native services and packages.

Changes:

- Preserve both old numeric and new typed/addressed Hyprland workspaces;
  missing IDs no longer turn a healthy desktop into an empty window list.
- Port input to the reviewed Hyprland main commit
  23118f9f7f24db7447069949c2df7fcd8ba380d0. The prerelease build check pins
  that commit; full runtime ABI verification remains enabled.
- Give the independent input seat keyboard focus for its click/drag.
  Without it, Ghostty receives typing and scrolling but drops button events.
  The primary seat is never activated or warped by this background route.
- Keep background pixel clicks on the independent seat. The old AT-SPI
  hit-test could trigger unrelated Ghostty widget actions instead of delivering
  a button event; real TTY-byte verification exposed this end-to-end failure.
- Allow a distributor to compile exact, tested Nix executable identities via
  CUA_HYPRLAND_QUALIFIED_NIX_EXECUTABLES. It is not a runtime bypass; unknown
  rebuilt executables still refuse. Arch package checks remain unchanged.
- CUA_HYPRLAND_DEFAULT_ENABLED is an explicit packaging option, default OFF.

## Native investigation on 2026-10-02 (not qualified)

GCC 16.2, Hyprland commit above, Ghostty 1.3.1 executable:
`/nix/store/i5zqr903i6yb642h9amwh5174n5bmfc4-ghostty-1.3.1/bin/.ghostty-wrapped`.
Two independent native Ghostty processes on two inactive workspaces received
`aB`, button press/release, wheel reports and simultaneous 1400 ms drags.
A third process received `HUMAN` through the primary virtual keyboard during
the drags. Its active-window, workspace and pointer snapshots matched.
Assertions checked the actual TTY bytes, not plugin acknowledgements.
Later fresh-window Driver/MCP tests delivered the text but dropped the first
mouse operations despite successful transport acknowledgements. Repeated or
primed tests sometimes passed. Therefore this does NOT qualify Ghostty, or any
other Nix client, for production input. The Nix qualified-executable list is
empty, and no input plugin autostart is deployed. Retaining keyboard focus and
reordering enter events did not resolve this; those lifecycle experiments
were not retained. The plugin remains an experimental build artifact.

The opt-in regression harness is `libs/cua-driver/scripts/qualify-native-ghostty.py`.
Use a disposable compositor with the plugin loaded. Launch three separate
Ghostty processes with `--gtk-single-instance=false --config-default-files=false
--gtk-titlebar=false --shell-integration=none --title="Cua NAME" -e python3
native-terminal-probe.py DIR/terminal-NAME.jsonl`, where NAME is one, two or
human. Let each map and write READY, then move one/two to inactive workspaces.
Set CUA_NATIVE_TEST=1, CUA_NATIVE_TEST_DIR=DIR and
CUA_NATIVE_TEST_COMPOSITOR_PID to its exact freshly started PID; retain the disposable
compositor's WAYLAND_DISPLAY/HYPRLAND_INSTANCE_SIGNATURE/XDG_RUNTIME_DIR,
and run the harness with hyprctl and wtype on PATH. Never aim it at a user's
working compositor. The JSON receipt records delivered bytes and identities.

Chrome 154.0.8037.92 did not bind the synthetic seat: raw input refused
client_not_bound. An accessibility button action changed the real test page
from Clicks: 0 to Clicks: 1; background text was refused. This is explicitly
not universal Chrome/Electron background input support. Same-client conflicts,
unknown clients and foreground fallbacks have not been weakened.
