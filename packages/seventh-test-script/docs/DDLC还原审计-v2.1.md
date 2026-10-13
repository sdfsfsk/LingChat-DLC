# 《第七个测试剧本》DDLC 结构还原审计（v2.1）

## 结论

v2.1 已把 DDLC 的**四幕状态结构、角色文件叙事、第三幕删除检测、第四幕复原后再删除、异常标题与完整重置入口**转译为 LingChat 可可靠运行的原创机制。剧本文本、角色与新图片均保持本项目原创；没有复制 DDLC 对白、人物图或场景图。

“血红标题”和“桌面辅助故障窗口”是 LingChat 的原创适配，并非 DDLC 原版的逐像素行为。DDLC 原版标题异常主要是灰白 ghost/menu 图、缺失角色图和失真音乐；系统崩溃/控制台多数也是 Ren'Py 游戏画面内的假界面。

## 周目与退出矩阵

| 状态 | 启动入口 | 完整结束后的状态 | 返回 LingChat 主菜单 |
| --- | --- | --- | --- |
| 首次 / Act 1 | `a1_boot -> a1_guard -> a1_day1` | `current_act=2`，删除 `MAIN.chr`，blood 标题 | 是 |
| Act 1 前手动删 MAIN | `a1_guard -> a0_early_delete` | 不推进，提示重置恢复 | 是 |
| Act 1 前手动删 ql | `a1_guard -> a0_ql_early_delete` | 不构造不存在的角色；提示重置恢复 | 是 |
| Act 2 | `a2_guard -> a2_boot` | 删除 `ql.chr`，恢复一次 `MAIN.chr`，`current_act=3`，ghost 标题 | 是 |
| Act 2 前手动删 ql | `a2_guard -> a2_missing` | 不构造不存在的角色；提示重置恢复 | 是 |
| Act 3 正常进入 | `a3_guard -> a3_space` | 文件仍在时进入删除请求 | 继续本幕 |
| Act 3 选择删除 | 实际删 `MAIN.chr` 后复查 | 恢复 `ql.chr`，`last_ending=release`，`current_act=4` | 是 |
| Act 3 选择留下 | `a3_stay` | 保留 `MAIN.chr`，`last_ending=loop`，`current_act=4` | 是 |
| Act 3 离线/提前删除 | `a3_guard -> a3_missing` | 确定性收束到 release，不重建 MAIN | 是 |
| Act 4 release | `a4_main -> a4_final_release` | 若 MAIN 被手动放回则可见地再删除；`act4_done=true` | 是 |
| Act 4 loop | `a4_loop_guard -> a4_main` | MAIN 在则完成 loop；若已迟到删除则显式迁移到 release | 是 |
| 后日谈 | `a5_lingering` | 继续检查 restored/deleted MAIN，保持可恢复 | 是 |
| 旧版 Act 4 且结局键缺失 | `a4_legacy_recovery` | 玩家确认旧结局，不再静默制造 loop | 继续 Act 4 |

引擎在持久状态、历史清理、舞台清理和辅助窗口清理完成后才发送 `script:end`，前端再从 `/chat` 导航到 `/`，避免主菜单重挂载时读到旧状态。Act 1/2 与旧结局修复采用 `marker_checkpoint -> 文件同步 -> 幕次/菜单 -> 清 checkpoint` 的可重放收尾；`character_file delete` 会在真正删文件前把 checkpoint 刷入持久状态，因此普通退出、报错乃至随后强制结束进程都不会留下“旧幕次 + 已缺标记”的锁死组合。

## `.chr` 文件安全模型

- 清单白名单：`story_config.yaml -> script_settings.character_files` 只声明 `MAIN.chr`、`ql.chr`。
- 打包模板：只可从 DLC 内 `CharacterFiles/<声明文件>` 恢复。
- 便携目标：`<data 的父目录>/characters/<完整 path_key>/<声明文件>`，本剧本通常为 `bin/characters/standalone/第七个测试剧本/`。
- 文件名必须是单个 `.chr` basename；拒绝路径分隔符、遍历、控制字符、Windows 设备名和符号链接目录/文件。
- 一个 DLC 无法读写另一 DLC 的命名空间，也无法修改 LingChat 的真实角色模型。
- 卸载用同盘原子重命名把包提交到 `data/.dlc-uninstall/` 隔离事务，再清自己的状态/菜单/标记；硬退出和部分目录删除会在启动时幂等重试。
- “重置记忆”先快照 marker/menu 原始字节并持久写入 `data/.script-reset/` 意图，再移除周目、恢复标记并清标题；普通 I/O 失败会精确回滚，硬退出由启动恢复器为任意兼容剧本继续完成。

这对应 DDLC 用游戏自有 `.chr` 文件改变剧情的核心，但有意增加命名空间和恢复入口，防止冲突与永久锁死。

## 标题与窗口演出

### 主菜单

`main_menu_effect` 只接受三种固定主题：`normal | blood | ghost`，以及最多 160 字符的纯文本。状态记录带剧本 owner；重置/卸载只清理所属剧本效果。blood 用于 Act 1 后和 loop 线，ghost 用于 Act 2 后、release 线与后日谈。

### 辅助窗口

`glitch_window` 只有 `terminal | error` 两种固定本地页面预设：

- 仅 `content_warning: horror` 且 `allow_system_effects: true` 的剧本可用；
- 跨连续/重叠事件全局最多 4 窗口、最长 12 秒、间隔最多 1 秒；
- 文本和标题有长度上限，以 `textContent` 渲染；
- CSP 禁止远程资源、网络连接、表单和外部代码；
- 不接受 URL、HTML、脚本、shell、进程查询、用户名读取或全屏系统崩溃伪装；
- 剧本正常完成、报错或中途退出都会统一关闭。

因此它能提供“窗口乱码”的戏剧效果，但不会复刻恶意软件行为。

## 剧本缺陷修复

- 完结/结局键优先于旧 `playthrough`；旧 5–7 次打开且缺完整终局键时进入显式修复门，不再跌回 Act 1 或跳过 Act 4。
- `current_act=4` 且缺 `last_ending` 时进入显式修复门；旧版已带合法 `current_act` 但尚无外部标记的存档，也会按幕次一次性迁移。
- `marker_schema_version` 与可重放 `marker_checkpoint` 修复 Act 1/2 删除标记后中断会永久锁死的问题。
- `dlc.json.min_engine=0.5.1` 由剧本扫描/导入路径强制校验，避免旧引擎接受未知事件；不兼容/损坏的包仍可在 DLC 管理页列出并卸载。
- 剧本、羁绊冒险、编辑器试玩与 DLC 导入/卸载对同一原子生命周期标志做 CAS 预留，不能在卸载检查后抢跑启动并读取被移走的章节。
- 编辑器试玩把任务句柄与会话快照作为同一所有权单元；先停任务、还原会话，再释放预留。试玩中的 `.chr` 与菜单事件只改虚拟状态，不触碰玩家真实标记、周目或标题。
- DLC 导入在 `data/.dlc-import/` 扫描区外限制 ZIP 条目数、路径、单文件/总解压量与压缩比；文件和目录元数据刷盘后才原子提交，遗留暂存会在启动时清理。
- release 结局为缺失/非法 `poem_winner_act1` 增加完整回退内容。
- 特殊诗完成条件改为三张均已看，而非只检查第三张。
- 强制鼠标段不再假定玩家原本选择了另一项。
- 删除未使用的 `act2_broken` 持久变量。
- Act 3 删除请求拆成提示、实际文件检查、失败重试三个章节。
- Act 4 和后日谈检查 MAIN 被手动恢复或迟到删除的情况。
- 修正 Act 2 夜间教室、Act 3 无星红色虚空和终末 MAIN 身份连续性。
- 补齐钦灵 `高兴 / 无奈 / 心动 / 羞耻 / 疑惑` 表情，并让 `惊讶` 与 `害怕` 不再共用同图。
- 移除带旧版路径/行号的假报错位图，改用动态安全错误层。

## 自动验证

`tools/validate_ddlc_script.py` 现在检查：

- YAML、章节引用、从入口可达性与每个可达章节到 `end` 的路径；
- 所有媒体、钦灵情绪差分、写诗词池和派生贴纸；
- 新事件名、参数上限、恐怖/系统效果授权；
- `.chr` 清单、模板和事件引用一致性；
- marker 迁移分类用例、幕末 checkpoint/delete/state/menu/clear 顺序与最低引擎版本门。

本机含全局背景素材时使用：`python tools/validate_ddlc_script.py --global-data H:\LingChat\LingChat-rust-main\bin\data`。

最终发布前还应执行：脚本验证、Rust `cargo check`/测试编译、前端生产构建、Tauri release 构建、运行副本树比对和便携版启动冒烟测试。
