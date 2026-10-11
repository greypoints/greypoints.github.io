# -*- coding: utf-8 -*-
"""灰点个人作品集 · HTML 模板

所有页面都由这里的函数拼装；站点信息通过 site 字典传入。
不依赖任何模板引擎，纯 f-string，改样式请动 assets/style.css。
"""

from html import escape as E


def geo_layer() -> str:
    """背景装饰层：星尘点阵 + 漂移细线（纯 CSS 动效）"""
    dots = "".join(f'<i class="geo-dot gd-{n}"></i>' for n in range(1, 8))
    lines = "".join(f'<i class="geo-line gl-{n}"></i>' for n in range(1, 3))
    return f'<div class="geo" aria-hidden="true">{dots}{lines}</div>'


def nav(site: dict, active: str = "") -> str:
    """顶栏：品牌 + 导航（active 高亮当前栏目）"""
    links = [("", "首页"), ("teardown/", "拆解案"), ("design/", "策划案"), ("about.html", "关于")]

    def one(href: str, label: str) -> str:
        item = f'<a class="ln{" on" if label == active else ""}" href="{site["root"]}{href}">{label}</a>'
        return item

    return f"""<header class="nav">
  <div class="nav-inner">
    <a class="brand" href="{site["root"]}"><b>GREYPOINT</b> <span>/ 灰点</span></a>
    <nav class="nav-links">{"".join(one(h, l) for h, l in links)}</nav>
  </div>
</header>"""


def foot(site: dict) -> str:
    """页脚：反色收尾"""
    return f"""<footer class="foot">
  <div class="foot-inner">
    <div class="foot-brand"><b>GREYPOINT</b> / 灰点</div>
    <div class="foot-meta">
      <span>{E(site["email"])}</span>
      <span>微信：{E(site["wechat"])}</span>
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
        feat = _empty("还没有作品。<code>content/</code> 里放第一篇 md 就会出现在这里。")

    blocks = []
    for _, cn, items in groups:
        # 首页在站点根目录，链接必须带栏目前缀（与列表页的 local 链接相反）
        body = "".join(_row(n, it) for n, it in enumerate(items, 1)) if items \
            else _empty("暂无内容。")
        blocks.append(f"""<section class="sec wrap">
  <div class="sec-head"><h2>{cn}</h2><span class="count">{len(items):02d} 篇</span></div>
  <ol class="items">{body}</ol>
</section>""")

    total = sum(len(i) for _, _, i in groups)
    body = f"""<main>
<section class="hero">
  <div class="hero-rule"></div>
  <h1 class="hero-title">{E(site["role"])}<small>{E(site["claim"])}</small></h1>
  <div class="hero-grid">
    <div>
      <h3>CONTACT</h3>
      <p><a class="ln" href="mailto:{E(site["email"])}">{E(site["email"])}</a><br>微信：{E(site["wechat"])}</p>
    </div>
    <div>
      <h3>ARCHIVE</h3>
      <p>共 <b class="n">{total:02d}</b> 篇作品 —— 拆解案 {len(groups[0][2]):02d} 篇 · 策划案 {len(groups[1][2]):02d} 篇</p>
    </div>
  </div>
</section>

<section class="sec wrap">
  <div class="sec-head"><h2>精选</h2><span class="count">SELECTED</span></div>
  <ol class="items">{feat}</ol>
</section>
{"".join(blocks)}
</main>"""
    return page(site, title=f'{site["name_cn"]} {site["name_en"]} · {site["role"]}',
                nav_active="", body=body, desc=site["claim"])


# ---------- 列表页 ----------

def listing(site: dict, *, key: str, cn: str, en: str, intro: str, items: list) -> str:
    rows = "".join(_row(n, it, local=True) for n, it in enumerate(items, 1)) if items \
        else _empty(f'暂无内容。把 md 放进 <code>content/{key}/</code> 后重跑构建脚本即可。')
    body = f"""<main>
<div class="page-head">
  <span class="kicker">{E(en)}</span>
  <h1>{cn}</h1>
  <p>{E(intro)}</p>
</div>
<div class="wrap" style="padding-top:52px">
  <ol class="items">{rows}</ol>
</div>
</main>"""
    return page(site, title=f"{cn} · {site['name_cn']}", nav_active=cn, body=body, desc=intro)


# ---------- 详情页 ----------

def detail(site: dict, *, item: dict, html: str, toc: list,
           prev: dict | None, nxt: dict | None) -> str:
    toc_html = ""
    if toc:
        links = []
        for node in toc:
            links.append(f'<a class="lv{node["level"]}" href="#{node["id"]}">{E(_plain(node["name"]))}</a>')
            for child in node.get("children", []):
                links.append(f'<a class="lv{child["level"]}" href="#{child["id"]}">'
                             f'{E(_plain(child["name"]))}</a>')
        toc_html = f"""<aside class="toc" id="toc">
  <div class="toc-h" id="tocToggle">目录</div>
  <nav>{"".join(links)}</nav>
</aside>"""

    pn = []
    if prev:
        pn.append(f'<a class="ln" href="{prev["sibling"]}">← {E(prev["title"])}</a>')
    if nxt:
        pn.append(f'<a class="ln" href="{nxt["sibling"]}">{E(nxt["title"])} →</a>')

    meta = [E(item["section_cn"]), E(item["date"] or ""),
            f'{item["chars"]:,} 字', f'约 {item["minutes"]} 分钟']
    if item.get("tag"):
        meta.append(f'<span class="tag">{E(item["tag"])}</span>')

    body = f"""<div class="progress"><i id="progressBar"></i></div>
<main class="detail">
{toc_html}
<article class="doc">
  <div class="doc-head">
    <div class="doc-meta">{"".join(f"<span>{m}</span>" for m in meta if m)}</div>
    <h1>{E(item["title"])}</h1>
    {f'<p class="summary">{E(item["summary"])}</p>' if item.get("summary") else ""}
  </div>
  <div class="doc-body">{html}</div>
  <div class="doc-foot">
    <div>{pn[0] if pn else ""}</div>
    <a class="back ln" href="./">{E(item["section_en"])} 列表 ↑</a>
    <div>{pn[1] if len(pn) > 1 else ""}</div>
  </div>
</article>
</main>"""
    return page(site, title=f'{item["title"]} · {site["name_cn"]}', nav_active=item["section_cn"],
                body=body, desc=item.get("summary") or item["title"])


# ---------- 关于页 ----------

def about(site: dict, blocks: list) -> str:
    """blocks: [{"k": "标签", "v": "值或 HTML"}]"""
    rows = "".join(f'<li><span class="k">{E(b["k"])}</span><span>{b["v"]}</span></li>'
                   for b in blocks)
    body = f"""<main>
<div class="page-head">
  <span class="kicker">ABOUT</span>
  <h1>{E(site["name_cn"])}</h1>
  <p>{E(site["claim"])}</p>
</div>
<div class="about" style="padding-top:48px">
  <div class="about-section">
    <h3>简介</h3>
    {site["bio"]}
  </div>
  <div class="about-section">
    <h3>信息</h3>
    <ul class="about-list">{rows}</ul>
  </div>
</div>
</main>"""
    return page(site, title=f'关于 · {site["name_cn"]}', nav_active="关于", body=body,
                desc=site["claim"])


# ---------- 内部工具 ----------

def _row(n: int, it: dict, local: bool = False) -> str:
    """local=True 用于列表页（与详情页同目录），否则用站内根相对路径"""
    tag = f'<em>{E(it["tag"])}</em>' if it.get("tag") else ""
    href = it["sibling"] if local else it["url"]
    return (
        f'<li><a href="{href}">'
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
