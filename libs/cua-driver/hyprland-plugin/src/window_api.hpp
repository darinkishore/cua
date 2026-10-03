#pragma once

namespace cua::hyprland {
// Hyprland main moved window lifecycle and identity behind public APIs.
// Keep the older input candidate buildable without accessing private fields.
template <typename Window> bool window_mapped(const Window& window) {
    if constexpr (requires { window.mapped(); }) return window.mapped();
    else return window.m_isMapped;
}
template <typename Window> bool window_x11(const Window& window) {
    if constexpr (requires { window.backend().isX11(); }) return window.backend().isX11();
    else return window.m_isX11;
}
template <typename Window> auto window_pid(Window& window) {
    if constexpr (requires { window.backend().pid(); }) return window.backend().pid();
    else return window.getPID();
}
template <typename Input> bool exclusive_layer(const Input& input) {
    if constexpr (requires { input.m_exclusiveKeyboardLSes; }) return !input.m_exclusiveKeyboardLSes.empty();
    else return !input.m_exclusiveLSes.empty();
}
} // namespace cua::hyprland
