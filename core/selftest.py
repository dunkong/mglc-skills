#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量自测：语法 / --list / --estimate / 无key引导 / source 注入 / SKILL.md frontmatter"""
import ast
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILLS = os.path.join(ROOT, "skills")
PY = sys.executable

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    return ok


slugs = sorted([d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d))])

# 1. 语法
bad = []
for s in slugs:
    for f in ("{}.py".format(s), "wm_core.py"):
        p = os.path.join(SKILLS, s, "scripts", f)
        if not os.path.isfile(p):
            bad.append("{}:缺少{}".format(s, f))
            continue
        try:
            ast.parse(open(p, encoding="utf-8").read())
        except SyntaxError as e:
            bad.append("{}:{}:{}".format(s, f, e))
check("语法解析 ({}个skill × 2文件)".format(len(slugs)), not bad, "; ".join(bad[:3]))

# 2. --list
bad = []
for s in slugs:
    r = subprocess.run([PY, os.path.join(SKILLS, s, "scripts", s + ".py"), "--list"],
                       capture_output=True, text=True)
    if r.returncode != 0 or "可用端点" not in r.stdout:
        bad.append(s)
check("--list 可用", not bad, ",".join(bad[:3]))

# 3. --estimate（无 key 也必须可用）
bad = []
for s in slugs:
    env = dict(os.environ)
    env.pop("WM_API_KEY", None)
    r = subprocess.run([PY, os.path.join(SKILLS, s, "scripts", s + ".py"), "--estimate"],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0 or "WM_ESTIMATE_TOTAL" not in r.stdout:
        bad.append("{}:rc={}".format(s, r.returncode))
check("--estimate 无key可用（付费前预估）", not bad, "; ".join(bad[:3]))

SLUGS = sorted([d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d))])
PRODUCTS = {p["slug"]: p for p in json.load(
    open(os.path.join(HERE, "products.json"), encoding="utf-8"))}

# 2b. --list 必须列出真实端点名（防止格式串被破坏）
bad = []
for s in SLUGS:
    r = subprocess.run([PY, os.path.join(SKILLS, s, "scripts", s + ".py"), "--list"],
                       capture_output=True, text=True)
    for k in PRODUCTS[s]["endpoints"]:
        if k not in r.stdout:
            bad.append("{}:缺{}".format(s, k))
            break
    if "{:" in r.stdout or "{{" in r.stdout:
        bad.append(s + ":格式串未展开")
check("--list 输出真实端点名（格式正确）", not bad, "; ".join(bad[:3]))

# 4. 无 key 调用 -> 退出码 3 + 引导
bad = []
for s in SLUGS:
    env = dict(os.environ)
    env.pop("WM_API_KEY", None)
    script = os.path.join(SKILLS, s, "scripts", s + ".py")
    first = PRODUCTS[s]["endpoints"][0]
    r = subprocess.run([PY, script, first, "url=test"], capture_output=True, text=True, env=env)
    if r.returncode != 3 or "api.we-media.cn" not in (r.stderr + r.stdout):
        bad.append("{}:rc={}".format(s, r.returncode))
check("无key调用→退出码3+官方引导", not bad, "; ".join(bad[:3]))

# 5. source 注入（mock 抓包）
sys.path.insert(0, os.path.join(HERE))
os.environ["WM_API_KEY"] = "test_key_for_mock"
import wm_core

captured = {}


class FakeResp:
    def read(self):
        return json.dumps({"code": "OK", "data": {"ok": 1},
                           "consumption": 0.01, "balance": 9.9}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_urlopen(req, timeout=None):
    captured["url"] = req.full_url
    captured["data"] = req.data
    captured["headers"] = dict(req.headers)
    return FakeResp()


wm_core.urllib.request.urlopen = fake_urlopen
try:
    wm = wm_core.WM("mglc-source-test", cache=False)
    wm.call("ch-info", url="https://channels.weixin.qq.com/sph/test")
    body = json.loads(captured["data"].decode("utf-8"))
    hdr = {k.lower(): v for k, v in captured["headers"].items()}
    ok_body = body.get("source") == "mglc-source-test"
    ok_hdr = hdr.get("x-wm-source") == "mglc-source-test"
    check("source 注入 body", ok_body, "body.source={}".format(body.get("source")))
    check("source 注入 header", ok_hdr, "X-WM-Source={}".format(hdr.get("x-wm-source")))
    check("X-API-Key 鉴权头", "x-api-key" in hdr, str(list(hdr.keys())[:5]))
except Exception as e:
    check("source 注入", False, repr(e))

# 6. SKILL.md frontmatter
bad = []
for s in slugs:
    p = os.path.join(SKILLS, s, "SKILL.md")
    txt = open(p, encoding="utf-8").read()
    if not txt.startswith("---"):
        bad.append(s + ":无frontmatter")
        continue
    fm = txt.split("---")[1]
    if "name:" not in fm or "description:" not in fm:
        bad.append(s + ":frontmatter缺字段")
check("SKILL.md frontmatter 合法", not bad, ",".join(bad[:3]))

# 6b. 付费前强制预估 + 确认闸门（确认未确认则绝不扣费）
# 取一个明确付费的 skill（公众号历史文章 ¥0.035）做验证
bad = []
for s in ("mglc-mp-history", "mglc-ch-info"):
    if s not in SLUGS:
        continue
    env = dict(os.environ)
    env["WM_API_KEY"] = "test_key_for_confirm_gate"
    script = os.path.join(SKILLS, s, "scripts", s + ".py")
    first = PRODUCTS[s]["endpoints"][0]
    # 有 key、未带 --yes：应停下并输出 WM_NEED_CONFIRM，且不得发生扣费（无 WM_CONSUMPTION）
    r = subprocess.run([PY, script, first, "url=test"], capture_output=True, text=True, env=env)
    charged = ("WM_CONSUMPTION=" in r.stdout) or ("[计费]" in r.stderr)
    if r.returncode != 0 or "WM_NEED_CONFIRM=1" not in r.stdout or charged:
        bad.append("{}:rc={} confirm={} charged={}".format(
            s, r.returncode, "WM_NEED_CONFIRM=1" in r.stdout, charged))
    # 免费端点（如存在）不要求 --yes：用 mglc-balance 验证不卡闸门
check("付费前强制预估+确认闸门（未确认绝不扣费）", not bad, "; ".join(bad[:3]))

# 6c. 免费端点无需 --yes 直接执行（用 mglc-balance 验证，但需 key，仅验证语法/流程不报错分支）
# 此处仅验证：带 --yes 的付费调用不会进入「未确认」分支
r = subprocess.run([PY, os.path.join(SKILLS, "mglc-mp-history", "scripts", "mglc-mp-history.py"),
                    "mp-account-articles", "--yes", "url=test"],
                   capture_output=True, text=True,
                   env={**os.environ, "WM_API_KEY": "test_key_for_yes"})
# 有 key + --yes 仍会因网络/鉴权失败退出（测试环境无真实网络），但不应再报「需确认」
yes_ok = "WM_NEED_CONFIRM=1" not in r.stdout
check("带 --yes 后不再卡确认闸门", yes_ok,
      "仍输出 WM_NEED_CONFIRM" if not yes_ok else "")

# 7. 底层一致性（所有 skill 的 wm_core.py 与 core 源一致）
src = open(os.path.join(HERE, "wm_core.py"), "rb").read()
diff = [s for s in slugs
        if open(os.path.join(SKILLS, s, "scripts", "wm_core.py"), "rb").read() != src]
check("底层一致（wm_core.py 完全相同）", not diff, ",".join(diff[:3]))

print("=" * 58)
for n, ok, d in results:
    print("{} {}{}".format("PASS" if ok else "FAIL", n, ("  → " + d) if d and not ok else ""))
print("=" * 58)
fails = [r for r in results if not r[1]]
print("结果：{}/{} 通过，{} 个 skill".format(len(results) - len(fails), len(results), len(slugs)))
sys.exit(0 if not fails else 1)
