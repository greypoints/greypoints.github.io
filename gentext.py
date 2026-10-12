# -*- coding: utf-8 -*-
"""生成/重建 网站文字.txt

用法：python gentext.py
作用：按当前 build.py 的默认值重新导出文字模板。
注意：会覆盖 网站文字.txt 里已有的修改（这是"想改回默认值"的手段）。
"""

import build as B
import texts as X

p = X.write_defaults(B.SITE, B.SECTIONS, B.NAV, B.FIXED)
print("[OK] 已生成 →", p)
print("     共", len(X.KEY_DEFS), "项")
