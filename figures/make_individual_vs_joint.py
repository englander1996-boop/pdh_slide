# -*- coding: utf-8 -*-
r"""make_individual_vs_joint.py — スライド15用「個別最適化の破綻 → 同時最適化が必要」。

C3 スプリッタを上流の膜と切り離して単独で最適設計すると破綻し、膜と同時に設計して
初めて成立することを対比で示す。装置境界を個別に最適化できない = 23 変数を一括で
最適化する必要がある、という主張の決定打。

実データ出典 (trial #201 の Dist2 塔底 C3H6 60.7 mol% を共通フィードに FUG で再計算):
  Z:\pdh_simulator\tools\_membrane_vs_dist3_trial201.py  (2026-06-07 実行で確認)
  個別 (膜なし, Case B): C3塔 N=200・塔高156.0m・径16.65m・CAPEX 11807.2億円・
                          サブシステムTAC 1624.8億円/年   (フィード C3H6 60.7 mol%)
  同時 (膜あり, Case A): C3塔 N=117・塔高 94.2m・径 9.15m・CAPEX  701.9億円・
                          膜+塔 サブシステムTAC 135.0億円/年 (Dist3 フィード C3H6 98.6 mol%)
  比: TAC 約 1/12、C3塔 CAPEX 約 1/17。

実行: Z:\pdh_simulator\.venv\Scripts\python.exe make_individual_vs_joint.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _cand in ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP", "HaranoAjiGothic"]:
    try:
        font_manager.findfont(_cand, fallback_to_default=False)
        matplotlib.rcParams["font.family"] = _cand
        print(f"[font] {_cand}")
        break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["xtick.direction"] = "in"
matplotlib.rcParams["ytick.direction"] = "in"
matplotlib.rcParams["ytick.right"] = True

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 検証済み実データ ----
RED, GRN, DKGRN = "#C0392B", "#1FB24D", "#0a7a32"
labels = ["個別\n膜なし", "同時\n膜あり"]
colors = [RED, GRN]
tac = [1624.8, 135.0]      # 分離サブシステム TAC [億円/年]

# 単一パネル (スライド右下): 分離サブシステム TAC で 1/12 を見せる。
# 物理スペック(200段/156m 等)はスライド側キャプションに置き、図はプロットを拡大。
fig, ax = plt.subplots(figsize=(4.6, 3.7))
x = np.arange(2)
bars = ax.bar(x, tac, color=colors, width=0.58, edgecolor="white", linewidth=0.6)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=13.5)
ax.set_ylabel("分離 TAC [億円/年]", fontsize=13)
ax.set_ylim(0, tac[0] * 1.16)
for b, v in zip(bars, tac):
    ax.text(b.get_x() + b.get_width() / 2, v + tac[0] * 0.02,
            f"{v:,.0f}", ha="center", va="bottom", fontsize=15, fontweight="bold")
ax.annotate("約 1/12", xy=(1, tac[1]), xytext=(0.52, tac[0] * 0.52),
            ha="center", fontsize=16, fontweight="bold", color=RED)
ax.tick_params(axis="y", labelsize=11.5)
fig.tight_layout(pad=0.3)
out = os.path.join(HERE, "fig_individual_vs_joint.pdf")
fig.savefig(out, bbox_inches="tight", pad_inches=0.03)
print("wrote", out)
