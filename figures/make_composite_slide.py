# -*- coding: utf-8 -*-
"""
make_composite_slide.py — スライド用 ピンチ解析 2パネル図（ベクトルPDF出力）。
  左: 与熱・受熱複合線（実温度, ΔTmin=10K で接近）
  右: グランドコンポジットカーブ（シフト温度）
同じ温度軸で横並びにしピンチを対応させる。文字は余白に大きく・PDFで鮮明。

データ: Z:\\report_for_processdesign\\graph\\gcc_bestpoint.json
実行  : Z:\\pdh_simulator\\.venv\\Scripts\\python.exe make_composite_slide.py
出力  : composite_slide.pdf（ベクトル＝拡大しても鮮明）
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, gridspec

for _c in ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP"]:
    try:
        font_manager.findfont(_c, fallback_to_default=False)
        matplotlib.rcParams["font.family"] = _c
        break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["pdf.fonttype"] = 42      # TrueType 埋め込み（和文も鮮明）

SRC = r"Z:\report_for_processdesign\graph\gcc_bestpoint.json"
HERE = os.path.dirname(os.path.abspath(__file__))
T0 = 273.15
RED = "#c0392b"; BLUE = "#1f6fb2"; OR = "#e8821e"

d = json.load(open(SRC, encoding="utf-8"))
QH = d["Q_H_min_kW"] / 1000.0
QC = d["Q_C_min_kW"] / 1000.0
H_hot = [p[0] / 1000.0 for p in d["composite_hot"]]
T_hot = [p[1] - T0 for p in d["composite_hot"]]
H_cold = [p[0] / 1000.0 + QC for p in d["composite_cold"]]
T_cold = [p[1] - T0 for p in d["composite_cold"]]
gH = [p[1] / 1000.0 for p in d["GCC"]]
gT = [p[0] - T0 for p in d["GCC"]]
Tp = 35.8
YLIM = (-120, 700)

fig = plt.figure(figsize=(11.0, 7.8))
gs = gridspec.GridSpec(1, 2, width_ratios=[2.25, 1.0], wspace=0.05)
axL = fig.add_subplot(gs[0]); axR = fig.add_subplot(gs[1], sharey=axL)

# ============ 左: 与熱・受熱複合線 ============
axL.plot(H_hot, T_hot, color=RED, lw=3.4, solid_capstyle="round")
axL.plot(H_cold, T_cold, color=BLUE, lw=3.4, solid_capstyle="round")
axL.axhline(Tp, color="0.55", ls="--", lw=1.0)

axL.text(190, 545, "与熱複合線", color=RED, fontsize=22, fontweight="bold", ha="center")
axL.text(190, 498, "高温流れ・要冷却", color=RED, fontsize=13, ha="center")
axL.text(335, 320, "受熱複合線", color=BLUE, fontsize=22, fontweight="bold", ha="center")
axL.text(335, 277, "低温流れ・要加熱", color=BLUE, fontsize=13, ha="center")

# ピンチ・最小接近温度差
axL.annotate("", xy=(141.7, 40.8), xytext=(141.7, 30.7),
             arrowprops=dict(arrowstyle="<->", color="black", lw=1.8))
axL.annotate("最小接近温度差 10 K\n両線が最接近＝ピンチ", xy=(141.7, 35.5),
             xytext=(166, -52), fontsize=15, ha="left", va="center",
             arrowprops=dict(arrowstyle="->", color="black", lw=1.4))
# 装置注釈（軸ラベルと重ならない位置へ）
axL.annotate("脱エタン塔 凝縮器  −82 ℃", xy=(40, -82.2), xytext=(20, 62),
             fontsize=15, color=RED, ha="left",
             arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))
axL.annotate("リボイラ", xy=(185, 41.5), xytext=(250, 165),
             fontsize=15, color=BLUE, ha="center",
             arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.4))
axL.annotate("反応器予熱  〜662 ℃", xy=(360, 545), xytext=(150, 650),
             fontsize=15, color=BLUE, ha="left", va="center",
             arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.4))

axL.set_xlabel("累積エンタルピー  $H$ [MW]", fontsize=17)
axL.set_ylabel("温度  $T$ [℃]", fontsize=17)
axL.set_xlim(-15, 415); axL.set_ylim(*YLIM)
axL.tick_params(labelsize=13, direction="in", top=True)
axL.grid(True, ls=":", lw=0.6, color="black", alpha=0.28)
axL.set_title("与熱・受熱複合線  $\\Delta T_{\\min}=10$ K", fontsize=16)

# ============ 右: グランドコンポジットカーブ ============
axR.plot(gH, gT, color="black", lw=2.8)
axR.fill_betweenx(gT, 0, gH, where=[t >= Tp for t in gT], color=OR, alpha=0.18)
axR.fill_betweenx(gT, 0, gH, where=[t <= Tp for t in gT], color=BLUE, alpha=0.16)
axR.axhline(Tp, color="0.55", ls="--", lw=1.0)
axR.axvline(0, color="black", lw=0.8)

# 上＝加熱不足域（橙）, 下＝冷却不足域（青）。曲線に被らない余白へ配置。
axR.text(14, 470, "加熱不足域", color="#b5651d", fontsize=15, fontweight="bold", ha="left")
# 外部加熱 Q_H（上端, 左上の橙余白）
axR.annotate(f"加熱  $Q_H^{{\\min}}$\n= {QH:.1f} MW", xy=(QH, 655),
             xytext=(12, 600), fontsize=16, color=RED, fontweight="bold",
             ha="left", va="center",
             arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))
axR.text(14, -52, "冷却不足域", color=BLUE, fontsize=15, fontweight="bold", ha="left")
# 外部冷却 Q_C（下端, 右下の余白）
axR.annotate(f"冷却  $Q_C^{{\\min}}$\n= {QC:.1f} MW", xy=(QC, -87),
             xytext=(96, -38), fontsize=16, color=BLUE, fontweight="bold",
             ha="left", va="center",
             arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))
# ピンチ
axR.plot([0], [Tp], "o", color="black", ms=7)
axR.annotate("ピンチ", xy=(0, Tp), xytext=(52, 190), fontsize=15, ha="left",
             arrowprops=dict(arrowstyle="->", color="black", lw=1.3))

axR.set_xlabel("正味熱量  $H$ [MW]", fontsize=17)
axR.set_xlim(-6, 172)
axR.tick_params(labelsize=13, direction="in", labelleft=False)
axR.grid(True, ls=":", lw=0.6, color="black", alpha=0.28)
axR.set_title("グランドコンポジットカーブ", fontsize=16)

fig.savefig(os.path.join(HERE, "composite_slide.pdf"), bbox_inches="tight")
plt.close(fig)
print(f"[out] composite_slide.pdf  Q_H={QH:.1f} / Q_C={QC:.1f} MW (vector, 2-panel)")
