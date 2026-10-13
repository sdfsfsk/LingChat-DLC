# LingChat DLC

独立发布的 LingChat 小游戏内容仓库：**暮色节拍**（四键音游、MIDI 导入）与 **星灯远征**（七关横版跳跃射击）。游戏源码从 [LingChat PR #797](https://github.com/SlimeBoyOwO/LingChat/pull/797) 迁入，原提交为 `17a04a4078cabeb2e0663019edccf9741e03572c`；原项目作者及贡献者的版权和署名保留。

需要支持 **Game DLC API v1** 的 LingChat。旧版 LingChat / 剧本 DLC 导入器不能直接运行这些包；宿主支持由配套 DLC PR 提供。

## 安装与更新

1. 在支持 DLC 的 LingChat 中打开「游戏模式 → 小游戏 / DLC」。
2. 目录地址填入 `https://raw.githubusercontent.com/sdfsfsk/LingChat-DLC/main/catalog.json`，点击「同步目录」。
3. 下载并安装需要的游戏，再点击「启用」「开始」。也可从 [Releases](https://github.com/sdfsfsk/LingChat-DLC/releases) 下载 ZIP，使用「导入本地包」。
4. 后续点击「同步目录」「更新已安装」。游戏内容单独更新，无需重编译 LingChat。

`catalog.json` 中包含版本、下载地址、字节大小、SHA-256 与接口版本。同步仅刷新目录；安装/更新由玩家触发。先发布 Release 文件，再更新目录，避免目录指向不存在的下载。

游戏存档由宿主管理，位于其 `data/game_saves/<plugin-id>/<game-id>.json`，更新和卸载保留存档。旧内置版暮色节拍的导入 MIDI、音量和判定调校可通过卡片上的「迁移旧版数据」复制；请在第一次游玩 DLC 前迁移，已有 DLC 存档不会被覆盖，旧浏览器数据也不删除。

## 开发

```sh
pnpm install --frozen-lockfile
pnpm dev:twilight
# 或 pnpm dev:star-trail
pnpm build
python scripts/package.py
```

Node.js 22、pnpm 11.21 与 Python 3.11+；Python 只负责确定性 ZIP 和目录生成，游戏运行不依赖 Python。

- `packages/<game>/manifest.toml`：插件身份与 `[[games]]` 入口。
- `packages/<game>/src`：完整玩法和素材，每个包独立构建。
- `sdk/index.js`：API v1 存档、退出、偏好设置适配；不调用 Tauri 原生 API。
- `dist/<game>`：可直接装入 `data/plugins/<manifest.id>` 的产物。
- `dist/*.zip`：可下载分发的压缩包。

新增游戏时，在 `packages/` 下增加一个含 `manifest.toml`、`index.html` 和前端源码的子目录即可；构建与目录生成会自动发现新包。宿主不需要增加游戏名称、路由或资源列表。

浏览器开发模式使用按包隔离的 localStorage；在 LingChat 中使用宿主 HTTP 存档接口。游戏逻辑使用 SDK 的同步缓存式 `storage`，退出会等待存档写入；写入失败显示可重试提示。保存上限为每游戏 8 MiB。

## 发布

修改相应包的 `manifest.toml` 版本后，手工运行 **Build DLC release** workflow，输入未使用过的 tag。流程构建、生成 ZIP 和 SHA-256、发布 GitHub Release，成功后提交 `catalog.json` 到 main。已发布的版本和下载文件应保持不变；修正内容请发新版本。

本机发布也可设置 `DLC_REPOSITORY`、`DLC_RELEASE_TAG` 后运行打包脚本；先上传 `dist/*.zip` 到同名 Release，再推送更新后的目录。

## 许可与来源

程序代码沿用 LingChat 的 **AGPL-3.0**（见 LICENSE），未将第三方素材重新授权为 AGPL。钦灵像素图的来源见 [素材记录](docs/minigames-twilight-assets.md)；《U.N.オーエンは彼女なのか？》及钢琴谱数据的作者、来源和独立使用条件见 [配乐来源](docs/minigames-twilight-midi.md)。包内保留上述文件和游戏内署名。

触摸操作保留。浏览器中的手机尺寸测试与 Android/iOS 真机验证是不同验证范围；宿主多窗口模式要求受支持的平台版本，具体以宿主说明为准。
