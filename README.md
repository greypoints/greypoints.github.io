# 灰点作品集

游戏策划（关卡 / 战斗方向）的作品集网站，存放拆解案与策划案。

线上地址：https://greypoints.github.io

## 怎么用

看 [使用说明.md](使用说明.md)。

一句话版：把 md 丢进 `content/teardown/` 或 `content/design/`，双击 `更新网站.bat`。

## 构建与自检

```
python build.py     # md → docs/（静态 HTML）
python verify.py    # 端到端冒烟：真加一篇 md 再删掉，检查产物/链接/编码/HTTP
```

`verify.py` 会在 `content/teardown/` 里临时建一篇文档、重建、断言它出现在首页和列表页，然后删掉并确认仓库回到干净状态。改完构建逻辑跑一遍，比肉眼翻页面可靠。

## 技术

纯静态：Markdown → Python 构建 → HTML，托管在 GitHub Pages。无框架无依赖（只需要 `markdown` 库）。
