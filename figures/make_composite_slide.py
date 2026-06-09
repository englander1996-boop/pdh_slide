# -*- coding: utf-8 -*-
"""
make_composite_slide.py — スライド用 ピンチ解析 2パネル図（ベクトルPDF出力）。
  左: 与熱・受熱複合線（実温度, ΔTmin=10K）— 線ラベル/加熱/冷却/コンデンサ/
      リボイラ/最小接近温度差（教科書 図参照）
  右: グランドコンポジットカーブ（シフト温度）— 加熱不足域/冷却不足域/ピンチ
注釈は余白へ配置（高解像度で余白確認済）。色は濃く・線は太く。

データ: Z:\\report_for_processdesign\\graph\\gcc_bestpoint.json
実行  : Z:\\pdh_simulator\\.venv\\Scripts\\python.exe make_composite_slide.py
出力  : composite_slide.pdf（ベクトル）
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
matplotlib.rcParams["pdf.fonttype"] = 42

SRC = r"Z:\report_for_processdesign\graph\gcc_bestpoint.json"
HERE = os.path.dirname(os.path.abspath(__file__))
T0 = 273.15
RED = "#cc0000"; BLUE = "#1565c0"; ORF = "#e8821e"; ORT = "#b5651d"

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
YLIM = (-210, 700)   # 下に余裕を作り、底部の Q_C/回収/Q_H ブラケットを大きく置く

fig = plt.figure(figsize=(10.2, 7.07))
gs = gridspec.GridSpec(1, 2, width_ratios=[2.55, 1.0], wspace=0.05)
axL = fig.add_subplot(gs[0]); axR = fig.add_subplot(gs[1], sharey=axL)

# ============ 左: 与熱・受熱複合線 ============
axL.plot(H_hot, T_hot, color=RED, lw=4.0, solid_capstyle="round")
axL.plot(H_cold, T_cold, color=BLUE, lw=4.0, solid_capstyle="round")
axL.axhline(Tp, color="0.5", ls="--", lw=1.1)

# 線ラベル（余白：上半分の左～中央）。結論文は載せず口頭で伝える方針。
axL.text(205, 520, "与熱複合線", color=RED, fontsize=23, fontweight="bold", ha="center")
axL.text(312, 66, "受熱複合線", color=BLUE, fontsize=23, fontweight="bold", ha="center")
# 下端：冷却 Q_C ｜ 回収熱量 Q_rec ｜ 加熱 Q_H の 3 区間ブラケット
#   重なり=装置間で回収できる熱、両端=外部から要る最小の冷却/加熱。ユーティリティ名も併記。
_xh = max(H_hot); _xc = max(H_cold); _yb = -122
_zones = [
    (0.0,  QC,  BLUE,  f"$Q_C$ {QC:.1f} MW",          ""),
    (QC,   _xh, "black", f"回収熱量 {_xh - QC:.0f} MW", ""),
    (_xh,  _xc, RED,   f"$Q_H$ {_xc - _xh:.1f} MW",     ""),
]
for _x0, _x1, _c, _lab, _util in _zones:
    axL.annotate("", xy=(_x1, _yb), xytext=(_x0, _yb),
                 arrowprops=dict(arrowstyle="<->", color=_c, lw=2.4))
    for _xx in (_x0, _x1):
        axL.plot([_xx, _xx], [_yb - 8, _yb + 8], color=_c, lw=1.6)
    _m = (_x0 + _x1) / 2
    axL.text(_m, -155, _lab, color=_c, fontsize=15, fontweight="bold",
             ha="center", va="center")
    if _util:
        axL.text(_m, -186, _util, color=_c, fontsize=11.5, ha="center", va="center")
# コンデンサ：上の空白にテキスト、空白列を通る縦矢印で −82℃ フラットへ（曲線に当てない）
axL.text(15, 250, "コンデンサ −82 ℃", fontsize=16, color="black", ha="left")
axL.annotate("", xy=(45, -76), xytext=(58, 222),
             arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
# リボイラ：右上の空白から受熱フラットへ（曲線の上側を通す）
axL.annotate("リボイラ", xy=(192, 43), xytext=(232, 165),
             fontsize=16, color="black", ha="center",
             arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
# 最小接近温度差（ピンチ）：ピンチでの 10K を両矢印で、説明は右下から
axL.annotate("", xy=(141.7, 40.8), xytext=(141.7, 30.7),
             arrowprops=dict(arrowstyle="<->", color="black", lw=2.0))
axL.annotate("最小接近温度差 10 ℃", xy=(144, 33), xytext=(174, -52),
             fontsize=16, color="black", ha="left", va="center",
             arrowprops=dict(arrowstyle="->", color="black", lw=1.5))

axL.set_xlabel("累積エンタルピー  $H$ [MW]", fontsize=18)
axL.set_ylabel("温度  $T$ [℃]", fontsize=18, labelpad=1)
axL.set_xlim(-15, 415); axL.set_ylim(*YLIM)
axL.set_yticks(list(range(-200, 701, 100)))
axL.tick_params(labelsize=14.5, direction="in", top=True, right=True)

# ============ 右: グランドコンポジットカーブ ============
axR.plot(gH, gT, color="black", lw=3.0)
# 面積の色塗りは「面積＝不足熱量」と誤読されやすい（熱量は横軸 H）。とりあえず無効化。
# axR.fill_betweenx(gT, 0, gH, where=[t >= Tp for t in gT], color=ORF, alpha=0.22)
# axR.fill_betweenx(gT, 0, gH, where=[t <= Tp for t in gT], color=BLUE, alpha=0.20)
axR.axhline(Tp, color="0.5", ls="--", lw=1.1)
axR.axvline(0, color="black", lw=0.9)

axR.text(10, 520, "加熱不足域", color=ORT, fontsize=16, fontweight="bold", ha="left")
axR.text(30, -78, "冷却不足域", color=BLUE, fontsize=16, fontweight="bold", ha="left")
axR.plot([0], [Tp], "o", color="black", ms=8)
axR.annotate("ピンチ", xy=(1, 42), xytext=(6, 285), fontsize=16, ha="left",
             arrowprops=dict(arrowstyle="->", color="black", lw=1.5))

axR.set_xlabel("正味熱量  $H$ [MW]", fontsize=18)
axR.set_xlim(-5, 118)
axR.tick_params(labelsize=14.5, direction="in", top=True, right=True, left=True, labelleft=False)

fig.savefig(os.path.join(HERE, "composite_slide.pdf"), bbox_inches="tight", pad_inches=0.0)
plt.close(fig)
print(f"[out] composite_slide.pdf  Q_H={QH:.1f} / Q_C={QC:.1f} MW")
