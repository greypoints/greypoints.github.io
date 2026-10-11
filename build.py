#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""灰点个人作品集 · 静态站构建脚本

把 content/ 下的 Markdown 编译成 docs/ 下的纯静态 HTML，可直接推送到 GitHub Pages。

用法：
    python build.py

新增作品：
    1. 写一个 .md 放进 content/teardown/ 或 content/design/
    2. 文件开头加 frontmatter（见 使用说明.md）
    3. 重跑 python build.py
"""

import re
import shutil
from datetime import date
from pathlib import Path

import markdown

import templates as T

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"

# ─────────────────────────── 站点信息（改这里） ───────────────────────────

SITE = {
    "name_en": "GREYPOINT",
    "name_cn": "灰点",
    "role": "游戏策划",
    "claim": "关卡 / 战斗方向 —— 这里存放我的拆解案与策划案。",
    "desc": "灰点的个人作品集：游戏关卡与战斗方向的拆解案、策划案存档。",
    "email": "1255893073@qq.com",
    "wechat": "（待填）",
    "root": "/",  # 站点根路径；若部署到子目录（如 /blog/）改成 "/blog/"
    "bio": "<p>【待改写】这里写一段自我介绍：你的方向、做过什么、在找什么样的机会。"
           "三四句即可，不要形容词堆砌。</p>",
}

# 栏目：目录名 → (中文名, 英文标签, 列表页导语)
SECTIONS = {
    "teardown": ("拆解案", "TEARDOWN", "把一款游戏拆到能复刻的程度：核心循环、系统构成、关卡节奏、感官反馈。"),
    "design": ("策划案", "DESIGN DOC", "自己设计的方案：玩法结构、数值框架、关卡提案与实现取舍。"),
}

FEATURED_LIMIT = 3  # 首页精选条数

# ─────────────────────────── frontmatter ───────────────────────────

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_front(text: str) -> tuple[dict, str]:
    """解析 --- key: value --- 头，返回 (meta, 正文)"""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        key, val = line.split(":", 1)
        val = val.strip().strip('"').strip("'")
        meta[key.strip().lower()] = val
    return meta, text[m.end():]


def truthy(val) -> bool:
    return str(val).strip().lower() in {"true", "yes", "1", "y", "是"}


# ─────────────────────────── Markdown 渲染 ───────────────────────────

MD = markdown.Markdown(extensions=[
    "tables", "fenced_code", "toc", "attr_list", "sane_lists", "nl2br", "md_in_html",
], extension_configs={"toc": {"permalink": False}})

PRE_RE = re.compile(r"<pre><code[^>]*>(.*?)</code></pre>", re.S)
CJK_RE = re.compile(r"[\u3400-\u9fff\u3000-\u303f\uff00-\uffef]")
TABLE_RE = re.compile(r"<table>.*?</table>", re.S)
TR_RE = re.compile(r"<tr>.*?</tr>", re.S)
CELL_RE = re.compile(r"<t[dh][^>]*>.*?</t[dh]>", re.S)
NUMERIC_RE = re.compile(r"^[-+]?[¥$]?\d[\d,.\s%×xX/+-]*$")
TAGS_RE = re.compile(r"<[^>]+>")


def render_md(text: str):
    """渲染 Markdown → (html, toc 结构)"""
    MD.reset()
    html = MD.convert(text)
    toc = MD.toc_tokens
    html = wrap_tables(mark_numeric_cols(mark_cjk_pre(html)))
    return html, toc


def wrap_tables(html: str) -> str:
    """表格套一层横向滚动容器，窄屏下才不会被撑破布局"""
    return html.replace("<table>", '<div class="table-scroll"><table>').replace(
        "</table>", "</table></div>")


def mark_cjk_pre(html: str) -> str:
    """代码块里含中文时改用中文等宽字体，否则 ASCII 图框线会错位"""
    def fix(m):
        if CJK_RE.search(m.group(1)):
            return m.group(0).replace("<pre>", '<pre class="cjk">', 1)
        return m.group(0)
    return PRE_RE.sub(fix, html)


def mark_numeric_cols(html: str) -> str:
    """整列都是数字的表，该列右对齐 + 等宽（数字对齐是表格可读性的关键）"""
    def fix_table(m):
        table = m.group(0)
        rows = TR_RE.findall(table)
        if len(rows) < 2:
            return table
        width = max((len(CELL_RE.findall(r)) for r in rows), default=0)
        body = [CELL_RE.findall(r) for r in rows[1:]]
        num_cols = set()
        for col in range(width):
            cells = [clean(t) for c in body for t in [c[col]] if col < len(c)]
            cells = [c for c in cells if c]
            if cells and sum(bool(NUMERIC_RE.match(c)) for c in cells) / len(cells) >= 0.7:
                num_cols.add(col)
        if not num_cols:
            return table
        pieces = re.split(r"(<tr>.*?</tr>)", table, flags=re.S)
        out = []
        for piece in pieces:
            if not piece.startswith("<tr>"):
                out.append(piece)
                continue
            idx = [-1]

            def add_class(mm):
                idx[0] += 1
                if idx[0] in num_cols:
                    return re.sub(r"^<(t[dh])", r'<\1 class="num"', mm.group(0), count=1)
                return mm.group(0)

            out.append(CELL_RE.sub(add_class, piece))
        return "".join(out)

    return TABLE_RE.sub(fix_table, html)


def clean(cell_html: str) -> str:
    return re.sub(r"\s+", " ", TAGS_RE.sub("", cell_html)).strip()


def stats(text: str) -> tuple[int, int]:
    """(字数, 预计阅读分钟数)"""
    plain = re.sub(r"```.*?```", "", text, flags=re.S)
    plain = re.sub(r"`[^`]*`", "", plain)
    chars = len(re.sub(r"\s+", "", TAGS_RE.sub("", plain)))
    return chars, max(1, round(chars / 400))


# ─────────────────────────── 收集内容 ───────────────────────────

def collect() -> dict:
    """扫描 content/ 下所有栏目，返回 item 列表（按 order → date 排序）"""
    items = []
    for key, (cn, en, _) in SECTIONS.items():
        folder = CONTENT / key
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            meta, body = parse_front(raw)
            if truthy(meta.get("draft", "false")):
                continue
            chars, minutes = stats(body)
            slug = meta.get("slug") or path.stem
            items.append({
                "section": key, "section_cn": cn, "section_en": en,
                "slug": slug,
                "title": meta.get("title") or path.stem,
                "date": meta.get("date", ""),
                "summary": meta.get("summary", ""),
                "tag": meta.get("tag", ""),
                "featured": truthy(meta.get("featured", "false")),
                "order": int(meta.get("order") or 999),
                "source": path, "body": body,
                "chars": chars, "minutes": minutes,
                "url": f"{key}/{slug}.html",   # 站内根相对
                "sibling": f"{slug}.html",     # 同目录相对（详情页用）
            })
    _sort(items)
    return {"items": items}


def _sort(items: list) -> None:
    """栏目顺序 → order 升序 → date 倒序（无 date 的排后面）"""
    rank = {k: i for i, k in enumerate(SECTIONS)}
    items.sort(key=lambda it: (
        rank.get(it["section"], 99), it["order"], _neg_date(it["date"]), it["title"]))


def _neg_date(d: str) -> str:
    return "".join(chr(255 - ord(c)) if c.isdigit() else c for c in d) or "~"


# ─────────────────────────── 生成 ───────────────────────────

def build() -> None:
    data = collect()
    items = data["items"]
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)

    shutil.copy2(ROOT / "assets" / "style.css", OUT / "assets" / "style.css")
    shutil.copy2(ROOT / "assets" / "main.js", OUT / "assets" / "main.js")
    shutil.copy2(ROOT / "assets" / "favicon.svg", OUT / "assets" / "favicon.svg")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")  # 禁用 Jekyll 处理

    site = dict(SITE, built=date.today().isoformat())
    for key in SECTIONS:
        (OUT / key).mkdir(exist_ok=True)

    # 详情页
    for idx, it in enumerate(items):
        same = [x for x in items if x["section"] == it["section"]]
        pos = same.index(it)
        html, toc = render_md(it["body"])
        page = T.detail(
            site, item=it, html=html, toc=toc,
            prev=same[pos - 1] if pos > 0 else None,
            nxt=same[pos + 1] if pos + 1 < len(same) else None,
        )
        (OUT / it["section"] / f'{it["slug"]}.html').write_text(page, encoding="utf-8")

    # 列表页
    groups = []
    for key, (cn, en, intro) in SECTIONS.items():
        mine = [x for x in items if x["section"] == key]
        groups.append((key, cn, mine))
        (OUT / key / "index.html").write_text(
            T.listing(site, key=key, cn=cn, en=en, intro=intro, items=mine), encoding="utf-8")

    # 首页（精选：featured 优先，不足则用最新补齐）
    chosen = [x for x in items if x["featured"]][:FEATURED_LIMIT]
    if len(chosen) < FEATURED_LIMIT:
        chosen += [x for x in items if x not in chosen][:FEATURED_LIMIT - len(chosen)]
    (OUT / "index.html").write_text(
        T.home(site, [(x, i) for i, x in enumerate(chosen)], groups), encoding="utf-8")

    # 关于页
    about_blocks = [
        {"k": "方向", "v": SITE["role"] + " · 关卡 / 战斗"},
        {"k": "邮箱", "v": f'<a href="mailto:{SITE["email"]}">{SITE["email"]}</a>'},
        {"k": "微信", "v": SITE["wechat"]},
    ]
    (OUT / "about.html").write_text(T.about(site, about_blocks), encoding="utf-8")

    print(f"[OK] 构建完成 → {OUT}")
    print(f"     作品 {len(items)} 篇：" + "、".join(f'{x["section_cn"]}·{x["title"]}' for x in items))


if __name__ == "__main__":
    build()
