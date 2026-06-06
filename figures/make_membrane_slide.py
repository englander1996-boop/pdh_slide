# -*- coding: utf-8 -*-
"""
make_membrane_slide.py — スライド用 膜有無比較図（形式はレポート Fig7.1 と同一、
フォント等を拡大して投影で見やすくしたもの）。

ベース: Z:\\report_for_processdesign\\graph\\make_membrane_charts.py
データ: trial #201 の Dist2 塔底(C3H6 60.7 mol%)共通フィード FUG Case A/B
  Case A (膜 + Dist3): 合計 TAC = 135.0 億円/年, Dist3 CAPEX = 702 億円
  Case B (Dist3 単体): 合計 TAC = 1624.8 億円/年, Dist3 CAPEX = 11807 億円
形式は変えない: 2パネル・対数軸・A=緑/B=赤・棒・「約X倍」注記。拡大のみ。

実行: Z:\\pdh_simulator\\.venv\\Scripts\\python.exe make_membrane_slide.py
"""

import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _cand in ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP"]:
    try:
        font_manager.findfont(_cand, fallback_to_default=False)
        matplotlib.rcParams["font.family"] = _cand
        print(f"[font] 使用フォント: {_cand}")
        break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["xtick.direction"] = "in"
matplotlib.rcParams["ytick.direction"] = "in"
matplotlib.rcParams["xtick.top"] = True
matplotlib.rcParams["ytick.right"] = True

HERE = os.path.dirname(os.path.abspath(__file__))

cases = ["Case A\n膜 + 蒸留", "Case B\n蒸留単独"]
colors = ["#55a868", "#c44e52"]   # A=緑, B=赤

tac = [135.0, 1624.8]          # 合計 TAC [億円/年]
capex = [702.0, 11807.0]       # Dist3 CAPEX [億円]

# スライド用に拡大・濃くしたフォント
F_TITLE = 21
F_LABEL = 19
F_TICK = 18
F_VAL = 26
F_ANN = 27
matplotlib.rcParams["text.color"] = "black"
matplotlib.rcParams["axes.labelcolor"] = "black"
matplotlib.rcParams["axes.edgecolor"] = "black"
matplotlib.rcParams["axes.linewidth"] = 1.4
matplotlib.rcParams["font.weight"] = "bold"


def _draw(ax, vals, ylabel, title, floor):
    bars = ax.bar(cases, vals, color=colors, width=0.64, edgecolor="black", linewidth=1.4)
    ax.set_yscale("log")
    ax.set_ylabel(ylabel, fontsize=F_LABEL, fontweight="bold")
    ax.set_title(title, fontsize=F_TITLE, fontweight="bold")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.12, f"{v:.0f}", ha="center", va="bottom",
                fontsize=F_VAL, fontweight="bold", color="black")
    ax.set_ylim(floor, vals[1] * 5.0)
    # 倍率注記は左上の空き（緑棒の上）に置き、棒と重ねない
    ax.text(0.04, 0.95, f"約 {vals[1] / vals[0]:.1f} 倍", transform=ax.transAxes,
            ha="left", va="top", fontsize=F_ANN, fontweight="bold", color="#b3201a")
    ax.tick_params(axis="both", labelsize=F_TICK, colors="black", width=1.4, length=5)
    for lab in ax.get_xticklabels():
        lab.set_fontweight("bold")


fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.3))
_draw(axes[0], tac, "合計 TAC [億円/年]", "分離サブシステムの合計 TAC", 50)
_draw(axes[1], capex, "C3 スプリッタ CAPEX [億円]", "C3 スプリッタの設備費", 100)
fig.tight_layout()
path = os.path.join(HERE, "membrane_vs_dist3_slide.png")
fig.savefig(path, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"[out] {path}")
print("完了.")
