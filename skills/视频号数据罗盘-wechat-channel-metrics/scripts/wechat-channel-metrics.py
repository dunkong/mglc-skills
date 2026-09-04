#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频号数据罗盘 —— 曼格云 skill（统一底座，source=wechat-channel-metrics）

用法：
  python scripts/wechat-channel-metrics.py --list
  python scripts/wechat-channel-metrics.py --estimate <端点> [参数]
  python scripts/wechat-channel-metrics.py <端点> [k=v ...] [--yes] [--format json|markdown|excel] [--report] [--output=路径] [--pages=N]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wm_core import WM, estimate, print_estimate, require_key, load_key, key_url, Formatter, EP, EXIT_INPUT, EXIT_OK

SLUG = "wechat-channel-metrics"
SOURCE = "clawhub"
KEY_URL = key_url(SOURCE)
ENDPOINTS = ['ch-metrics', 'ch-info']
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
    is_help = not positional or positional[0] in ("-h", "--help", "--list")
    is_est = bool(positional) and positional[0] == "--estimate"

    # ① 第一优先：检查 Key。没有 Key 时只做注册引导（不显示任何价格信息），退出码 3。
    #    引导链接带 ?source=<SOURCE>，用于统计用户来源平台。
    if not load_key():
        require_key(SLUG, SOURCE)   # 内部打印引导并 sys.exit(3)

    if is_help:
        print("可用端点：")
        for k in ENDPOINTS:
            e = EP[k]
            print("  {:32s} {:4s} Â¥{:<8} {}".format(k, e["method"], e["price"], e["name"]))
        print("")
        print("示例: python scripts/wechat-channel-metrics.py <端点> --yes url=链接 --format excel")
        sys.exit(EXIT_OK)

    if is_est:
        print_estimate(estimate(positional[1:]), title="视频号数据罗盘 费用预估")
        sys.exit(EXIT_OK)

    key = positional[0]
    if key not in ENDPOINTS:
        print("该 skill 不含端点 {!r}，可用：{}".format(key, ", ".join(ENDPOINTS)), file=sys.stderr)
        sys.exit(EXIT_INPUT)
    ep = EP[key]

    # 说明：参数合法性交由服务端校验（返回中文错误更明确），此处不做强校验，
    # 避免把可选项（如 ghid 与 url 二选一）误判为必填导致误退。

    # 付费前强制预估（零调用零扣费）
    est = estimate([(key, params)])
    print_estimate(est, title="视频号数据罗盘 费用预估")
    if est["total"] > 0 and not yes:
        print("WM_NEED_CONFIRM=1")
        print("以上为预估费用。用户确认后加 --yes 执行：")
        rest = " ".join(a for a in sys.argv[1:] if a not in ("--yes", "-y"))
        print("  python scripts/wechat-channel-metrics.py {key} --yes {rest}".format(key=key, rest=rest))
        sys.exit(EXIT_OK)

    wm = WM(SLUG, source=SOURCE)

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
