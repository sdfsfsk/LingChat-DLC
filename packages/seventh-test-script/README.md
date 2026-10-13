# 第七个测试剧本

四幕、45 章的恐怖剧本 DLC，完整保留 v2.13.0 的剧情、写诗小游戏、真实系统窗口、受限鼠标牵引和 .chr 文件互动。

## 安装与游玩

需要支持 `story_api_version = 1` 的 LingChat 构建（[统一 DLC PR #884](https://github.com/SlimeBoyOwO/LingChat/pull/884)）。旧 PR #677 已迁入该引擎方案。

1. 设置 → 插件 / DLC → DLC → 同步目录。
2. 下载《第七个测试剧本》，然后启用。
3. 开始游戏 → 剧情模式 → 第七个测试剧本；阅读并确认内容警告后进入。

也可以从本仓库 Releases 下载 `seventh-test-script-2.14.0.zip`，在同一 DLC 页导入。
保留游戏自带的 DeepSeek 角色（`data/game_data/characters/DeepSeek/settings.yml`）；剧本进入时绑定此主角，退出后恢复原角色。
旧版手动安装的同名剧本优先于插件版：请先备份旧目录，再把它移出 `data/game_data/scripts/`，旧存档不要删除。

## 内容提示与存档

建议 16 岁以上；包含突脸、画面闪烁、心理恐怖和血色 UI。确认后会出现受限原生窗口；鼠标牵引只在主窗口聚焦时短暂生效，Esc、失焦或 5 秒后停止，不会自动点击。
原生演出仍在剧情流程中运行，普通小游戏则在主窗口内游玩。

无害的 .chr 标记位于 `data` 旁边的 `characters/plugins/seventh-test-script/seventh-test-script/`，与真实角色文件隔离。
升级和卸载保留周目状态与标记；需要重新开始时，在剧情列表点击“重置记忆”。两种终局留下的 SCRIPT_CORRUPTED 状态也可这样重置。
剧本运行期间不能更新或卸载 DLC，请先退出剧本。

v2.14.0 仅迁移安装格式、目录和署名文档，45 个章节与 v2.13.0 内容一致。

## 素材与版权

- **twilight**：作者 / 作曲 **the_last_summer**，专辑 **LingChat OST**（据音轨内嵌信息），由维护者提供的本项目委托配乐，以 [CC BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/) 授权（署名-禁止演绎），不适用下述剧本文本的 BY-NC 许可。音频保留原文件、按原速播放；曲名及原包中冲突的许可标注已按维护者转达的作者信息修正。署名、完整许可与接入说明见 [`Twilight-credits`](scripts/seventh-test-script/Assets/Musics/Twilight-credits/SOURCE.md)。

- **剧本文本、剧情、崩坏背景/立绘等生成素材**：本仓库原创内容，以 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) 授权（署名-非商业性使用）。
- **DDLC 素材**（`Assets/` 中的 `1/2/6/g1/ghostmenu/heartbeat/d.ogg` 及 `glitch1-3 / mscare / eyes / giggle / s_kill_glitch1.ogg`）来自免费游戏《Doki Doki Literature Club》，版权属 **Team Salvato** 所有，依其 [IP Guidelines](https://teamsalvato.com/ip-guidelines/) 作非商业社区二创使用。**这些素材不在本仓库协议覆盖范围内，请勿二次分发或商用。**
- 本 DLC 为免费社区内容，与 Team Salvato 及 LingChat 官方无隶属关系。


原仓库最后提交：`38a37962b495282a55a948bf367660e89387ce81`。本包许可证优先于仓库根目录许可证；不同来源素材继续适用各自原许可。
