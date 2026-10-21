# Issue tracker：GitHub

任务与规格保存在 [MuZiJin701/wechat-channels-downloader 的 GitHub Issues](https://github.com/MuZiJin701/wechat-channels-downloader/issues)。
使用 gh CLI；仓库外运行时显式传入 `--repo MuZiJin701/wechat-channels-downloader`。

- 读取：`gh issue view <编号> --json number,title,body,labels,comments`
- 列表：`gh issue list --state open`
- 创建：`gh issue create --title "..." --body-file <文件>`
- 评论：`gh issue comment <编号> --body-file <文件>`
- 标签：`gh issue edit <编号> --add-label "..."` 或 `--remove-label "..."`
- 关闭：`gh issue close <编号>`

多行正文通过 UTF-8 文件传入。发布任务指创建 Issue；读取任务指读取对应 Issue。
创建、评论及其他写入须有当前任务授权。

## Pull requests as a triage surface

**PRs as a request surface: no.**
