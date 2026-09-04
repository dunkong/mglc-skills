# 曼格云 Skill 矩阵（微信生态数据 API 技能包）

> 官网：https://api.we-media.cn ｜ 共 **16** 个 skill ｜ 底层统一底座 `wm_core.py` ｜ 付费前强制预估费用
>
> 商业模式：**skill 是 API 获客前端，收入来自按调用量计费**（官网充值，不接 SkillPay）。

## 一句话说明

每个 `skills/<目录名>/` 是一个独立、可直接上架的 skill（含 `SKILL.md` + `scripts/`）。
用户无 Key 时引导去官网创建；所有付费接口调用前自动打印费用预估，需 `--yes` 确认才扣费；
失败 / 超限接口费用自动退回（已用真实 Key 全量实测验证）。

## 技能目录（16 个）

| 名称 | 目录（标题） | 定位 | 覆盖接口 |
|------|------|------|----------|
| 微信生态数据台 | `微信生态数据台-wechat-ecosystem-data-hub` | 平台入口 | 全部接口（32 个，详见各专项 skill） |
| 公众号历史文章库 | `公众号历史文章库-wechat-official-history` | 追号 | 公众号历史文章、公众号今日文章、公众号资料、文章短链解析 |
| 公众号文章数据透视 | `公众号文章数据透视-wechat-official-article-analytics` | 看内容 | 文章基本信息、文章互动数据、文章正文、文章媒体资源、文章完整数据、文章完整报告 |
| 公众号找号 | `公众号找号-wechat-official-account-finder` | 找号 | 搜一搜公众号、公众号资料 |
| 公众号竞品追踪 | `公众号竞品追踪-wechat-official-competitor-tracker` | 看同行 | 公众号资料、公众号历史文章、文章互动数据 |
| 视频号作品透视 | `视频号作品透视-wechat-channel-video-insight` | 看内容 | 视频号作品资料、视频号作品解析、视频号分享链接、export 转作品 |
| 视频号博主动态 | `视频号博主动态-wechat-channel-author-feed` | 追号 | 视频号作品列表、视频号账号搜索 |
| 视频号数据罗盘 | `视频号数据罗盘-wechat-channel-metrics` | 看数据 | 视频号互动数据、视频号作品资料 |
| 视频号找号 | `视频号找号-wechat-channel-finder` | 找号 | 视频号账号搜索、视频号作品资料 |
| 视频号投放背调 | `视频号投放背调-wechat-channel-ad-audit` | 找号 | 视频号账号搜索、视频号作品列表、视频号作品资料、视频号互动数据 |
| 热点选题雷达 | `热点选题雷达-wechat-hot-topic-radar` | 找方向 | 全网热搜、低粉爆文、搜一搜推荐词 |
| 微信选题挖掘 | `微信选题挖掘-wechat-search-topic-mining` | 找方向 | 搜一搜综合、微信指数、搜一搜文章、搜一搜推荐词、搜索引导 |
| 视频内容理解官 | `视频内容理解官-video-content-understanding` | 做内容 | 视频视觉理解、视频号播放地址 |
| 音视频转写台 | `音视频转写台-audio-video-transcription` | 做内容 | 音频转文字、视频号播放地址 |
| 视频号直播回放台 | `视频号直播回放台-wechat-channel-live-replay` | 看数据 | 视频号直播回放、视频号作品资料、视频号互动数据 |
| 小程序查找 | `小程序查找-wechat-mini-program-finder` | 找号 | 搜一搜小程序 |

## 怎么上架到 skillhub / clawhub

每个 skill 目录即为一个独立发布单元，逐个上传即可（目录名即平台显示标题）：

```bash
# 以「视频号找号」为例
# 在 skillhub / clawhub 的发布入口选择 skills/视频号找号-wechat-channel-finder/ 目录发布
skills/
├── 微信生态数据台-wechat-ecosystem-data-hub/       # 平台入口（全接口兜底）
├── 视频号找号-wechat-channel-finder/          # 视频号找号
├── 视频内容理解官-video-content-understanding/    # 视频内容理解官
└── ... （其余 13 个）
```

- 无 Key 引导、source 归因、费用预估、Excel/Markdown/报告输出均已内置。
- 抖音相关与「账户余额」独立 skill 未纳入（抖音先不上；余额能力保留在每次付费调用后回告 `WM_BALANCE`）。

## GitHub 自动同步

本目录已 `git init` 并提交。要同步到 GitHub：

```bash
git remote add origin <你的仓库地址>
git push -u origin main
```

之后每次更新只需 `git add -A && git commit && git push`。

## 计费与合规

- 计费以接口响应 `consumption` 为准，调用前先预估。
- 合规红线：**不触碰评论 / 个人信息抓取**；本矩阵已剔除全部评论类端点。
- 临时文件直传（视频/音频分析前上传到平台存储）不计费，≤128MB，约 2 小时清理。

> 测试报告：`reports/realtest_report.md`（33 端点全绿、16 skill 全绿、封装层实测）。
