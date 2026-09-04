#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量生成 mglc-* skill。所有 skill 共用 wm_core.py，底层完全一致。"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILLS = os.path.join(ROOT, "skills")

EP = {e["key"]: e for e in json.load(open(os.path.join(HERE, "endpoints.json"), encoding="utf-8"))["endpoints"]}
PRODUCTS = json.load(open(os.path.join(HERE, "products.json"), encoding="utf-8"))

# 这些参数名一旦出现即为必填（避免无输入空跑）
REQ_NAMES = {"url", "ghid", "keyword", "query", "secUid", "accountId",
             "shareUrl", "objectId", "exportId", "videoId", "fileUrl",
             "videoUrl", "biz"}

RUNNER = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{name} —— 曼格云 skill（统一底座，source={slug}）

用法：
  python scripts/{slug}.py --list
  python scripts/{slug}.py --estimate <端点> [参数]
  python scripts/{slug}.py <端点> [k=v ...] [--yes] [--format json|markdown|excel] [--report] [--output=路径] [--pages=N]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wm_core import WM, estimate, print_estimate, require_key, Formatter, EP, EXIT_INPUT, EXIT_OK

SLUG = "{slug}"
ENDPOINTS = {endpoints!r}
REQ_NAMES = {"url", "ghid", "keyword", "query", "secUid", "accountId",
             "shareUrl", "objectId", "exportId", "videoId", "fileUrl", "videoUrl", "biz"}


def parse(argv):
    params = {}
    fmt = "markdown"
    report = False
    output = None
    yes = False
    pages = 1
    file_path = None
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--file":
            i += 1
            if i < len(argv):
                file_path = argv[i]
        elif a.startswith("--file="):
            file_path = a.split("=", 1)[1]
        elif a == "--format":
            i += 1
            if i < len(argv):
                fmt = argv[i]
        elif a.startswith("--format="):
            fmt = a.split("=", 1)[1]
        elif a == "--output":
            i += 1
            if i < len(argv):
                output = argv[i]
        elif a.startswith("--output="):
            output = a.split("=", 1)[1]
        elif a == "--pages":
            i += 1
            try:
                pages = max(1, int(argv[i]))
            except (ValueError, IndexError):
                pages = 1
        elif a.startswith("--pages="):
            try:
                pages = max(1, int(a.split("=", 1)[1]))
            except ValueError:
                pages = 1
        elif a == "--report":
            report = True
        elif a == "--yes" or a == "-y":
            yes = True
        elif "=" in a:
            k, v = a.split("=", 1)
            if v.isdigit():
                v = int(v)
            params[k] = v
        else:
            positional.append(a)
        i += 1
    return positional, params, fmt, report, output, yes, pages, file_path


def main():
    positional, params, fmt, report, output, yes, pages, file_path = parse(sys.argv[1:])
    if not positional or positional[0] in ("-h", "--help", "--list"):
        print("可用端点：")
        for k in ENDPOINTS:
            e = EP[k]
            print("  {:32s} {:4s} \xc2\xa5{:<8} {}".format(k, e["method"], e["price"], e["name"]))
        print("")
        print("示例: python scripts/{slug}.py <端点> --yes url=链接 --format excel")
        sys.exit(EXIT_OK)

    if positional[0] == "--estimate":
        print_estimate(estimate(positional[1:]), title="{name} 费用预估")
        sys.exit(EXIT_OK)

    key = positional[0]
    if key not in ENDPOINTS:
        print("该 skill 不含端点 {!r}，可用：{}".format(key, ", ".join(ENDPOINTS)), file=sys.stderr)
        sys.exit(EXIT_INPUT)
    ep = EP[key]

    # 无 Key 引导（退出码 3，0 费用）—— 放在校验之前，没 Key 先引导
    require_key(SLUG)

    # 说明：参数合法性交由服务端校验（返回中文错误更明确），此处不做强校验，
    # 避免把可选项（如 ghid 与 url 二选一）误判为必填导致误退。

    # 付费前强制预估（零调用零扣费）
    est = estimate([(key, params)])
    print_estimate(est, title="{name} 费用预估")
    if est["total"] > 0 and not yes:
        print("WM_NEED_CONFIRM=1")
        print("以上为预估费用。用户确认后加 --yes 执行：")
        rest = " ".join(a for a in sys.argv[1:] if a not in ("--yes", "-y"))
        print("  python scripts/{slug}.py {key} --yes {rest}".format(key=key, rest=rest))
        sys.exit(EXIT_OK)

    wm = WM(SLUG)

    # 本地文件：先传到平台临时存储（不计费、≤128MB、2 小时后自动清理），换成公网地址
    if file_path:
        _u = wm.upload_file(file_path)
        if "videoUrl" in ep.get("params", []):
            params["videoUrl"] = _u
        elif "audioUrl" in ep.get("params", []):
            params["audioUrl"] = _u
        else:
            print("端点 {} 不接受文件地址参数，--file 不适用".format(key), file=sys.stderr)
            sys.exit(EXIT_INPUT)
    # 也允许把 videoUrl/audioUrl 直接写成本地路径，自动识别并上传
    for _pk in ("videoUrl", "audioUrl"):
        _v = params.get(_pk)
        if (isinstance(_v, str) and not _v.startswith(("http://", "https://", "file://"))
                and os.path.isfile(_v)):
            params[_pk] = wm.upload_file(_v)

    if pages > 1 and ep["method"].upper() == "POST":
        rows = wm.paginate(key, max_pages=pages, **params)
        data = {"count": len(rows), "items": rows}
    else:
        data = wm.call(key, **params)
    wm.finish()

    fmtri = Formatter(SLUG)
    path, n = fmtri.present(data, ep["name"], fmt=fmt, report=report, output=output)
    print("WM_OUTPUT_FILE=" + path)
    print("WM_ROWS=" + str(n))
    if fmt == "markdown" and not report:
        print("")
        print(fmtri.preview(data, ep["name"], n=5))


if __name__ == "__main__":
    main()
'''

SKILL_TMPL = '''---
name: {name}
slug: {slug}
description: "{desc} 适用场景：{desc_when}。"
metadata:
  slug: {slug}
  version: v1.0.0
  author: 曼格云
  stage: {stage}
  requires:
    bins:
      - python3
---

# {name}

> 曼格云 skill ｜ 环节：{stage} ｜ 底层统一底座 `wm_core.py`

## 何时使用

{desc_when}。

## 执行流程（严格按顺序）

### 第 1 步：确认 API Key（不产生费用）

运行前先确认 Key 已就绪：

```bash
python scripts/{slug}.py --list
```

若用户未提供 Key，脚本会退出码 3 并输出标准引导。此时**原样转述下面的话给用户**，不要自行改写：

> 需要曼格云 API Key 才能调用数据接口 🔑
>
> 获取步骤（约 1 分钟）：
> 1. 打开 <https://api.we-media.cn> 注册并登录
> 2. 在控制台创建 API Key（形如 `ach_live_...`）
> 3. 把 Key 发给我，我写入配置后就可以开始
>
> 没有 Key 之前不会产生任何费用。

拿到 Key 后写入本技能目录的 `config.json`（`{"WM_API_KEY":"..."}`）再继续。

### 第 2 步：确认用户需求（尽量给选项）

需要用户决策的地方，用 `AskUserQuestion` 提供选项让其直接选择，不要让用户手打参数。
常用可选项见下方「交互选项」。

### 第 3 步：费用预估与确认（付费前强制，代码级）

调用**付费端点**时，脚本会**先自动打印费用预估，然后停下并输出 `WM_NEED_CONFIRM=1`，不会直接扣费**——这是硬性约束，绕不过。

把明细告知用户，**用户确认后**，重新运行并加 `--yes` 执行：

```bash
python scripts/{slug}.py <端点> --yes [参数=值 ...]
```

- 免费端点（余额 / 热搜 / 低粉爆文类）无需 `--yes`，直接执行。
- 也可单独用 `python scripts/{slug}.py --estimate <端点>` 预先查看成本。
- 金额以接口响应 `consumption` 为准，本表为参考单价。

### 第 4 步：执行并导出（已确认后）

```bash
python scripts/{slug}.py <端点> --yes [参数=值 ...] --format excel
```

- `--format` 可选 `json` / `markdown`（默认） / `excel`，结果会**落盘为文件**并回显路径。
- 加 `--report` 可生成带表头与说明的「报告版」Markdown（适合直接发给客户/汇报）。
- 列表型接口可加 `--pages=N` 自动翻页合并多页结果（按 cursor 游标）。
- Excel 需要本地已安装 `openpyxl`（缺失时脚本会给出明确提示）。

### 第 5 步：回告

把 `WM_TOTAL_CONSUMPTION`（本次总消费）与 `WM_BALANCE`（账户余额）告知用户，
并把生成的文件（`WM_OUTPUT_FILE`）路径一并给出。

## 覆盖接口与计费

{price_table}

## 交互选项（用 AskUserQuestion 呈现）

{options}

## 示例

```bash
python scripts/{slug}.py --list
python scripts/{slug}.py --estimate {primary}
python scripts/{slug}.py {primary} --yes --format excel {example}
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

- 所有请求自动带 `source={slug}` 标识，便于用量归因与结算。
- 付费成功响应本地缓存 24 小时，同一请求重试不会重复扣费；失败响应不缓存。
- Excel 导出依赖 `openpyxl`；其余为纯标准库实现。
'''


def price_table(keys, allmode):
    rows = ["| 端点 | 名称 | 单价 |", "|---|---|---|"]
    if allmode:
        for k, e in sorted(EP.items(), key=lambda x: (x[1]["cat"], x[1]["name"])):
            p = "免费" if (e.get("free") or e["price"] == 0) else "¥{}".format(e["price"])
            rows.append("| `{}` | {} | {} |".format(k, e["name"], p))
    else:
        for k in keys:
            e = EP.get(k)
            if not e:
                continue
            p = "免费" if (e.get("free") or e["price"] == 0) else "¥{}".format(e["price"])
            rows.append("| `{}` | {} | {} |".format(k, e["name"], p))
    return "\n".join(rows)


def build():
    os.makedirs(SKILLS, exist_ok=True)
    made = []
    for p in PRODUCTS:
        slug, name = p["slug"], p["name"]
        dname = p.get("dir", slug)  # 目录名：中文混合展示名（slug 仍用于脚本/归因）
        d = os.path.join(SKILLS, dname)
        os.makedirs(os.path.join(d, "scripts"), exist_ok=True)

        # 交互选项
        if p.get("all"):
            opts = "本 skill 为平台入口，覆盖全部接口。用户需求不明确时，先给这几个方向让其选择：\n\n" + \
                   "\n".join("- {}".format(s) for s in
                            ["查公众号（文章/账号/历史）", "查视频号（作品/博主/互动）",
                             "找号找达人", "找选题热点", "AI 分析（视频理解/转写）",
                             "查余额"])
        else:
            opts = "\n".join("- {}".format(EP[k]["name"]) for k in p["endpoints"] if k in EP)

        # 示例参数（注意 ch-account-search 真实参数名为 keyword）
        primary = p["endpoints"][0]
        exmap = {
            "mp-account-articles": "url=https://mp.weixin.qq.com/s/xxxx",
            "mp-account-articles-today": "url=https://mp.weixin.qq.com/s/xxxx",
            "mp-account-profile": "url=https://mp.weixin.qq.com/s/xxxx",
            "mp-article-info": "url=https://mp.weixin.qq.com/s/xxxx",
            "ch-info": "url=https://channels.weixin.qq.com/sph/xxxx",
            "ch-video-list": "accountId=your_account_id",
            "video-understanding": "videoUrl=https://example.com/a.mp4 analysisMode=timeline",
            "audio-transcription": "fileUrl=https://example.com/a.m4a",
            "hot-search": "platform=all limit=20",
            "low-baseline-viral": "limit=20",
            "mp-search-accounts": "query=职场",
            "ch-account-search": "keyword=美食",
            "mp-search-miniprograms": "query=点餐",
            "douyin-author-posts": "url=https://www.douyin.com/user/xxxx",
            "account-balance": "",
            "mp-search-suggestions": "query=视频号",
        }
        example = exmap.get(primary, "url=你的链接")

        md = (SKILL_TMPL
              .replace("{name}", name)
              .replace("{slug}", slug)
              .replace("{desc}", p["desc"])
              .replace("{desc_when}", p["when"])
              .replace("{stage}", p["stage"])
              .replace("{price_table}", price_table(p["endpoints"], bool(p.get("all"))))
              .replace("{options}", opts)
              .replace("{primary}", primary)
              .replace("{example}", example))
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(md)

        runner = (RUNNER
                  .replace("{name}", name)
                  .replace("{slug}", slug)
                  .replace("{endpoints!r}", repr(p["endpoints"])))
        with open(os.path.join(d, "scripts", slug + ".py"), "w", encoding="utf-8") as f:
            f.write(runner)

        # 自包含：复制底座
        for src in ("wm_core.py", "endpoints.json"):
            shutil.copy(os.path.join(HERE, src), os.path.join(d, "scripts", src))
        made.append(slug)
    return made


if __name__ == "__main__":
    m = build()
    print("生成 {} 个 skill：".format(len(m)))
    for s in m:
        print("  " + s)
