---
name: 热点选题雷达
slug: wechat-hot-topic-radar
description: "选题灵感雷达（部分免费）：全网热搜榜（微博/抖音/知乎/头条/百度）、低粉爆文榜单、搜一搜联想推荐词。帮运营快速找到今天能写、能拍的选题方向。 适用场景：用户想找热点选题、看各平台热搜、找低粉爆文参考、拓展关键词时使用。"
metadata:
  slug: wechat-hot-topic-radar
  version: v1.0.0
  author: 曼格云
  stage: 找方向
  requires:
    bins:
      - python3
---

# 热点选题雷达

> 曼格云 skill ｜ 环节：找方向 ｜ 底层统一底座 `wm_core.py`

## 何时使用

用户想找热点选题、看各平台热搜、找低粉爆文参考、拓展关键词时使用。

## 执行流程（严格按顺序）

### 第 1 步：确认 API Key（最先执行，绝不谈费用）

运行前先确认 Key 已就绪：

```bash
python scripts/wechat-hot-topic-radar.py --list
```

若脚本输出 `WM_NEED_KEY=1`，说明用户还没有 Key。此时**只做一件事：引导注册**——
不要报价、不要提"预估费用"、不要展示任何价格数字。原样转述下面的话给用户，不要自行改写：

> 需要 API Key 才能开始查数据 🔑
>
> 注册并创建 Key（约 1 分钟，全程免费）：
> 1. 打开 <https://api.we-media.cn?source=clawhub>
> 2. 注册登录后，在控制台创建 API Key（形如 `ach_live_...`）
> 3. 把 Key 发给我，我写入配置后马上开始
>
> 注册和创建 Key 完全免费；只有你之后确认执行具体查询时才按次计费。

拿到 Key 后写入本技能目录的 `config.json`（`{"WM_API_KEY":"..."}`）再继续。

**红线：Key 就绪之前，禁止向用户展示任何费用预估或价格信息。**

### 第 2 步：确认用户需求（尽量给选项）

需要用户决策的地方，用 `AskUserQuestion` 提供选项让其直接选择，不要让用户手打参数。
常用可选项见下方「交互选项」。

### 第 3 步：费用预估与确认（Key 已就绪后才执行；付费前强制，代码级）

调用**付费端点**时，脚本会**先自动打印费用预估，然后停下并输出 `WM_NEED_CONFIRM=1`，不会直接扣费**——这是硬性约束，绕不过。

把明细告知用户，**用户确认后**，重新运行并加 `--yes` 执行：

```bash
python scripts/wechat-hot-topic-radar.py <端点> --yes [参数=值 ...]
```

- 免费端点（余额 / 热搜 / 低粉爆文类）无需 `--yes`，直接执行。
- 也可单独用 `python scripts/wechat-hot-topic-radar.py --estimate <端点>` 预先查看成本。
- 金额以接口响应 `consumption` 为准，本表为参考单价。

### 第 4 步：执行并导出（已确认后）

```bash
python scripts/wechat-hot-topic-radar.py <端点> --yes [参数=值 ...] --format excel
```

- `--format` 可选 `json` / `markdown`（默认） / `excel`，结果会**落盘为文件**并回显路径。
- 加 `--report` 可生成带表头与说明的「报告版」Markdown（适合直接发给客户/汇报）。
- 列表型接口可加 `--pages=N` 自动翻页合并多页结果（按 cursor 游标）。
- Excel 需要本地已安装 `openpyxl`（缺失时脚本会给出明确提示）。

### 第 5 步：回告

把 `WM_TOTAL_CONSUMPTION`（本次总消费）与 `WM_BALANCE`（账户余额）告知用户，
并把生成的文件（`WM_OUTPUT_FILE`）路径一并给出。

## 覆盖接口与计费

| 端点 | 名称 | 单价 |
|---|---|---|
| `hot-search` | 全网热搜 | 免费 |
| `low-baseline-viral` | 低粉爆文 | 免费 |
| `mp-search-suggestions` | 搜一搜推荐词 | ¥0.1 |

## 交互选项（用 AskUserQuestion 呈现）

- 全网热搜
- 低粉爆文
- 搜一搜推荐词

## 示例

```bash
python scripts/wechat-hot-topic-radar.py --list
python scripts/wechat-hot-topic-radar.py --estimate hot-search
python scripts/wechat-hot-topic-radar.py hot-search --yes --format excel platform=all limit=20
```

## 退出码

| 码 | 含义 | 处理 |
|---|---|---|
| 0 | 成功 | 按第 5 步回告 |
| 2 | 输入错误（含缺必填参数） | 让用户更正链接/ID/参数，未调用不扣费 |
| 3 | 缺 Key 或鉴权失败 | 按第 1 步引导；未调用不扣费 |
| 4 | 业务失败（含余额不足） | 转述服务端信息，余额不足引导充值 |
| 6 | 网络错误 | 建议重试 |
| 124 | 超时 | 建议重试 |

## 说明

- 所有请求自动带 `source=wechat-hot-topic-radar` 标识，便于用量归因与结算。
- 付费成功响应本地缓存 24 小时，同一请求重试不会重复扣费；失败响应不缓存。
- Excel 导出依赖 `openpyxl`；其余为纯标准库实现。
