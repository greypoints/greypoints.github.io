# -*- coding: utf-8 -*-
"""构建流水线的回归检查（不是单元测试，是端到端冒烟）。

做法跟真实使用一致：
  1. 从零构建 → 断言产物齐全
  2. 真的新增一篇 md → 重建 → 断言它出现在列表页和首页
  3. 删掉它 → 重建 → 断言仓库回到干净状态
  4. 校验生成页面的不变量（链接可解析、表格滚动容器、数字列/中文代码块标记）
  5. 校验 bat 文件的编码与换行（GBK + CRLF + PYTHONIOENCODING）
  6. 用 HTTP 起服务逐个抓页面（站点用绝对路径，file:// 下会丢样式）

用法： python verify.py      （全通过退出码 0）

注：输出刻意只用 ASCII，避免控制台编码把失败信息吃掉。
"""
import http.server
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
FAILS = []
CHECKS = [0]

BAT_FILES = ["本地预览.bat", "更新网站.bat", "首次部署.bat", "生成文字模板.bat"]
EXPECTED = [
    "index.html", "about.html", ".nojekyll",
    "assets/style.css", "assets/main.js", "assets/favicon.svg",
    "teardown/index.html", "design/index.html",
    "teardown/example-teardown.html", "design/example-design.html",
]

# 文字层：验证「改 txt → 重建 → 页面变」这条链路真的通
TEXT_FILE = ROOT / "网站文字.txt"
TEXT_KEYS_PROBE = ("role", "claim", "nav_4", "about_k_direction")


def check(label, ok, detail=""):
    CHECKS[0] += 1
    if ok:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILS.append(label)


def read(p):
    return Path(p).read_text(encoding="utf-8")


def build():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, "build.py"], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env)


def git_dirty():
    st = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                        capture_output=True, text=True)
    return [l for l in st.stdout.splitlines() if l.strip()]


# ── 1. 从零构建 ────────────────────────────────────────────────
print("[1] clean build from scratch")
shutil.rmtree(DOCS, ignore_errors=True)
r = build()
check("build exits 0", r.returncode == 0, r.stderr[-400:])
for rel in EXPECTED:
    check(f"artifact docs/{rel}", (DOCS / rel).exists())

# ── 2. 新增一篇文档（模拟真实使用） ─────────────────────────────
print("[2] add a new doc the way a user would")
slug = "verify-tmp"
tmp = ROOT / "content" / "teardown" / f"{slug}.md"
tmp.write_text(
    "---\ntitle: VERIFY TMP\ndate: 2026-10-12\nsummary: temp\n"
    "tag: tmp\nfeatured: true\norder: 0\n---\n\n"
    "## Section A\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n\n```\n[框] -> 测试\n```\n",
    encoding="utf-8")
r = build()
check("rebuild with new doc exits 0", r.returncode == 0, r.stderr[-400:])
check("new doc page generated", (DOCS / "teardown" / f"{slug}.html").exists())
check("new doc linked from section list", slug in read(DOCS / "teardown" / "index.html"))
check("new doc linked from homepage", slug in read(DOCS / "index.html"))

# ── 3. 生成页面的不变量 ────────────────────────────────────────
print("[3] HTML invariants")
pages = list(DOCS.rglob("*.html"))
check("page count >= 6", len(pages) >= 6, str(len(pages)))

broken = []
for page in pages:
    for href in re.findall(r'(?:href|src)="([^"#]+)"', read(page)):
        if href.startswith(("http", "mailto:", "data:")):
            continue
        target = (DOCS / href.lstrip("/")) if href.startswith("/") else (page.parent / href)
        if not Path(target).exists():
            broken.append(f"{page.name} -> {href}")
check("every internal link resolves", not broken, "; ".join(broken[:4]))

det = read(DOCS / "teardown" / "example-teardown.html")
check("tables wrapped in scroll container", det.count('class="table-scroll"') >= 2,
      str(det.count('class="table-scroll"')))
check("numeric columns marked", 'class="num"' in det)
check("cjk code block marked", 'class="cjk"' in det)
check("reading progress bar present", 'id="progressBar"' in det)
check("toc generated", 'id="toc"' in det)

idx = read(DOCS / "index.html")
check("homepage hero present", 'class="hero-title"' in idx)
check("homepage sections wrapped/aligned", idx.count('class="sec wrap"') >= 3,
      str(idx.count('class="sec wrap"')))

# 回归：首页在站点根，行链接必须带栏目前缀；列表页在栏目目录内，必须不带。
home_rows = re.findall(r'<li><a href="([^"]+)"', idx)
check("homepage row links carry section prefix",
      bool(home_rows) and all("/" in h for h in home_rows), str(home_rows[:3]))
list_rows = re.findall(r'<li><a href="([^"]+)"', read(DOCS / "teardown" / "index.html"))
check("listing row links are same-folder",
      bool(list_rows) and all("/" not in h for h in list_rows), str(list_rows[:3]))

# ── 4. bat 文件的编码与换行 ─────────────────────────────────────
print("[4] bat files: encoding + cmd-safe newlines")
for name in BAT_FILES:
    raw = (ROOT / name).read_bytes()
    try:
        text = raw.decode("gbk")
        ok, detail = True, ""
    except UnicodeDecodeError as e:
        ok, text, detail = False, "", str(e)
    check(f"{name} decodes as GBK", ok, detail)
    check(f"{name} is CRLF-only (no bare LF)", re.search(rb"(?<!\r)\n", raw) is None)
    check(f"{name} sets PYTHONIOENCODING=gbk", "PYTHONIOENCODING=gbk" in text)
    check(f"{name} has no bare chcp", "chcp" not in text.lower())
    check(f"{name} picks an interpreter", "PY=py -3" in text)

# ── 5. 文字层（网站文字.txt）────────────────────────────────────
print("[5] text layer: edit 网站文字.txt -> rebuild -> page changes")
backup = None
if TEXT_FILE.exists():
    backup = TEXT_FILE.read_text(encoding="utf-8")

    def set_key(text, key, value):
        """只改目标键那一行，其余原样"""
        out, hit = [], 0
        for ln in text.splitlines(True):
            if ln.strip().startswith(key + "："):
                out.append(f"{key}：{value}\n")
                hit += 1
            else:
                out.append(ln)
        assert hit == 1, f"{key}: matched {hit} lines"
        return "".join(out)

    probes = [("role", "家里的个人页", DOCS / "index.html", "index"),
              ("about_k_direction", "方向标", DOCS / "about.html", "about")]
    for key, value, page, label in probes:
        TEXT_FILE.write_text(set_key(backup, key, value), encoding="utf-8")
        r = build()
        ok = r.returncode == 0 and value in read(page)
        check(f"txt key '{key}' reaches {label} page", ok, r.stderr[-200:])
        TEXT_FILE.write_text(backup, encoding="utf-8")

    # 还原后必须回到原样
    r = build()
    check("restore txt + rebuild exits 0", r.returncode == 0, r.stderr[-200:])
    check("restored page drops the probe text",
          "家里的个人页" not in read(DOCS / "index.html"))

    # 容错：文件整个不存在也要能构建
    TEXT_FILE.unlink()
    r = build()
    check("build works with 网站文字.txt absent", r.returncode == 0, r.stderr[-200:])
    TEXT_FILE.write_text(backup, encoding="utf-8")

    # 键名写错的行被忽略（不能把站搞崩，也不能改到别的键）
    TEXT_FILE.write_text("not_a_key：WRONG\nclaim：只改这一行\n", encoding="utf-8")
    r = build()
    check("unknown key ignored, valid key applied",
          r.returncode == 0 and "只改这一行" in read(DOCS / "index.html")
          and "WRONG" not in read(DOCS / "index.html"), r.stderr[-200:])
    TEXT_FILE.write_text(backup, encoding="utf-8")
    r = build()
    check("final restore exits 0", r.returncode == 0, r.stderr[-200:])
else:
    check("网站文字.txt exists", False, "missing")

# ── 6. HTTP 抓页面 ─────────────────────────────────────────────
print("[6] serve docs/ over HTTP and fetch every page")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


s = socket.socket()
s.bind(("127.0.0.1", 0))
port = s.getsockname()[1]
s.close()

srv = http.server.ThreadingHTTPServer(
    ("127.0.0.1", port),
    lambda *a, **k: Quiet(*a, directory=str(DOCS), **k))
threading.Thread(target=srv.serve_forever, daemon=True).start()

for u in ["/", "/teardown/", "/design/", "/about.html",
          "/teardown/example-teardown.html", "/design/example-design.html",
          "/assets/style.css", "/assets/main.js", "/assets/favicon.svg"]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{u}", timeout=10) as resp:
            check(f"HTTP 200 {u}", resp.status == 200 and len(resp.read()) > 0)
    except Exception as e:  # noqa: BLE001
        check(f"HTTP 200 {u}", False, repr(e))
srv.shutdown()

# ── 7. 收尾：回到干净状态 ──────────────────────────────────────
print("[7] cleanup and confirm the repo returns to its committed state")
tmp.unlink()
r = build()
check("rebuild after cleanup exits 0", r.returncode == 0, r.stderr[-400:])
check("temp page gone", not (DOCS / "teardown" / f"{slug}.html").exists())
dirty = git_dirty()
check("git working tree clean after rebuild", not dirty, "; ".join(dirty[:5]))
junk = [p.name for p in ROOT.glob("_*") if p.name != "__pycache__"]
check("no leftover temp files starting with _", not junk, str(junk))
check("__pycache__ is gitignored", "__pycache__" in read(ROOT / ".gitignore"))

print()
print(f"{CHECKS[0] - len(FAILS)}/{CHECKS[0]} checks passed")
if FAILS:
    print("FAILED: " + ", ".join(FAILS))
    sys.exit(1)
print("ALL CHECKS PASSED")
