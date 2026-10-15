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
PAGES = CONTENT / "pages"   # 独立页面（如「项目经历」）
PROJECTS_SLUG = "projects"  # 首页首屏「个人项目」入口指向的独立页面 slug

# ─────────────────────────── 站点信息（改这里） ───────────────────────────

SITE = {
    "name_en": "GREYPOINT",
    "name_cn": "灰点",
    "role": "灰点的个人页",
    "claim": "我的项目与设计案",
    "desc": "灰点的个人作品集：游戏拆解案、策划案存档。",
    "email": "18272287614@163.com",
    "wechat": "Grey_spot",
    "root": "/",  # 站点根路径；若部署到子目录（如 /blog/）改成 "/blog/"
    "bio": "",  # 关于页「简介」正文；留空则整块不渲染
    "title_home": "",  # 首页浏览器标题；留空 = 自动拼「灰点 GREYPOINT · 灰点的个人页」
}

# 栏目：目录名 → (中文名, 英文标签, 列表页导语)
SECTIONS = {
    "teardown": ("拆解案", "TEARDOWN"),
    "design": ("策划案", "DESIGN DOC"),
    "study": ("学习记录", "STUDY"),
}

# 顶栏导航（顺序即显示顺序）；指向栏目目录的末尾要带 /
NAV = [
    ("", "首页"),
    ("teardown/", "拆解案"),
    ("design/", "策划案"),
    ("study/", "学习记录"),
    ("projects.html", "项目"),
    ("about.html", "关于"),
]

# 模板里的固定文字（默认值；可被 网站文字.txt 覆盖）
FIXED = {
    "sec_projects": "个人项目",  # 首页首屏「个人项目」入口的小标题
    "sec_contact": "CONTACT",
    "sec_archive": "ARCHIVE",
    "about_kicker": "ABOUT",
    "about_bio_head": "简介",
    "about_info_head": "信息",
    "about_k_direction": "方向",
    "about_v_direction": "关卡",
    "about_k_email": "邮箱",
    "about_k_wechat": "微信",
    # 父子文档（frontmatter 里的 parent 字段）
    "doc_children_head": "子文档",
    "doc_parent_head": "所属",
}


def section_meta(tup) -> tuple:
    """栏目配置允许两段（中文名 / 英文标签）或三段（再加列表页导语）"""
    cn, en = tup[0], tup[1]
    intro = tup[2] if len(tup) > 2 else ""
    return cn, en, intro


# 文字层：把 网站文字.txt 的改动合并进来（文件不存在就原样用上面的值）
import texts as _TEXTS  # noqa: E402

SITE, SECTIONS, NAV, FIXED, TEXT_VALUES = _TEXTS.parse(SITE, SECTIONS, NAV, FIXED)

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
    html = MD.convert(autolink(space_blocks(text)))
    toc = MD.toc_tokens
    html = wrap_figures(embed_media(wrap_tables(mark_numeric_cols(mark_cjk_pre(html)))))
    return html, toc


# ─────────────── 块级归一化：图片 / 图注前后补空行 ───────────────

BLOCK_STARTS = ("![", '<p class="fig-cap">')


def space_blocks(text: str) -> str:
    """图片 / 图注 / 表格都是块级元素，但 md 里常常紧贴上一行写。
    开了 nl2br 之后图片会被并进上一段，图注甚至会整条丢掉；
    表格后面紧跟的正文会被 tables 扩展当成表行吞掉。
    这里在它们前后补空行（并折叠多余空行），保证各自独立成块。"""
    lines = text.splitlines()
    out, in_fence = [], False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            out.append(ln)
            continue
        if in_fence:
            out.append(ln)
            continue
        if s.startswith(BLOCK_STARTS):
            if out and out[-1].strip():
                out.append("")
            out.append(ln)
            out.append("")
            continue
        out.append(ln)
        # 表格行之后如果不再是表格行，补一个空行，
        # 否则紧跟的正文会被 tables 扩展当成新的一行吞进表格
        if s.startswith("|"):
            nxt = next((x for x in lines[i + 1:] if x.strip()), "")
            if not nxt.strip().startswith("|"):
                out.append("")
    res = []
    for ln in out:
        if not ln.strip() and res and not res[-1].strip():
            continue
        res.append(ln)
    return "\n".join(res)


# ─────────────── 图片包成 <figure>（配合 CSS 的图注样式） ───────────────

IMG_RE = re.compile(r"<img\b[^>]*?>")
# markdown 会把独立成段的图片包进 <p>（一行写多张图时，一个 <p> 里会有多个 <img>）；
# 图注是紧随其后的 .fig-cap 段落
IMGS_GROUP = r"((?:<img\b[^>]*?>\s*)+)"
FIG_CAP_RE = re.compile(r'<p>\s*' + IMGS_GROUP + r'</p>\s*<p class="fig-cap">(.*?)</p>', re.S)
FIG_P_RE = re.compile(r"<p>\s*" + IMGS_GROUP + r"</p>", re.S)


def _figs(imgs_html: str, cap: str | None = None) -> str:
    """把一段里的若干 <img> 变成若干 <figure>；图注只挂在最后一张上"""
    imgs = IMG_RE.findall(imgs_html)
    out = []
    for i, img in enumerate(imgs):
        last = i == len(imgs) - 1
        if cap and last:
            out.append(f"<figure>{img}<figcaption>{cap}</figcaption></figure>")
        else:
            out.append(f"<figure>{img}</figure>")
    return "".join(out)


def wrap_figures(html: str) -> str:
    """正文里每张图都包一层 <figure>；紧随其后的 <p class="fig-cap"> 升级为 <figcaption>。
    这样图与说明文字成对，不会散在段落里。"""
    # 1) 图片 + 图注：整段替换，顺带把 markdown 给的 <p> 外壳去掉
    html = FIG_CAP_RE.sub(lambda m: _figs(m.group(1), m.group(2)), html)
    # 2) 独立成段的图片（无图注）
    html = FIG_P_RE.sub(lambda m: _figs(m.group(1)), html)
    # 3) 剩下的行内裸图（例如写在列表项里的）
    out, pos = [], 0
    for m in IMG_RE.finditer(html):
        before = html[:m.start()]
        if before.rfind("<figure>") > before.rfind("</figure>"):
            continue  # 已经在 figure 里了
        out.append(html[pos:m.start()])
        rest = html[m.end():]
        cm = re.match(r'\s*<p class="fig-cap">(.*?)</p>', rest, re.S)
        if cm:
            out.append(f"<figure>{m.group(0)}<figcaption>{cm.group(1)}</figcaption></figure>")
            pos = m.end() + cm.end()
        else:
            out.append(f"<figure>{m.group(0)}</figure>")
            pos = m.end()
    out.append(html[pos:])
    return "".join(out)


# ─────────────── 裸网址自动成链接 + 视频 / 可玩站点自动内嵌 ───────────────

# 行内出现的裸网址（排除已写成 Markdown 链接、尖括号、引号里的）
URL_RE = re.compile(r'(?<![\w"\'<=\(\[/])(https?://[^\s<>()\[\]"\'，。；：、）】]+)')
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def autolink(text: str) -> str:
    """把 md 里光秃秃的网址变成可点链接（Markdown 原生的 <url> 形式）。
    跳过代码块和缩进代码，避免破坏 ASCII 流程图。"""
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or line.startswith("    "):
            out.append(line)
            continue

        def wrap(m):
            url = m.group(1).rstrip(".,;:!")
            return f"<{url}>{m.group(1)[len(url):]}"

        out.append(URL_RE.sub(wrap, line))
    return "\n".join(out)


BILI_RE = re.compile(r"https?://(?:www\.|m\.)?bilibili\.com/video/(BV[0-9A-Za-z]+|av\d+)")
YT_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{6,})")
VIMEO_RE = re.compile(r"https?://(?:www\.)?vimeo\.com/(\d+)")
ITCH_RE = re.compile(r"https?://itch\.io/embed/(\d+)")
MEDIA_FILE_RE = re.compile(r"https?://\S+\.(?:mp4|webm|ogg|ogv|mov)(?:\?\S*)?$", re.I)
BLOCK_RE = re.compile(r"<(p|li)>(.*?)</\1>", re.S)
A_RE = re.compile(r'<a href="([^"]+)"[^>]*>.*?</a>', re.S)

# itch.io 作品页 → 可玩嵌入要用的 game id（取自作品页里的 data-game_id）
# 想让某个作品页变成页内可玩窗口，把「域名/作品名: id」加到这里即可；
# 或者直接在 md 里写 itch 的嵌入地址 https://itch.io/embed/<id>
ITCH_IDS = {
    "dshzsh.itch.io/azz": "2311370",
}


def _iframe(src: str, title: str, cls: str = "") -> str:
    box = f"embed {cls}".strip()
    return (f'<div class="{box}"><iframe src="{src}" title="{title}" loading="lazy" '
            f'scrolling="no" frameborder="0" allowfullscreen '
            f'allow="autoplay; fullscreen; picture-in-picture"></iframe></div>')


def embed_for(url: str) -> str | None:
    """能内嵌的地址 → 播放器 HTML；不能内嵌的返回 None（保持普通链接）"""
    if m := BILI_RE.search(url):
        vid = m.group(1)
        key = f"aid={vid[2:]}" if vid.lower().startswith("av") else f"bvid={vid}"
        return _iframe("https://player.bilibili.com/player.html?"
                       f"{key}&autoplay=0&danmaku=0&high_quality=1", "B 站视频")
    if m := YT_RE.search(url):
        return _iframe(f"https://www.youtube.com/embed/{m.group(1)}", "YouTube 视频")
    if m := VIMEO_RE.search(url):
        return _iframe(f"https://player.vimeo.com/video/{m.group(1)}", "Vimeo 视频")
    if m := ITCH_RE.search(url):
        return _iframe(f"https://itch.io/embed/{m.group(1)}", "itch.io 作品卡", cls="embed-itch")
    for host, gid in ITCH_IDS.items():
        if host in url:
            return _iframe(f"https://itch.io/embed/{gid}", "itch.io 作品卡", cls="embed-itch")
    if MEDIA_FILE_RE.match(url):
        return ('<div class="embed embed-file"><video controls preload="metadata" '
                f'src="{url.replace(chr(34), "%22")}"></video></div>')
    return None


def embed_media(html: str) -> str:
    """独立成段、或只带一句前缀的链接（段落或列表项），是视频/可嵌站点就换成播放器。
    例如「作品展示：<bilibili 链接>」→ 保留「作品展示：」+ 内嵌播放器。
    列表项保留 <li> 外壳（否则 <div> 会变成 <ul> 的直接子节点，嵌套非法）。"""
    def fix(m):
        tag, inner = m.group(1), m.group(2)
        links = A_RE.findall(inner)
        if len(links) != 1 or "<" in A_RE.sub("", inner):
            return m.group(0)
        embed = embed_for(links[0])
        if not embed:
            return m.group(0)
        prefix = A_RE.sub("", inner).strip()
        label = f'<p class="embed-label">{prefix}</p>' if prefix else ""
        if tag == "li":
            return f'<li class="embed-row">{label}{embed}</li>'
        return label + embed

    return BLOCK_RE.sub(fix, html)


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


IMG_MD_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def stats(text: str) -> tuple[int, int]:
    """(字数, 预计阅读分钟数)。图片语法（含路径与 alt）不算字数。"""
    plain = re.sub(r"```.*?```", "", text, flags=re.S)
    plain = re.sub(r"`[^`]*`", "", plain)
    plain = IMG_MD_RE.sub("", plain)
    chars = len(re.sub(r"\s+", "", TAGS_RE.sub("", plain)))
    return chars, max(1, round(chars / 400))


def count_imgs(text: str) -> int:
    return len(IMG_MD_RE.findall(text))


# ─────────────────────────── 收集内容 ───────────────────────────

def collect() -> dict:
    """扫描 content/ 下所有栏目，返回 item 列表（按 order → date 排序）"""
    items = []
    for key, tup in SECTIONS.items():
        cn, en, _ = section_meta(tup)
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
                "wide": truthy(meta.get("wide", "false")),  # 宽图模式：图片可超出阅读栏宽
                "parent": (meta.get("parent") or "").strip(),  # 父文档 slug（子文档用）
                "order": int(meta.get("order") or 999),
                "source": path, "body": body,
                "chars": chars, "minutes": minutes,
                "imgs": count_imgs(body),
                "url": f"{key}/{slug}.html",   # 站内根相对
                "sibling": f"{slug}.html",     # 同目录相对（详情页用）
            })
    _sort(items)
    return {"items": items}


def collect_pages() -> list:
    """content/pages/*.md → 独立页面（如「项目经历」），输出到 docs/<slug>.html"""
    pages = []
    if not PAGES.exists():
        return pages
    for path in sorted(PAGES.glob("*.md")):
        meta, body = parse_front(path.read_text(encoding="utf-8"))
        if truthy(meta.get("draft", "false")):
            continue
        pages.append({
            "slug": meta.get("slug") or path.stem,
            "title": meta.get("title") or path.stem,
            "label": meta.get("label", ""),
            "summary": meta.get("summary", ""),
            "body": body,
            "order": int(meta.get("order") or 999),
        })
    pages.sort(key=lambda p: (p["order"], p["slug"]))
    return pages


def _sort(items: list) -> None:
    """栏目顺序 → order 升序 → date 倒序（无 date 的排后面）；
    再把子文档（parent 指向本栏目内某篇）紧跟在父文档后面。"""
    rank = {k: i for i, k in enumerate(SECTIONS)}
    items.sort(key=lambda it: (
        rank.get(it["section"], 99), it["order"], _neg_date(it["date"]), it["title"]))

    by_slug = {it["slug"]: it for it in items}
    out, placed = [], set()
    for it in items:
        if it["slug"] in placed:
            continue
        # 子文档不单独出现，等父文档带它出来
        if it["parent"] and it["parent"] in by_slug:
            continue
        out.append(it)
        placed.add(it["slug"])
        for kid in items:
            if kid["parent"] == it["slug"] and kid["slug"] not in placed:
                out.append(kid)
                placed.add(kid["slug"])
    # 兜底：parent 指向不存在的 slug（或跨栏目）→ 当普通文档排在最后
    for it in items:
        if it["slug"] not in placed:
            out.append(it)
            placed.add(it["slug"])
    items[:] = out


def children_of(items: list, slug: str) -> list:
    return [x for x in items if x["parent"] == slug]


def parent_of(items: list, it: dict):
    if not it["parent"]:
        return None
    for x in items:
        if x["slug"] == it["parent"]:
            return x
    return None


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
    # 文章配图（assets/img/ 存在才拷，没有就跳过）
    img_src = ROOT / "assets" / "img"
    if img_src.is_dir():
        shutil.copytree(img_src, OUT / "assets" / "img")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")  # 禁用 Jekyll 处理

    site = dict(SITE, built=date.today().isoformat(), nav=NAV, fixed=FIXED)
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
            children=children_of(items, it["slug"]),
            parent=parent_of(items, it),
        )
        (OUT / it["section"] / f'{it["slug"]}.html').write_text(page, encoding="utf-8")

    # 独立页面（content/pages/*.md）
    pages = collect_pages()
    for pg in pages:
        html, toc = render_md(pg["body"])
        (OUT / f'{pg["slug"]}.html').write_text(
            T.standalone(site, pg=pg, html=html, toc=toc), encoding="utf-8")

    # 列表页
    groups = []
    for key, tup in SECTIONS.items():
        cn, en, intro = section_meta(tup)
        mine = [x for x in items if x["section"] == key]
        groups.append((key, cn, mine))
        (OUT / key / "index.html").write_text(
            T.listing(site, key=key, cn=cn, en=en, intro=intro, items=mine), encoding="utf-8")

    # 首页：首屏多一个「个人项目」入口，指向 content/pages/ 里的那一页
    proj_page = next((p for p in pages if p["slug"] == PROJECTS_SLUG), None)
    (OUT / "index.html").write_text(
        T.home(site, groups, proj_page), encoding="utf-8")

    # 关于页
    about_blocks = [
        {"k": FIXED["about_k_direction"], "v": FIXED["about_v_direction"]},
        {"k": FIXED["about_k_email"], "v": f'<a href="mailto:{SITE["email"]}">{SITE["email"]}</a>'},
        {"k": FIXED["about_k_wechat"], "v": SITE["wechat"]},
    ]
    (OUT / "about.html").write_text(T.about(site, about_blocks), encoding="utf-8")

    print(f"[OK] 构建完成 → {OUT}")
    print(f"     作品 {len(items)} 篇：" + "、".join(f'{x["section_cn"]}·{x["title"]}' for x in items))


if __name__ == "__main__":
    build()
