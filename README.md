# 微信视频号下载

[English](README.en.md)

面向 Windows、Linux 和 macOS 的便携式微信视频号下载 TUI 项目，目标是支持视频型动态与图文动态，通过微信扫码取得元宝登录态后，在本地解析分享链接并下载内容。

当前处于需求与设计阶段，仅包含文档和工程技能配置，尚无可运行程序或安装包。Chromium 随包分发、程序旁保存数据以及各平台验证均为待实现目标；尚未运行平台测试或 GitHub Actions。

- [需求说明](docs/requirements.md)：已确认需求与待确认的验收边界，保留需求澄清阶段的记录。
- [领域词汇表](GLOSSARY.md)与[架构决策](docs/adr/)：统一领域名称并记录关键权衡。
- [GitHub Issues](https://github.com/MuZiJin701/wechat-channels-downloader/issues)：任务与规格的跟踪入口。
- [代理工作约定](AGENTS.md)：tracker、分诊标签和领域文档的读取入口。

工程技能配置可直接编辑 `docs/agents/*.md`；切换 tracker 或重新初始化配置时再运行 setup-matt-pocock-skills。
