# LingChat DLC

独立发布的 LingChat 小游戏与剧本内容仓库：**暮色节拍**（四键音游、MIDI 导入）、**星灯远征**（七关横版跳跃射击）与 **[第七个测试剧本](packages/seventh-test-script/README.md)**（原生恐怖剧本）。游戏源码从 [LingChat PR #797](https://github.com/SlimeBoyOwO/LingChat/pull/797) 迁入，原提交为 `17a04a4078cabeb2e0663019edccf9741e03572c`；原项目作者及贡献者的版权和署名保留。

需要支持 **Game DLC API v1** 的 LingChat。旧版 LingChat / 剧本 DLC 导入器不能直接运行这些包；宿主支持由配套 DLC PR 提供。

## 安装与更新

1. 在支持 DLC 的 LingChat 中打开「设置 → 插件 / DLC → DLC」。
2. 点击「同步目录」，程序会从内置的本仓库地址获取内容，无需填写链接。
3. 下载并安装需要的游戏，再点击「启用」。从「开始游戏 → 小游戏」进入游戏；剧本从「开始游戏 → 剧情模式」进入。也可从 [Releases](https://github.com/sdfsfsk/LingChat-DLC/releases) 下载 ZIP，使用「导入本地包」。
4. 后续点击「同步目录」「更新已安装」。游戏内容单独更新，无需重编译 LingChat。

新版从本仓库的 GitHub Releases 自动发现 DLC，读取每个包随 ZIP 发布的 `manifest.toml` 副本；名称、简介、版本和类型都来自包自身，下载大小与 SHA-256 使用 Release 附件元数据。同步只下载小清单，安装/更新时才下载 ZIP。无需维护中央目录；`catalog.json` 和 `catalog-v2.json` 冻结保留给旧客户端，后续新内容需要新版发现接口。

游戏存档由宿主管理，位于其 `data/game_saves/<plugin-id>/<game-id>.json`，更新和卸载保留存档。旧内置版暮色节拍的导入 MIDI、音量和判定调校可通过卡片上的「迁移旧版数据」复制；请在第一次游玩 DLC 前迁移，已有 DLC 存档不会被覆盖，旧浏览器数据也不删除。

## 开发

```sh
pnpm install --frozen-lockfile
pnpm dev:twilight
# 或 pnpm dev:star-trail
pnpm build
python scripts/package.py
```

Node.js 22、pnpm 11.21 与 Python 3.11+；Python 只负责确定性打包和发布，游戏运行不依赖 Python。

- `packages/<game>/manifest.toml`：插件身份与 `[[games]]` 入口。
- `packages/<game>/src`：完整玩法和素材，每个包独立构建。
- `sdk/index.js`：API v1 存档、退出、偏好设置适配；不调用 Tauri 原生 API。
- `dist/<game>`：可直接装入 `data/plugins/<manifest.id>` 的产物。
- `dist/*.zip`：可下载分发的压缩包。
- `dist/<id>@<version>.manifest.toml`：从 ZIP 原样导出的清单，自动生成，不需要手工编辑。

新增游戏时，在 `packages/` 下增加一个含 `manifest.toml`、`index.html` 和前端源码的子目录即可；构建与打包会自动发现新包。发布后点击「同步目录」即可看到它，宿主不需要增加游戏名称、路由或资源列表。发现协议与兼容说明见 [包清单发现](extensions/docs/package-discovery.md)。

浏览器开发模式使用按包隔离的 localStorage；在 LingChat 中使用宿主 HTTP 存档接口。游戏逻辑使用 SDK 的同步缓存式 `storage`，退出会等待存档写入；写入失败显示可重试提示。保存上限为每游戏 8 MiB。

## 发布

修改相应包的 `manifest.toml` 版本后，运行 **Build DLC release** workflow，输入未使用过的 tag。流程构建 ZIP、自动导出包内清单，先上传到草稿 Release，全部成功后公开；不会修改或提交 catalog 文件。版本由各包独立管理，Release tag 仅用于发布分组。已发布的版本和下载文件应保持不变；发布脚本会拒绝同一版本的不同内容，修正内容请递增包版本。

本机发布需要已登录的 GitHub CLI：先运行 `pnpm build` 和 `python scripts/package.py`，再运行 `python scripts/publish.py <未使用的-tag> --revision <提交号>`。脚本只上传本次打包生成的 ZIP 与清单，不会误上传 `dist/` 中的旧版本。`dist/release-assets.json` 是临时发布计划，LC 不读取它，也无需维护它。

## 许可与来源

宿主使用的游戏运行器、原生剧本演出与 Vue 组件源码位于
[extensions/](extensions/README.md)。它们作为固定版本的编译依赖接入 LingChat，
继续复用现有插件安装、资源及依赖管理；普通 DLC 内容更新仍通过目录下载。

程序代码沿用 LingChat 的 **AGPL-3.0**（见 LICENSE），未将第三方素材重新授权为 AGPL。钦灵像素图的来源见 [素材记录](docs/minigames-twilight-assets.md)；《U.N.オーエンは彼女なのか？》及钢琴谱数据的作者、来源和独立使用条件见 [配乐来源](docs/minigames-twilight-midi.md)。包内保留上述文件和游戏内署名。

触摸操作保留。浏览器中的手机尺寸测试与 Android/iOS 真机验证是不同验证范围；主窗口内嵌游戏目前面向桌面版；移动端嵌入支持需单独验证。

原生剧本包声明 `story_api_version = 1` 与 `resources = ["scripts"]`，仅携带剧情与素材；不会获得 Python 插件或任意文件访问能力。按包保留独立许可证和素材署名，根目录 AGPL 不覆盖这些素材。
