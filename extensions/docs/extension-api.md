# DLC 扩展接口（SDK 0.3）

内容复用 LC 插件的安装、启停和资源管理。主程序负责通用引擎与权限边界，具体演出由本仓库实现。

| 扩展内容 | 本仓库入口 | 宿主职责 |
| --- | --- | --- |
| 演出事件 | `frontend/src/core/events/index.ts` | 注册处理器，保留既有 FIFO 顺序与取消信号 |
| IPC 事件 | `frontend/src/host/listeners.ts` | 提供统一载荷转换器 |
| 菜单与路由 | `frontend/src/host/menu.ts`、`routes.ts` | 渲染注册项，沿用 LC 菜单布局 |
| 界面插槽 | `frontend/src/host/*Overlay.vue` | 提供展示位置、角色和尺寸 |
| 显示策略与生命周期 | `frontend/src/host/policy.ts`、`lifecycle.ts`、`finish.ts` | 在进入/退出等时机调用 |
| 类型与状态 | `frontend/src/types/story.ts`、`host/gameState.ts` | 组合扩展事件联合类型与状态 |
| 本地化 | `frontend/src/locales/index.ts` | 合并后统一播种与加载用户翻译 |
| 静态辅助页面 | `frontend/build.mjs` | 调用 Vite 插件，开发和生产使用相同资源 |
| 原生命令 | `rust/runtime/src/commands.rs` | 先执行窗口权限检查，再分派；命令只在 SDK 声明一次 |
| 每轮互动状态 | `rust/runtime/src/story/channels.rs` | `ScriptChannels::extension_mut<T>()` 提供有类型的状态槽，结束时统一释放 |
| 兼容与角色策略 | `rust/runtime/src/story/lifecycle.rs` | 配置读取、初始化时调用 `script_engine::extension::Hooks` |
| 编辑器字段与特效名称 | `rust/runtime/src/story/schema.rs` | `configure_schema` 合并扩展定义，内置清单保持独立 |
| 既有事件的展示参数 | `rust/runtime/src/story/responses.rs` | `event_fields` 透传扩展投影；角色身份、动作仍由 LC 控制 |
| 关闭演出与桌宠提示 | `frontend/src/host/policy.ts` | 调用策略接口；宿主继续等待存档完成后退出 |
| 剧本附加操作 | `frontend/src/host/ScriptActions.vue` | 菜单预留操作插槽，重置记忆按钮及样式在 SDK 中 |
| 媒体释放与音调 | `frontend/src/host/media.ts` | 提供音频对象与释放回调，SDK 判断包归属 |

增加演出事件时，在 SDK 定义载荷类型并注册 Rust 事件、前端处理器和监听；需要原生命令时再加入 `commands!`。主仓库无需再添加具体事件枚举项、写诗通道或命令名称。增加小游戏、剧本或素材仍通过包清单与目录发布。

资源归属、运行预留、路径校验和对话存档隔离仍由宿主负责。下载内容不能自行安装 Rust/Vue 扩展：SDK 是锁定版本的编译依赖，提升原生能力需要审核并重建宿主；普通内容更新继续走插件/DLC 目录。

SDK 0.3 必须使用配套宿主接口，不是适用于所有 LC 版本的二进制 ABI。目录地址、演出策略、页面和提示词由 DLC 仓库维护，宿主只锁定依赖来源与版本。

0.3 将原先残留在宿主中的剧情台词、关闭演出延时、写诗/突脸等事件名称、内容警告字段、立绘闪现与噪点参数收回本仓库。宿主不再枚举具体剧情表情：别名照常解析，其余名称按角色自己的素材查找，缺图时回退到正常立绘。发布新的普通内容包不需要修改宿主或维护 catalog，仍从 Release 的每包清单发现。

本次删除宿主里旧独立窗口方案的 Android Activity、局域网明文策略与 iOS 多场景配置。当前内嵌游戏运行时仍仅支持桌面；没有以扩大移动端权限来模拟支持。原生剧本、`.chr` 互动、主窗口小游戏和包校验边界保持不变。
