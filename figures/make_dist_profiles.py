# -*- coding: utf-8 -*-
"""
make_dist_profiles.py — 蒸留3塔の段プロファイル（組成・温度）をスライド用に作図。
データ: Z:\\pdh_simulator\\monitor\\prof_dist{1,2,3}.csv（HYSYS, 段1=塔頂→末尾=塔底）。
形式: 内向き目盛り(上下左右)・グリッドなし・和文。x軸=実段数（長さの違いも見せる）。
実行: Z:\\pdh_simulator\\.venv\\Scripts\\python.exe make_dist_profiles.py
"""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _c in ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP"]:
    try:
        font_manager.findfont(_c, fallback_to_default=False)
        matplotlib.rcParams["font.family"] = _c; break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["xtick.direction"] = "in"
matplotlib.rcParams["ytick.direction"] = "in"
matplotlib.rcParams["xtick.top"] = True
matplotlib.rcParams["ytick.right"] = True
matplotlib.rcParams["font.weight"] = "bold"
matplotlib.rcParams["axes.linewidth"] = 1.3

SRC = r"Z:\pdh_simulator\monitor"
HERE = os.path.dirname(os.path.abspath(__file__))

# (csv, 軽キー列, 色, 凡例)
COLS = [
    ("prof_dist1.csv", "x_C3H8", "#1F6FC4", r"脱ブタン塔  $\mathrm{C_3H_8}$"),
    ("prof_dist2.csv", "x_C2H6", "#E8821E", r"脱エタン塔  $\mathrm{C_2H_6}$"),
    ("prof_dist3.csv", "x_C3H6", "#C0392B", r"C3 スプリッタ  $\mathrm{C_3H_6}$"),
]

def load(fn, xcol):
    with open(os.path.join(SRC, fn), encoding="utf-8") as fh:
        r = list(csv.DictReader(fh))
    # CSV は N+2 段（凝縮器＋N＋リボイラ）。両端を落として内部 N 段に揃える
    r = r[1:-1]
    st = list(range(1, len(r) + 1))
    x  = [float(row[xcol]) if row[xcol] not in ("", None) else float("nan") for row in r]
    T  = [float(row["T_C"]) for row in r]
    return st, x, T

FL, FT, FK, FTT = 14, 17, 16, 21   # label / tick / legend / title
LBL = "black"                      # 軸ラベルは小さめ・黒
fig, (axc, axt) = plt.subplots(1, 2, figsize=(10.6, 3.62))

for fn, xc, col, lab in COLS:
    st, x, T = load(fn, xc)
    lw = 3.4 if "C3" in lab else 2.2     # C3 スプリッタを強調
    z  = 5 if "C3" in lab else 3
    axc.plot(st, x, color=col, lw=lw, label=lab, zorder=z)
    axt.plot(st, T, color=col, lw=lw, label=lab, zorder=z)

axc.set_title("段ごとの組成", fontsize=FTT, fontweight="bold")
axt.set_title("段ごとの温度", fontsize=FTT, fontweight="bold")
axc.set_xlabel("段　塔頂 1 → 塔底", fontsize=FL, fontweight="normal", color=LBL)
axc.set_ylabel("軽キー 液組成 $x$", fontsize=FL, fontweight="normal", color=LBL)
axc.set_ylim(0, 1.02)
axc.legend(fontsize=FK, frameon=False, loc="center right")
axc.tick_params(labelsize=FT, width=1.3, length=5, colors="black")

axt.set_xlabel("段　塔頂 1 → 塔底", fontsize=FL, fontweight="normal", color=LBL)
axt.set_ylabel("温度 [$^\\circ$C]", fontsize=FL, fontweight="normal", color=LBL)
axt.tick_params(labelsize=FT, width=1.3, length=5, colors="black")

fig.tight_layout(w_pad=3.0)
out = os.path.join(HERE, "dist_profiles.png")
fig.savefig(out, dpi=300, bbox_inches="tight")
plt.close(fig)
print("[out]", out)
