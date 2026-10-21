# WeChat Channels Downloader

[简体中文](README.md)

A planned portable TUI for Windows, Linux, and macOS that downloads WeChat Channels videos and image posts. The intended flow uses WeChat QR login to obtain a Yuanbao session, then resolves share links and downloads their content locally.

The project is in the requirements and design stage. It currently contains documentation and engineering skill configuration; no runnable application or release package is available. Bundled Chromium, data stored beside the application, and platform verification are planned. No platform tests or GitHub Actions workflows have been run.

- [Requirements](docs/requirements.md): confirmed requirements and the proposed acceptance boundary, including records from the requirements interview.
- [Glossary](GLOSSARY.md) and [architecture decisions](docs/adr/): domain vocabulary and important trade-offs.
- [GitHub Issues](https://github.com/MuZiJin701/wechat-channels-downloader/issues): the tracker for tasks and specifications.
- [Agent conventions](AGENTS.md): entry points for tracker, triage label, and domain documentation rules.

Edit `docs/agents/*.md` directly to adjust the configuration. Run setup-matt-pocock-skills again only to switch trackers or restart the setup.
