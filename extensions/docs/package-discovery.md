# 从包自身发现 DLC

运行时 SDK 0.2.1 起，LC 的「同步目录」请求本仓库的 [GitHub Releases API](https://api.github.com/repos/sdfsfsk/LingChat-DLC/releases)，不再请求中央 `catalog-v2.json`。宿主只接入通用接口；包发现、校验及发布脚本都位于 DLC 仓库。

## 内容作者需要维护什么

仅维护 `packages/<包目录>/manifest.toml` 和该包内容。新增包无需在其他文件注册 ID、名称或下载链接；游戏/剧本声明继续复用插件清单的 `[[games]]` 或 `story_api_version` / `resources`。修改内容时递增清单的语义版本。

构建后，`scripts/package.py` 自动生成配对附件，例如：

```text
star-trail-1.0.3.zip
star-trail@1.0.3.manifest.toml
```

第二个文件直接从第一个 ZIP 的根目录 `manifest.toml` 导出，字节完全一致，不能手工另写。`@` 分隔包 ID 与版本，避免 ID 或预发布版本中的连字符歧义。

## 发现与校验

1. 分页查询正式 Release，跳过草稿和预发布 Release（SDK 发布使用预发布）。只识别配对的 `.manifest.toml` 和 `.zip` 附件，其余附件不影响发现。
2. 按每个包的语义版本选择最高版本，不依赖 Release 顺序；同一版本不能对应不同 ZIP 摘要。
3. 下载所选版本的小清单，验证长度、SHA-256、ID、版本及现有插件权限约束，从中生成名称、简介、类型与版本。ZIP 的下载地址、大小与摘要使用 GitHub 附件元数据；列表同步不会下载游戏 ZIP。
4. 全部成功后原子替换本地缓存。网络、限流或校验失败保留旧缓存，用户可稍后重试；安装时仍验证 ZIP 摘要、路径、清单与接口版本。

清单最大 64 KiB，安装包最大 128 MiB，最多 256 个包；Release 分页最多 1,000 条，超限明确报错而不默默截断。网络请求复用现有 HTTPS、重定向和响应大小限制。GitHub 未认证 API 有访问频率限制，离线仍可显示缓存、运行已安装内容。

SHA-256 来自 GitHub [Release asset 的 digest 字段](https://docs.github.com/en/rest/releases/assets)；缺少摘要的旧附件需要重新发布为完整的包与清单组合。下载的清单不是远程代码，权限仍由插件安装和 DLC API 校验。

## 发布与兼容

`Build DLC release` 工作流会测试、构建、打包并上传全部配对文件，上传完成后才把草稿 Release 公开。发布脚本比较既有公开附件摘要，拒绝同版本覆盖。`dist/release-assets.json` 只是自动生成的临时上传计划，既不是客户端索引，也不提交到仓库。

`catalog.json` / `catalog-v2.json` 保持原样供旧客户端使用，不再随发布自动修改；旧客户端仍能安装其原有条目，需要升级宿主才能发现后续内容。新版可读取旧内置目录缓存，再通过「同步目录」刷新为 Release 发现结果。现有 ZIP 不重打版本，只为当前正式 Release 补充从原 ZIP 导出的清单。

运行时源码：`extensions/rust/runtime/src/games/discovery.rs`；不包含任何具体游戏或剧本的名称、ID 或版本列表。
