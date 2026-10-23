# 元宝登录态解析单条视频号动态：能力核对

查证日期：2026-10-21；文档状态于 2026-10-23 同步。本文保留当时的能力证据，不替代功能验收；当前行为见[本地规格](spec.md)，实现与验证范围见[验证记录](validation.md)，其他文档见[导航](README.md)。下文“本轮样本”与资源可达性只指查证当日，不表示持续可用。

## 解析链路与证据范围

1. 携带元宝登录 Cookie，向 `https://yuanbao.tencent.com/api/weixin/get_parse_result` 提交分享链接，类型为 `video_channel_url`，场景为 `1`。
2. 从返回的 `playable_url` 提取访问参数，向 `https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info` 请求该动态的信息。
3. 根据返回的具体媒体地址读取图片、视频、音频等资源。元宝登录态只用于第一步，不应将元宝 Cookie 随媒体请求发往其他域名。

本轮核对了当前本地解析代码、公开上游源码、腾讯当前公开预览页及其 JavaScript，并分析了用户指定的图文 JSON 样本。未读取登录态或发起新的认证解析请求；没有取得新的视频型动态完整响应。

未查到腾讯发布的这两个 Web 接口的完整字段契约。下表是已取得证据的字段，不是接口可能返回字段的封闭全集。字段可能缺失，未知字段应保留原名，不能凭名称编造含义。

## 第一步：元宝解析响应

[公开解析源码的响应类型](https://github.com/ltaoo/wx_channels_download/blob/124f044235bc706fe796c043a14ff442a150ae5d/pkg/scraper/wxchannels/yuanbao.go#L16-L30) 声明了以下字段。客户端类型声明会忽略其他字段，因此这些是已知字段，不证明实际响应仅有七项。

| 字段 | 已知用途或内容 | 可采取的处理 |
| --- | --- | --- |
| `author` | 作者名称 | 整理展示 |
| `author_icon` | 作者头像地址 | 有有效地址时下载图像 |
| `author_certification_icon` | 作者认证图标地址 | 有有效地址时下载图像 |
| `cover_url` | 封面地址 | 有有效地址时下载封面 |
| `desc` | 描述或正文 | 原样保留和展示 |
| `playable_url` | 视频号预览页地址及访问参数 | 用于第二步解析；它本身不是 MP4 文件 |
| `wx_export_id` | 动态解析标识 | 保留来源信息，不视为已证实的永久标识 |

查证时的本地程序仅利用第一步的 `playable_url`，其他字段未归档。此限制现已修正：当前归档分别在 `parse.json`、`feed.json` 中保留两步完整响应，并从已知字段收集媒体；取得哪一步才保存对应响应。未知字段仍原样保留，详见[当前规格](spec.md)。

## 第二步：视频号动态响应

腾讯当前公开预览页使用 `feedInfo`、`authorInfo`、`sceneInfo` 和错误信息。接口调用直接接收返回对象，没有展示完整静态 schema。

| 内容 | 字段或证据 | 能否下载或整理 |
| --- | --- | --- |
| 视频版本 | `h264VideoInfo.videoUrl`、`h265VideoInfo.videoUrl`、`videoUrl`；腾讯页面代码 | 非空地址可尝试下载对应版本，不承诺是发布者上传前的源文件 |
| 图文图片 | `picInfo[].url`；腾讯页面与本地样本 | 可逐项下载，保留顺序及实际格式 |
| 封面 | `coverUrl`；腾讯页面与本地样本 | 可下载；与正文图片是否相同需另外判断 |
| 背景音乐 | `bgmInfo.bgmUrl`；本地样本 | 可尝试直接下载；本轮样本的 HTTPS 地址已通过限量读取 |
| 备用音乐地址 | `bgmInfo.mediaStreamingUrl`；公开上游页面读取代码 | 有返回时进一步核验其内容，未有本轮实样 |
| 作者名称、头像、认证图标 | `authorInfo.nickname/headImgUrl/authIconUrl`；腾讯页面 | 名称可展示，非空图像地址可下载；样本认证图标为空 |
| 正文 | `description`；腾讯页面与本地样本 | 原样整理，不需要 OCR 或改写 |
| 创建时间 | `createtime`；腾讯页面按秒级时间戳转日期 | 保留原值并展示日期，注明使用的时区 |
| 互动展示值 | `likeCountFmt/favCountFmt/forwardCountFmt/commentCountFmt`；腾讯页面与本地样本 | 保存当次返回的展示字符串，不能假定是精确、实时的整数 |
| 位置或跳转文案 | `jumpInfo.wording`；腾讯页面的 Location 组件 | 返回时可展示文案；不能据此推断必有经纬度或完整地址；本地样本无该字段 |
| 媒体分类与展示属性 | `mediaType/scalingInfo/isHardAd` 等；本地样本 | 保留字段，已知含义再作说明；这些不是独立媒体文件 |
| 场景、标识、时效 | `sceneInfo` 中的 `dynamicExportId/expiredTime` 及场景字段；本地样本 | 本地保留原字段，不作为面向用户的主要内容或永久标识承诺 |

腾讯页面还会从媒体元素取得视频时长、宽高，通过资源请求取得 MIME 和长度。这些可以在媒体探测或下载时补充，但不能表述为本轮已证明动态接口必定返回这些字段。

没有证据证明本链路能够取得评论正文、评论者名单、点赞者名单、独立字幕文件、发布者上传前原片、完整账号历史或创作者后台数据。腾讯当前预览页的评论操作引导前往微信查看，不能以此断言不存在其他评论接口。正文中的话题文字可以原样保留，独立话题结构尚未核实。

## 用户指定样本的资源可达性

样本是图文动态，包含六张图片、一个封面、一个作者头像和一段背景音乐的地址，共九个候选资源；正文 101 字，没有视频地址或评论列表。未将样本正文、作者值、带参数的地址或标识复制到仓库。

实际采用无 Cookie 的流式 GET，请求 `Range: bytes=0-1023`，仅消费每个资源首 1024 字节后关闭，不保存资源文件；请求及重定向目标限制为已知腾讯 HTTPS 域名。

| 资源 | HTTP 结果 | 内容核对 |
| --- | --- | --- |
| 六张原图 | 全部 206 | `image/jpg`，JPEG 文件头 |
| 封面 | 200，服务器未遵从 Range | `image/jpg`，仅消费前 1024 字节，JPEG 文件头 |
| 作者头像 | 206 | `image/jpeg`，JPEG 文件头 |
| 背景音乐 | 原地址为 HTTP，未访问该 HTTP 地址；同地址改用 HTTPS 后为 206 | `audio/mp4`，ISO BMFF 文件头；URL 路径为 `.m4a` |

这证明上述资源在本轮可访问且返回了相应媒体数据，不等同于完整文件下载、解码或离线播放验收。地址时效与后续访问结果仍由外部服务决定。

## 整理可行性结论

- 媒体资源可以直接按接口提供的版本保存，不必转为 TXT；原图、封面、头像和背景音乐均有实际可达性证据，视频地址有解析流程与腾讯播放器代码证据。
- 正文、作者、日期和互动展示值可整理为离线可读内容；媒体引用本地文件，可以减少对远端地址时效的依赖。用户已确认采用离线 HTML，后续实现与验收单独记录。
- 两步解析的全部返回字段可以各自保存为 JSON，避免只挑已知字段而丢失信息；原始响应可能含访问参数，仅本地保留，不输出到公共日志或交付包。
- “字段已完整保存”“资源已完整下载”“资源可正常播放”应分别报告。资源地址存在或局部读取成功，不足以报告全部下载成功。

## 一手来源

- [腾讯公开预览页](https://channels.weixin.qq.com/finder-preview/pages/feed)：本轮无凭据 GET 为 200，并从页面取得下列资源地址。
- [腾讯当前页面脚本 feed.adb6ee0a.js](https://res.wx.qq.com/t/wx_fed/finder/web/finder-preview/res/assets/feed.adb6ee0a.js)：视频、图文、作者、时间、计数、位置文案、评论跳转和媒体探测的实际消费者。
- [腾讯当前接口脚本 merlin.208c29a2.js](https://res.wx.qq.com/t/wx_fed/finder/web/finder-preview/res/assets/merlin.208c29a2.js)：`feed/get_feed_info` 调用与返回对象读取。
- [固定版本解析器源码](https://github.com/ltaoo/wx_channels_download/blob/124f044235bc706fe796c043a14ff442a150ae5d/pkg/scraper/wxchannels/yuanbao.go)：元宝已知响应字段及两步解析流程。
- [固定版本上游页面字段读取](https://github.com/ltaoo/wx_channels_download/blob/124f044235bc706fe796c043a14ff442a150ae5d/internal/workers/sph/index.html#L454-L476)：备用背景音乐地址的消费证据，不作为腾讯完整接口契约。
