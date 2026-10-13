# LingChat DLC extension SDK

These readable source packages contain the shared game runtime and native story
presentation extracted from LingChat PR #884. Game and story content stays under
`packages/` and continues to use the existing catalogs, manifests and downloads.

- `frontend/`: Vue components, story presentation, audio, state and typed events.
- `rust/contract/`: content manifest validation and plugin lifecycle callbacks.
- `rust/runtime/`: download verification, isolated game webviews, native story
  events, persistence, reset transactions and editor diagnostics.
- `docs/`: authoring and runtime documentation moved with the implementation.

The host still owns the plugin importer/manager, dependency resolution, resource
scanning, script execution, user consent and application command registration.
The extension reuses those facilities. Downloaded DLC cannot register arbitrary
Rust or Python code, bypass native-window tickets or access host commands from a
game webview. Saves remain outside installed packages.

## Building with the host

This SDK is compiled into LingChat; it is not downloaded executable code. The host
pins Rust packages to a Git revision and the UI tarball to a release URL plus its
lockfile integrity. Changing this SDK requires rebuilding LingChat. Updating game
or story content remains an ordinary catalog download and does not require a host
rebuild.

`@lingchat/host/*` resolves to the host's `src/` modules. The host's workspace patches
`ling-chat-main` and `ling-chat-plugins` to its own crates so there is exactly one
copy of host state. The matching host integration is required; these are source
extension interfaces, not a stable binary ABI.

For development, point the two workspace Cargo dependencies at `extensions/rust`
and the UI dependency at `extensions/frontend`. Run the host's `pnpm build`,
`pnpm check:effects`, and `cargo test --release -p ling-chat-dlc-runtime`.
Windows test binaries require the application's common-controls v6 manifest.
Published host manifests must use pinned remote dependencies, never local paths.

All moved host code retains its AGPL-3.0 license (see repository LICENSE).
