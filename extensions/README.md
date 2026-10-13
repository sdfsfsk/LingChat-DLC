# LingChat DLC extension SDK

SDK 0.2 exposes [host integration interfaces](docs/extension-api.md) for views,
menus, event registration, typed run state, command dispatch and lifecycle policy.
Specific horror presentations, translations and helper pages stay in this repository.

These readable source packages contain the shared game runtime and native story
presentation extracted from LingChat PR #884. Game and story content stays under
`packages/` and is discovered from each published package's own manifest. Runtime
0.2.1 adds [package discovery](docs/package-discovery.md); the UI and contract remain
at 0.2.0. Central catalog files are frozen for legacy clients.

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
or story content remains an ordinary DLC download and does not require a host
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

## Story regression checks

The host must register `createStoryEventProcessors()` from `@lingchat/dlc-ui/core/events`:
its local `import.meta.glob` cannot discover processors inside this package.

Build the `audit_story` and `story_routes` examples from the matching host workspace
(`cargo build --release -p ling-chat-dlc-runtime --examples`). Run `audit_story
HOST_DATA_DIR SCRIPT_DIR` for media/schema/factory validation and `story_routes
SCRIPT_DIR` for all 45 chapters, both endings, poem routes, early marker deletion,
checkpoint replay and legacy entries. The route audit uses the host condition and
assignment functions; presentation and external effects are simulated there.

`frontend/tests/story-smoke.mjs` renders the actual LC chat components and registers
actual Tauri event listeners with mocked IPC. Set `LINGCHAT_HOST` to the host checkout;
provide Playwright through `PLAYWRIGHT_MODULE` or the host's node_modules, and optionally
`BROWSER_PATH` and `AUDIT_OUTPUT`. It checks Enter advancement, two portraits, forced
choice, 20-word submissions in three poem modes, native-window tickets, timed effects
and interruption cleanup. It does not claim to test native OS windows. Windows smoke
validation additionally exercised the real executable, DLC portrait paths, forced
choice, a complete poem, live checkpoint writes and stop cleanup in an independent
data directory without player credentials.

All moved host code retains its AGPL-3.0 license (see repository LICENSE).
