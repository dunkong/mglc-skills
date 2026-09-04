# -*- coding: utf-8 -*-
"""从 products.json / endpoints.json 生成发布目录 README、manifest.json、.gitignore。"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)  # mglc-skills/

products = json.load(open(os.path.join(BASE, "products.json"), encoding="utf-8"))
ep_meta = json.load(open(os.path.join(BASE, "endpoints.json"), encoding="utf-8"))
ep_map = {e["key"]: e for e in ep_meta["endpoints"]}

def ep_info(key):
    e = ep_map.get(key, {})
    return {"key": key, "name": e.get("name", key), "price": e.get("price", 0.0)}

skills = []
for it in products:
    skills.append({
        "slug": it["slug"],
        "name": it["name"],
        "stage": it.get("stage", ""),
        "when": it.get("when", ""),
        "desc": it.get("desc", ""),
        "all": it.get("all", False),
        "endpoints": [ep_info(k) for k in it.get("endpoints", [])],
        "path": "skills/" + it["slug"],
    })

manifest = {
    "platform": "曼格云 (api.we-media.cn)",
    "official_site": "https://api.we-media.cn",
    "base": "wm_core.py (shared)",
    "count": len(skills),
    "note": "抖音相关与余额查询未纳入矩阵（抖音先不上；余额能力保留在每次付费调用回告）。",
    "skills": skills,
}
with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

# ---- README ----
rows = []
for s in skills:
    if s.get("all"):
        eps = "全部接口（32 个，详见各专项 skill）"
    else:
        eps = "、".join(e["name"] for e in s["endpoints"])
    rows.append("| {name} | `{slug}` | {stage} | {eps} |".format(
        name=s["name"], slug=s["slug"], stage=s["stage"], eps=eps))

table = "\n".join(rows)

readme = f"""# 曼格云 Skill 矩阵（微信生态数据 API 技能包）

> 官网：https://api.we-media.cn ｜ 共 **{len(skills)}** 个 skill ｜ 底层统一底座 `wm_core.py` ｜ 付费前强制预估费用
>
> 商业模式：**skill 是 API 获客前端，收入来自按调用量计费**（官网充值，不接 SkillPay）。

## 一句话说明

每个 `skills/<slug>/` 是一个独立、可直接上架的 skill（含 `SKILL.md` + `scripts/`）。
用户无 Key 时引导去官网创建；所有付费接口调用前自动打印费用预估，需 `--yes` 确认才扣费；
失败 / 超限接口费用自动退回（已用真实 Key 全量实测验证）。

## 技能目录（{len(skills)} 个）

| 名称 | slug | 定位 | 覆盖接口 |
|------|------|------|----------|
{table}

## 怎么上架到 skillhub / clawhub

每个 skill 目录即为一个独立发布单元，逐个上传即可：

```bash
# 以「视频号找号」为例
# 在 skillhub / clawhub 的发布入口选择 skills/mglc-ch-finder/ 目录发布
skills/
├── mglc-api/                # 平台入口（全接口兜底）
├── mglc-ch-finder/          # 视频号找号
├── mglc-vision/             # 视频内容理解官
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
"""

with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

gitignore = """# 运行时缓存与产物
*/scripts/.cache/
*/__pycache__/
__pycache__/
*.pyc

# 运行时生成的输出（用户执行 skill 时产生）
*_2026*.md
*_2026*.xlsx

# 用户本地密钥
config.json
*.local.json

# 系统
.DS_Store
Thumbs.db
"""
with open(os.path.join(ROOT, ".gitignore"), "w", encoding="utf-8") as f:
    f.write(gitignore)

print("已生成: manifest.json, README.md, .gitignore")
print("skill 数:", len(skills))
