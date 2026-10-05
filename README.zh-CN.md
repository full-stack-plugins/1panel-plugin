# 1Panel

## 插件市场导航

本插件所属分类：**全栈开发**。

| 分类 | 插件市场入口 | 用途 |
| --- | --- | --- |
| 全栈开发 | [Full Stack Plugins](https://github.com/partme-ai/full-stack-plugins) | 架构与 UI 设计、代码理解、质量检查、代码审查、流程治理与服务器运维 |
| AIGC 内容创作 | [Full AIGC Plugins](https://github.com/partme-ai/full-aigc-plugins) | 图像、视频、音频、音乐、3D 与多模态内容创作 |

通过受控 stdio 入口、私有配置和可执行权限规则接入官方 1Panel MCP。英文显示名称为 **1Panel**。`1panel` 0.1.1 源码仓库：[1panel-plugin](https://github.com/full-stack-plugins/1panel-plugin)。固定版本 v0.1.1 通过 Full Stack 插件市场分发，客户端安装验收另行进行，本插件由社区维护。

[English](README.md) | 简体中文 · [架构](docs/1Panel-Plugin-Architecture.zh_CN.md) · [验收合同](docs/implementation-spec.md)

## 架构与能力

```mermaid
flowchart LR
    A[8 个来源技能] --> B[实际发现的 MCP 工具]
    B --> C[标准 mcp.json：stdio 权限入口]
    D[私有 PLUGIN_DATA 配置] --> C
    C --> E[锁定的官方 mcp-1panel]
    E --> F[用户既有 1Panel API]
    F --> G[实际结果与复核]
```

8 个技能覆盖分流、设置、系统、网站、证书、数据库、应用和有限风险审查，从 1panel-skills 按文件哈希快照分发。官方服务固定为 v1.0.0 / a12b2d4ddae90f6b210b73b89ba2bc4b572dcd0c，由用户独立编译或安装；Apache 插件包不捆绑 GPL 服务源码或二进制。

默认 readonly 仅提供 6 个读取工具；readwrite 增加 create_website/create_ssl/create_database；full 再增加 install_mysql/install_openresty。工具发现经过过滤，直接调用受限或未知工具也会被拒绝。配置使工具可用，不代表全面操作授权或面板端 RBAC。官方发布版尚无访问级别参数，因此权限由插件入口执行。

不承诺删除、防火墙、SSH、备份恢复、任意 SQL、通用应用安装或证书续期/绑定。列表上限为 500；证书创建内部选首个 ACME 账户；MySQL 创建默认来源权限 `%`；自动生成密码不是可靠凭据交付渠道。操作前阅读技能内部工具引用。

## 显式设置

需要 Python 3.11+、已开启 API 的既有面板及可信官方可执行文件。根 mcp.json 遵守 Agent Plugins 1.0.0，不包含密钥，也不依赖继承的 PANEL 环境变量。`${PLUGIN_DATA}` 由标准客户端提供，私有配置不存进插件。

显式源码构建需要已有官方 checkout（含 v1.0.0 tag）、Git 和 Go 1.25+：

```text
python scripts/build_official.py --source <official-checkout> --output <new-absolute-binary-path>
```

辅助工具校验 ref/commit，使用 GOTOOLCHAIN=local 构建，生成含 SHA256 的构建记录，不安装或升级 Go。构建会获取项目依赖。使用哈希前核实来源与记录；哈希本身不证明发布者身份。

```text
python scripts/setup_connection.py --data <absolute-client-data> --binary <verified-absolute-binary> --binary-sha256 <verified-sha256> --host <https-panel-origin>
```

密钥通过本地隐藏输入接收。connection.json 保存二进制身份、地址、上游 commit 和访问级别；credentials.json 单独保护（POSIX 权限或 Windows 当前用户 ACL）。不要把密钥粘贴进聊天。默认 readonly，`--access-level readwrite` 或 full 表示显式变更；覆盖既有设置需要 `--replace`，然后重连。官方子进程通过环境接收凭据，不放进参数；其本地日志位于私有 runtime 目录，插件不记录请求内容。

Codex/Claude 清单和 .mcp.json 为兼容文件。不提供或不展开 PLUGIN_DATA 的原生客户端须在私有配置中明确绝对数据路径；不能启动 Windows .cmd 别名时须选真实 Python 可执行文件。原生路径展开和已安装客户端加载未验证，不能用清单一致性代替安装验收。

## 操作与异常合同

确认准确目标和已有授权，检查既有资源，一次提交有界操作，然后用可用读取复核。不会自动重试；超时或子进程丢失标为结果未知，先检查面板状态再决定是否重发。没有自动删除回滚。配置错误只输出简洁脱敏诊断，MCP 入口不可用时其它技能仍可加载。

## 校验与打包

```bash
python scripts/validate_portable_plugin.py
python scripts/validate_markdown_links.py
python scripts/check_snapshot.py
python -m unittest discover -s tests -v
python scripts/package_plugin.py
```

运行真实官方 MCP 集成测试前，将 ONEPANEL_TEST_BINARY 设置为独立构建的锁定版二进制路径；未设置时会明确跳过，不能算已覆盖。测试通过本插件入口初始化真实官方服务，向回环模拟 API 调用全部 11 个工具，检查认证、权限、异常、脱敏和未知结果，不修改生产服务器。

压缩包和 SHA256 位于 dist/，排除密钥、日志和本地二进制。实际结果见[验证记录](docs/verification.md)。托管发布、市场登记以及用户已安装客户端/生产面板验收保持独立状态。见[许可证](LICENSE)和[来源声明](THIRD-PARTY-NOTICES.md)。

## 安装与技能源维护

通过客户端市场界面添加 `partme-ai/full-stack-plugins`，再选择 **1Panel**；安装来源固定为 `v0.1.1`。先按本文设置官方可执行文件、私有数据目录与面板 API；安装技能不会自动配置连接。

技能内容只在 `1panel-skills` 修改。先发布技能源版本，再更新固定来源并执行：

```bash
python scripts/vendor/skill_vendor.py update
python scripts/vendor/skill_vendor.py check
python scripts/check_snapshot.py
```
