# -*- coding: utf-8 -*-
"""灰点个人作品集 · HTML 模板

所有页面都由这里的函数拼装；站点信息通过 site 字典传入。
不依赖任何模板引擎，纯 f-string，改样式请动 assets/style.css。
"""

from html import escape as E

# 模板固定文字的兜底默认值（正常由 build.py 的 FIXED + 网站文字.txt 提供）
_FIXED_DEFAULT = {
    "sec_featured": "精选",
    "sec_contact": "CONTACT",
    "sec_archive": "ARCHIVE",
    "about_kicker": "ABOUT",
    "about_bio_head": "简介",
    "about_info_head": "信息",
    "about_k_direction": "方向",
    "about_v_direction": "关卡 / 战斗",
    "about_k_email": "邮箱",
    "about_k_wechat": "微信",
    "doc_children_head": "子文档",
    "doc_parent_head": "所属",
}


def _f(site: dict, key: str) -> str:
    """取固定文字：优先 网站文字.txt 的值，其次模板兜底"""
    return (site.get("fixed") or {}).get(key) or _FIXED_DEFAULT.get(key, "")


def geo_layer() -> str:
    """背景装饰层：星尘点阵 + 漂移细线（纯 CSS 动效）"""
    dots = "".join(f'<i class="geo-dot gd-{n}"></i>' for n in range(1, 8))
    lines = "".join(f'<i class="geo-line gl-{n}"></i>' for n in range(1, 3))
    return f'<div class="geo" aria-hidden="true">{dots}{lines}</div>'


def nav(site: dict, active: str = "") -> str:
    """顶栏：品牌 + 导航（导航项在 build.py 的 NAV 里配，active 高亮当前栏目）"""
    links = site.get("nav") or [("", "首页")]

    def one(href: str, label: str) -> str:
        on = " on" if label == active else ""
        return f'<a class="ln{on}" href="{site["root"]}{href}">{label}</a>'

    return f"""<header class="nav">
  <div class="nav-inner">
    <a class="brand" href="{site["root"]}"><b>{E(site["name_en"])}</b> <span>/ {E(site["name_cn"])}</span></a>
    <nav class="nav-links">{"".join(one(h, l) for h, l in links)}</nav>
  </div>
</header>"""


def foot(site: dict) -> str:
    """页脚：反色收尾"""
    return f"""<footer class="foot">
  <div class="foot-inner">
    <div class="foot-brand"><b>{E(site["name_en"])}</b> / {E(site["name_cn"])}</div>
    <div class="foot-meta">
      <span>{E(site["email"])}</span>
      <span>{_f(site, "about_k_wechat")}：{E(site["wechat"])}</span>
      <span>更新于 {site["built"]}</span>
    </div>
  </div>
</footer>"""


def page(site: dict, *, title: str, nav_active: str, body: str,
         desc: str = "", extra: str = "") -> str:
    """页面外壳"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc or site["desc"])}">
<link rel="stylesheet" href="{site["root"]}assets/style.css">
<link rel="icon" href="{site["root"]}assets/favicon.svg" type="image/svg+xml">
{extra}</head>
<body>
{geo_layer()}
{nav(site, nav_active)}
{body}
{foot(site)}
<script src="{site["root"]}assets/main.js" defer></script>
</body>
</html>
"""


# ---------- 首页 ----------

def home(site: dict, featured: list, groups: list) -> str:
    """featured: [(item, index)]；groups: [(section_key, 中文名, [item, ...])]"""
    if featured:
        feat = "".join(_row(i + 1, it) for i, (it, _) in enumerate(featured))
    else:
        feat = _empty("暂无作品。")

    blocks = []
    for _, cn, items in groups:
        if not items:
            continue  # 空栏目不在首页占位；往 content/<栏目>/ 放 md 后自动出现
        # 首页在站点根目录，链接必须带栏目前缀（与列表页的 local 链接相反）
        body = "".join(_row(n, it) for n, it in enumerate(items, 1))
        blocks.append(f"""<section class="sec wrap">
  <div class="sec-head"><h2>{cn}</h2><span class="count">{len(items):02d} 篇</span></div>
  <ol class="items">{body}</ol>
</section>""")

    total = sum(len(i) for _, _, i in groups)
    tally = " · ".join(f"{cn} {len(items):02d} 篇" for _, cn, items in groups if items)
    tally_html = f" —— {tally}" if tally else ""
    body = f"""<main>
<section class="hero">
  <div class="hero-rule"></div>
  <h1 class="hero-title">{E(site["role"])}<small>{E(site["claim"])}</small></h1>
  <div class="hero-grid">
    <div>
      <h3>{_f(site, "sec_contact")}</h3>
      <p><a class="ln" href="mailto:{E(site["email"])}">{E(site["email"])}</a><br>{_f(site, "about_k_wechat")}：{E(site["wechat"])}</p>
    </div>
    <div>
      <h3>{_f(site, "sec_archive")}</h3>
      <p>共 <b class="n">{total:02d}</b> 篇作品{tally_html}</p>
    </div>
  </div>
</section>

<section class="sec wrap">
  <div class="sec-head"><h2>{_f(site, "sec_featured")}</h2><span class="count">SELECTED</span></div>
  <ol class="items">{feat}</ol>
</section>
{"".join(blocks)}
</main>"""
    return page(site, title=site.get("title_home") or f'{site["name_cn"]} {site["name_en"]} · {site["role"]}',
                nav_active="", body=body, desc=site["desc"])


# ---------- 列表页 ----------

def listing(site: dict, *, key: str, cn: str, en: str, intro: str, items: list) -> str:
    rows = "".join(_row(n, it, local=True) for n, it in enumerate(items, 1)) if items \
        else _empty("暂无内容。")
    intro_html = f"<p>{E(intro)}</p>" if intro else ""
    body = f"""<main>
<div class="page-head">
  <span class="kicker">{E(en)}</span>
  <h1>{cn}</h1>
  {intro_html}
</div>
<div class="wrap" style="padding-top:52px">
  <ol class="items">{rows}</ol>
</div>
</main>"""
    return page(site, title=f"{cn} · {site['name_cn']}", nav_active=cn, body=body,
                desc=intro or site["desc"])


# ---------- 详情页 ----------

def _toc_html(toc: list) -> str:
    """左侧目录；无标题则返回空串"""
    if not toc:
        return ""
    links = []
    for node in toc:
        links.append(f'<a class="lv{node["level"]}" href="#{node["id"]}">'
                     f'{E(_plain(node["name"]))}</a>')
        for child in node.get("children", []):
            links.append(f'<a class="lv{child["level"]}" href="#{child["id"]}">'
                         f'{E(_plain(child["name"]))}</a>')
    return ('<aside class="toc" id="toc">\n'
            '  <div class="toc-h" id="tocToggle">目录</div>\n'
            f'  <nav>{"".join(links)}</nav>\n</aside>')


def detail(site: dict, *, item: dict, html: str, toc: list,
           prev: dict | None, nxt: dict | None,
           children: list | None = None, parent: dict | None = None) -> str:
    toc_html = _toc_html(toc)

    pn = []
    if prev:
        pn.append(f'<a class="ln" href="{prev["sibling"]}">← {E(prev["title"])}</a>')
    if nxt:
        pn.append(f'<a class="ln" href="{nxt["sibling"]}">{E(nxt["title"])} →</a>')

    meta = [E(item["section_cn"]), E(item["date"] or ""),
            f'{item["chars"]:,} 字', f'约 {item["minutes"]} 分钟']
    if item.get("tag"):
        meta.append(f'<span class="tag">{E(item["tag"])}</span>')

    # 子文档 → 父文档的回指
    parent_html = ""
    if parent:
        parent_html = (f'<p class="doc-parent"><span class="k">{_f(site, "doc_parent_head")}</span>'
                       f'<a class="ln" href="{parent["sibling"]}">{E(parent["title"])}</a></p>')

    # 父文档 → 子文档清单
    kids_html = ""
    if children:
        rows = "".join(
            f'<li><a href="{c["sibling"]}">'
            f'<span class="ttl">{E(c["title"])}</span>'
            f'<span class="meta">{c["chars"]:,} 字 · {c["minutes"]} 分钟</span>'
            f"</a></li>" for c in children)
        kids_html = f"""  <section class="doc-children">
    <h3>{_f(site, "doc_children_head")}</h3>
    <ol class="items">{rows}</ol>
  </section>
"""

    body = f"""<div class="progress"><i id="progressBar"></i></div>
<main class="detail">
{toc_html}
<article class="doc">
  <div class="doc-head">
    <div class="doc-meta">{"".join(f"<span>{m}</span>" for m in meta if m)}</div>
    <h1>{E(item["title"])}</h1>
    {f'<p class="summary">{E(item["summary"])}</p>' if item.get("summary") else ""}
    {parent_html}
  </div>
  <div class="doc-body">{html}</div>
{kids_html}  <div class="doc-foot">
    <div>{pn[0] if pn else ""}</div>
    <a class="back ln" href="./">{E(item["section_en"])} 列表 ↑</a>
    <div>{pn[1] if len(pn) > 1 else ""}</div>
  </div>
</article>
</main>"""
    return page(site, title=f'{item["title"]} · {site["name_cn"]}', nav_active=item["section_cn"],
                body=body, desc=item.get("summary") or site["desc"])


# ---------- 独立页面（content/pages/*.md） ----------

def standalone(site: dict, *, pg: dict, html: str, toc: list) -> str:
    """不属于任何栏目的独立页面，例如「项目经历」"""
    toc_html = _toc_html(toc)
    cls = "detail" if toc_html else "detail no-toc"
    label = E(pg.get("label") or "")
    meta = f'<div class="doc-meta"><span>{label}</span></div>' if label else ""
    summary = f'<p class="summary">{E(pg["summary"])}</p>' if pg.get("summary") else ""
    body = f"""<div class="progress"><i id="progressBar"></i></div>
<main class="{cls}">
{toc_html}
<article class="doc">
  <div class="doc-head">
    {meta}
    <h1>{E(pg["title"])}</h1>
    {summary}
  </div>
  <div class="doc-body">{html}</div>
</article>
</main>"""
    return page(site, title=f'{pg["title"]} · {site["name_cn"]}',
                nav_active=pg["title"], body=body,
                desc=pg.get("summary") or site["desc"])


# ---------- 关于页 ----------

def about(site: dict, blocks: list) -> str:
    """blocks: [{"k": "标签", "v": "值或 HTML"}]"""
    rows = "".join(f'<li><span class="k">{E(b["k"])}</span><span>{b["v"]}</span></li>'
                   for b in blocks)
    # 「简介」正文留空 → 整块不渲染（在 build.py 的 SITE["bio"] 或 网站文字.txt 里填）
    bio = (site.get("bio") or "").strip()
    bio_html = ""
    if bio:
        bio_html = f"""  <div class="about-section">
    <h3>{_f(site, "about_bio_head")}</h3>
    {bio}
  </div>
"""
    body = f"""<main>
<div class="page-head">
  <span class="kicker">{_f(site, "about_kicker")}</span>
  <h1>{E(site["name_cn"])}</h1>
  <p>{E(site["claim"])}</p>
</div>
<div class="about" style="padding-top:48px">
{bio_html}  <div class="about-section">
    <h3>{_f(site, "about_info_head")}</h3>
    <ul class="about-list">{rows}</ul>
  </div>
</div>
</main>"""
    return page(site, title=f'关于 · {site["name_cn"]}', nav_active="关于", body=body,
                desc=site["desc"])


# ---------- 内部工具 ----------

def _row(n: int, it: dict, local: bool = False) -> str:
    """local=True 用于列表页（与详情页同目录），否则用站内根相对路径"""
    tag = f'<em>{E(it["tag"])}</em>' if it.get("tag") else ""
    href = it["sibling"] if local else it["url"]
    cls = ' class="child"' if it.get("parent") else ""
    return (
        f'<li{cls}><a href="{href}">'
        f'<span class="idx">{n:02d}</span>'
        f'<span class="ttl">{E(it["title"])}{tag}</span>'
        f'<span class="meta">{it["chars"]:,} 字 · {it["minutes"]} 分钟</span>'
        f'<span class="date">{E(it["date"] or "")}</span>'
        f"</a></li>"
    )


def _empty(msg: str) -> str:
    return f'<li class="empty">{msg}</li>'


def _plain(text: str) -> str:
    """去掉标题里的行内标记，用于目录"""
    return text.replace("**", "").replace("`", "").strip()
