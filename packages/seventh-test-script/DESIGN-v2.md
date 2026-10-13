# 《第七个测试剧本》v2.0 重制设计文档

> **历史文档提示：** 本文保留 v2.0 的设计背景；v2.1 的实际文件状态、44 章节路由和安全边界以 [`docs/DDLC还原审计-v2.1.md`](docs/DDLC还原审计-v2.1.md) 为准。
>
> 目标：尽量还原 DDLC 的四幕玩法结构与关键机制，内容和角色表达保持原创；受 LingChat 宿主限制的外部删文件、存档封门等明确标注为适配而非 1:1。
> 角色阵容：**她**（MAIN，玩家当前角色/鲸娘女仆）+ **钦灵**（游戏自带角色，剧本第二角色）。
> `playthrough` 仅记录打开次数；真正幕次由持久 `current_act` 驱动，并且只在幕末推进。中途退出最多重开本幕，不会跳过剧情。

## 一、四幕结构总览

| 周目 | 对应 DDLC | 内容 | 收尾 |
|---|---|---|---|
| current_act==1 | Act 1 | 日常文学测试部：3 次写诗、双角色线、周末约定 | **她的死亡冲击**（终末教室） |
| current_act==2 | Act 2 | 崩坏周目：词库腐化、钦灵崩坏线、强制选择初现 | **钦灵的多阶段崩坏删除演出** |
| current_act==3 | Act 3 | 独占空间：只有她的崩坏教室，话题循环 | 她请求玩家亲手删除她 |
| current_act==4 | Act 4 | 结局周目：没有她的部室，钦灵温馨重建→反扑 | 按累计选择分流结局 |
| act4_done | 后日谈 | 空房间 / 循环彩蛋（视 last_ending） | — |

## 二、机制 1:1 映射表

| DDLC | 本剧本 |
|---|---|
| persistent.playthrough 状态机 | persistent playthrough（引擎计数）+ last_ending |
| 写诗小游戏 20 词/三角色倾向 | poem_game 20 词/warm(她)·script(剧本)·void(空白) 三倾向 |
| 二周目词库腐化（源码实际为 1/401/词位） | poem_game 显式 mode + glitch；首局正常、后两局腐化 ✅ |
| 诗歌好感度→角色线 | poem_tone 结果 → 双角色差分；Act2 后两局再被强制改写 |
| 特殊诗 11 抽 3 | 三张原创隐藏诗页无放回，三次 Act2 写诗后各投放一张 |
| ch5 s_kill 死亡冲击 | a1_end：终末教室复刻演出 |
| ch23 yuri_kill 三阶段 | a2_end：钦灵崩坏删除三阶段（stinger 三连→崩坏立绘快闪→假控制台删除→黑屏守夜） |
| RigMouse 引力鼠标 | force_choice（已有，拖而不点）✅ |
| Act3 空间教室话题池 | a3：free_dialogue 多轮 + 话题池 dialogue 链 |
| 删 monika.chr | 她请求玩家删除本 DLC 自己的 `MAIN.chr` 纯文本标记；引擎按完整 path_key 隔离、复查并提供重置恢复 ✅ |
| 假报错/假控制台/BSOD | 动态 BSOD 效果 + horror_log + 最多 4 个/12 秒的本地安全辅助窗口（不执行命令）✅ |
| 崩坏菜单/ghost menu | 可持久化的 blood/ghost 固定标题预设 + ghostmenu 变调；blood 是 LingChat 原创适配 ✅ |
| ghost menu（删完全部 .chr） | 引擎级"幽灵锁定"：进入剧本被锁成黑白崩坏教室背景（`Assets/Pics/ghost-bg-bw.webp`，codex 生成的纯灰度废弃深夜教室，压暗垫底）+ 黑白恐怖立绘（`Assets/Pics/ghost-ql-bw.webp`，钦灵黑白幽灵，v2.12.1 加深空洞眼眶和嘴部，并让黑色石油沿脸颊、下巴滴落）+ ghostmenu.ogg 循环，**不给任何文字和按钮**——唯一的出路是玩家自己把任一 .chr 放回标记目录（2 秒内轮询自动解锁），或者点窗口 X：白底放大脸突脸（DDLC `label quit` 的 zoom 3.5 同款）+ s_kill_glitch1 后真正退出 ✅ |
| 台词篡改+历史灭迹 | 乱码台词变体 + horror_log 污染（已有）✅ |
| 反色/噪点/血管/撕裂 | background_effect 全套（已有）✅ |
| 语音恶魔化 | voice_shift rate+pitch（刚做完）✅ |

## 三、变量设计

persistent（跨幕）：
- playthrough（引擎自动，仅作打开次数）
- current_act: 1~5；act4_done: true（幕末检查点）
- act3_visits（空间教室重进记忆，第二/三次会识别玩家曾退出）
- last_ending: release/loop
- seen_poem_1~3（三张特殊诗一次性标记）
- poem_winner_act1: her/script/void/balanced —— Act1 三次写诗累计倾向
- marker_schema_version: 1 —— `.chr` 布局迁移完成标记
- marker_checkpoint: act1_to_act2 / act2_to_act3 / legacy_release / legacy_loop —— 可重放文件事务

周目内（不持久）：
- d1_choice / d2_choice / d3_choice —— 每日关键选择
- wary（警惕线，沿用 watcher 隐藏线思路）
- comfort/silent/finale/release/reentered 等沿用

## 四、章节地图

```
入口: a1_boot（按 current_act/act4_done 路由）
Act1: a1_day1 → a1_poem1 → a1_day2 → a1_poem2 → a1_day3 → a1_poem3
      → a1_weekend → a1_end(她死亡冲击) → end
Act2: a2_boot → a2_day1 → a2_poem1 → 特殊诗① → a2_day2 → a2_poem2
      → 特殊诗② → a2_day3(强制选择) → a2_poem3 → 特殊诗③ → a2_end → end
Act3: a3_space → a3_talk → a3_delete(删除演出) / a3_stay(循环结局) → end
Act4: a4_main → a4_turn → a4_final → a4_final_release / a4_final_loop → end
Act5+: a5_lingering（空房间 / 循环残留）
```

## 五、素材复用/新增清单

复用：白天/夜晚/jumpscare-face/写诗贴纸×5/特殊诗×3/音效音乐/stinger/rumble
新增/替换：
- 钦灵完整情绪差分 + 崩坏差分（生成表情仅移植面部，保留原透明身体轮廓）
- `夜班教室.webp`、`无星教室.webp`、重绘 `终末教室(-zoom).webp`
- 旧 `假报错.webp`、`夜晚-崩坏1.webp`、`崩坏教室.webp` 已删除且无运行引用
- v2.8：`崩坏logo1/2.webp` 两连闪跳脸演出效果不佳，演出与素材一并删除（启动故障音与 Tear 转场保留）

## 六、警告与合规

沿用 R18+抑郁/自残/自杀暗示警告。死亡演出走"消失/删除"的含蓄表达（终末教室剪影级），
不做直白血腥画面。
