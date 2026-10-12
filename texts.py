# -*- coding: utf-8 -*-
"""灰点个人作品集 · 文字层

把所有"需要手改的界面文字"集中到 网站文字.txt，你在那个 txt 里改，
build.py 构建时读进来覆盖掉代码里的默认值。

设计原则：
  - 这个模块只做两件事：解析 txt（parse）和写回 txt（write_defaults）。
  - 回填是"精确替换值"，从不动键名、不重排、不重写整行；解析失败的键保留原值。
  - 键名是唯一标识，删掉一行 = 该键回落到代码默认值，不会报错。
"""

from pathlib import Path

TEXT_FILE = Path(__file__).resolve().parent / "网站文字.txt"

# 允许跨行的字段（简介这种长文案要能分行写）
MULTILINE_KEYS = {"bio"}

SEP = "＝"          # 全角等号，避开正文里的冒号
KEY_SEP = "："      # 全角冒号

# ─────────────────────────── 键定义 ───────────────────────────
# (键名, 所属区块, 中文说明, 默认取值的来源)
# 来源 "site:xxx" = build.py 的 SITE 字典；"sections:<key>:0/1/2" = SECTIONS；"nav:<i>" = NAV；
# "fixed:xxx" = 模板里的固定文字（由 build.py 声明默认值）

KEY_DEFS = [
    # 站点名称
    ("name_en", "站点名称", "英文名（顶栏左上、页脚、浏览器标题）", "site:name_en"),
    ("name_cn", "站点名称", "中文名（顶栏左上、页脚、关于页大标题）", "site:name_cn"),

    # 首页
    ("role", "首页", "首屏大标题", "site:role"),
    ("claim", "首页", "大标题下面的小字／副标题", "site:claim"),
    ("sec_featured", "首页", "「精选」区块的标题", "fixed:sec_featured"),
    ("sec_contact", "首页", "「联系方式」小标题", "fixed:sec_contact"),
    ("sec_archive", "首页", "「存档」小标题", "fixed:sec_archive"),

    # 顶栏导航
    ("nav_1", "顶栏导航", "第 1 项导航文字", "nav:0"),
    ("nav_2", "顶栏导航", "第 2 项导航文字", "nav:1"),
    ("nav_3", "顶栏导航", "第 3 项导航文字", "nav:2"),
    ("nav_4", "顶栏导航", "第 4 项导航文字", "nav:3"),
    ("nav_5", "顶栏导航", "第 5 项导航文字", "nav:4"),

    # 栏目
    ("sec_teardown_cn", "栏目", "「拆解案」栏目名", "sections:teardown:0"),
    ("sec_teardown_en", "栏目", "「拆解案」英文小标签", "sections:teardown:1"),
    ("sec_teardown_intro", "栏目", "「拆解案」列表页标题下的导语（可留空）", "sections:teardown:2"),
    ("sec_design_cn", "栏目", "「策划案」栏目名", "sections:design:0"),
    ("sec_design_en", "栏目", "「策划案」英文小标签", "sections:design:1"),
    ("sec_design_intro", "栏目", "「策划案」列表页标题下的导语（可留空）", "sections:design:2"),

    # 关于页
    ("about_kicker", "关于页", "关于页左上角小标签", "fixed:about_kicker"),
    ("about_bio_head", "关于页", "「简介」小标题", "fixed:about_bio_head"),
    ("about_info_head", "关于页", "「信息」小标题", "fixed:about_info_head"),
    ("about_k_direction", "关于页", "信息栏第 1 行左边的标签", "fixed:about_k_direction"),
    ("about_v_direction", "关于页", "信息栏第 1 行右边的值", "fixed:about_v_direction"),
    ("about_k_email", "关于页", "信息栏第 2 行左边的标签", "fixed:about_k_email"),
    ("about_k_wechat", "关于页", "信息栏第 3 行左边的标签", "fixed:about_k_wechat"),

    # 联系方式
    ("email", "联系方式", "邮箱（首页、页脚、关于页）", "site:email"),
    ("wechat", "联系方式", "微信（首页、页脚、关于页）", "site:wechat"),

    # 其它
    ("desc", "其它", "浏览器搜索结果里的站点描述", "site:desc"),
    ("bio", "其它", "关于页正文（可写多行 HTML，如 <p>…</p>）", "site:bio"),
]

KEYS = [k for k, *_ in KEY_DEFS]

# 页脚里「微信：」和「更新于」是固定前缀，不参与替换
FOOT_WECHAT = "微信："


def _defaults(site: dict, sections: dict, nav: list, fixed: dict) -> dict:
    """算出每个键此刻的默认值"""
    out = {}
    for key, _bk, _label, src in KEY_DEFS:
        kind, _, arg = src.partition(":")
        if kind == "site":
            out[key] = str(site.get(arg, ""))
        elif kind == "nav":
            i = int(arg)
            out[key] = nav[i][1] if i < len(nav) else ""
        elif kind == "sections":
            sec, idx = arg.split(":")
            tup = sections.get(sec, ())
            i = int(idx)
            out[key] = str(tup[i]) if i < len(tup) else ""
        elif kind == "fixed":
            out[key] = str(fixed.get(arg, ""))
        else:
            out[key] = ""
    return out


def parse(site: dict, sections: dict, nav: list, fixed: dict) -> tuple[dict, list]:
    """读取 网站文字.txt 并覆盖默认值。

    返回 (site, sections)：site 是合并后的字典，sections 是合并后的栏目元组表。
    文件不存在 → 原样返回（站照常构建，不会因为少一个 txt 就挂）。
    """
    base = _defaults(site, sections, nav, fixed)
    got = dict(base)

    if TEXT_FILE.exists():
        got.update(_read_file(base))

    merged_site = dict(site)
    for key in ("name_en", "name_cn", "role", "claim", "desc", "email", "wechat", "bio"):
        merged_site[key] = got[key]

    merged_sections = {}
    for sec in sections:
        merged_sections[sec] = (
            got[f"sec_{sec}_cn"],
            got[f"sec_{sec}_en"],
            got[f"sec_{sec}_intro"],
        )

    # 导航顺序不变，只换标签
    merged_nav = [(href, got.get(f"nav_{i}", label)) for i, (href, label) in enumerate(nav, 1)]

    merged_fixed = {
        "sec_featured": got["sec_featured"],
        "sec_contact": got["sec_contact"],
        "sec_archive": got["sec_archive"],
        "about_kicker": got["about_kicker"],
        "about_bio_head": got["about_bio_head"],
        "about_info_head": got["about_info_head"],
        "about_k_direction": got["about_k_direction"],
        "about_v_direction": got["about_v_direction"],
        "about_k_email": got["about_k_email"],
        "about_k_wechat": got["about_k_wechat"],
    }

    return merged_site, merged_sections, merged_nav, merged_fixed, got


def _read_file(base: dict) -> dict:
    """解析 txt。键名不认识、格式不对的行 → 跳过（保留默认值）。多行值缩进续行。"""
    out = {}
    lines = TEXT_FILE.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # 跳过注释、分隔线、空行
        if not stripped or stripped.startswith("#") or stripped.startswith(SEP):
            i += 1
            continue

        # 允许以「- 」或「* 」开头的列表式写法
        body = stripped[2:] if stripped[:2] in ("- ", "* ") else stripped
        if KEY_SEP not in body:
            i += 1
            continue

        raw_key, _, raw_val = body.partition(KEY_SEP)
        key = raw_key.strip()
        if key not in KEYS:
            i += 1
            continue

        val = raw_val.strip()
        value_lines = [val] if val else []

        # 多行字段：后面缩进的行接着读（空行也吃掉，直到遇到新键或区块）
        while i + 1 < len(lines):
            nxt = lines[i + 1]
            ns = nxt.strip()
            if not ns:
                # 空行：只有多行字段才继续
                if key in MULTILINE_KEYS and value_lines:
                    value_lines.append("")
                    i += 1
                    continue
                break
            if ns.startswith("#") or ns.startswith(SEP):
                break
            # 以「已知键＋全角冒号」开头的下一行 = 新键
            head = ns[2:] if ns[:2] in ("- ", "* ") else ns
            if KEY_SEP in head and head.partition(KEY_SEP)[0].strip() in KEYS:
                break
            if ns.startswith(" "):
                value_lines.append(ns)
                i += 1
                continue
            if key in MULTILINE_KEYS:
                value_lines.append(ns)
                i += 1
                continue
            break

        out[key] = "\n".join(value_lines).strip()
        i += 1
    return out


def write_defaults(site: dict, sections: dict, nav: list, fixed: dict) -> Path:
    """生成 网站文字.txt 模板（按当前值）。"""
    vals = _defaults(site, sections, nav, fixed)
    lines = [
        "# 灰点个人作品集 · 网站文字",
        "#",
        "# 改法：只改全角冒号「：」右边的内容。",
        "#   - 左边（键名）不要动，动了那一行会被忽略、回落到默认值。",
        "#   - 以 # 开头的行是说明，随便留。",
        "#   - 导语这类可以留空（冒号后什么都不写）。",
        "#   - 想改回默认值：删掉整行，或者跑一次「生成文字模板.bat」重建本文件。",
        "#   - 改完保存，双击「更新网站.bat」即可。",
        "#",
        "# 各区块共 " + str(len(KEY_DEFS)) + " 项。",
        "",
    ]
    cur_block = None
    for key, block, label, _src in KEY_DEFS:
        if block != cur_block:
            lines.append("")
            lines.append(f"{SEP * 6} {block} {SEP * 6}")
            cur_block = block
        val = vals[key].replace("\n", "\n    ")
        lines.append(f"# {label}")
        lines.append(f"{key}{KEY_SEP}{val}")
    lines.append("")
    TEXT_FILE.write_text("\n".join(lines), encoding="utf-8")
    return TEXT_FILE


def known_keys() -> list:
    return list(KEYS)
