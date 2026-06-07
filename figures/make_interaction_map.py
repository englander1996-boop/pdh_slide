# -*- coding: utf-8 -*-
r"""make_interaction_map.py — スライド15用「相互作用=斜め谷」2D TAC マップ。

run_interaction_grid.py が出力した fig_interaction_grid.csv (trial #201 背景、入口温度 T_in と
浅床厚 L_bed を全フローシート HYSYS 評価) を読み、TAC_hi 等高線を描く。目標転化率は「床を厚く」
or「高温」で達成でき等転化率線は斜め。だが高温は選択率を損なうため最小 TAC の谷は斜めに走る。
= T_in と L_bed は独立に最適化できない(相互作用) → 23 変数の同時最適化が必要。

出力: fig_interaction_map.pdf (ベクトル, JP フォント埋込)
実行: Z:\pdh_simulator\.venv\Scripts\python.exe make_interaction_map.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch

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
matplotlib.rcParams["xtick.direction"] = "out"
matplotlib.rcParams["ytick.direction"] = "out"

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "fig_interaction_grid.csv"))

X = np.array(sorted(df["T_in"].unique()))     # x 軸: 入口温度
Y = np.array(sorted(df["L_bed"].unique()))     # y 軸: 浅床厚
TAC = np.full((len(Y), len(X)), np.nan)
FEAS = np.zeros((len(Y), len(X)), dtype=bool)
for _, r in df.iterrows():
    j = int(np.where(X == r["T_in"])[0][0]); i = int(np.where(Y == r["L_bed"])[0][0])
    FEAS[i, j] = bool(r["feasible"])
    if bool(r["feasible"]):
        TAC[i, j] = r["TAC_hi"]

# 谷底: 各 T_in 列で TAC 最小の L_bed (可行のみ)
floorX, floorY = [], []
for j in range(len(X)):
    col = TAC[:, j]
    if np.any(~np.isnan(col)):
        i = int(np.nanargmin(col)); floorX.append(X[j]); floorY.append(Y[i])
# 最良点 (採用設計 #201)
BX, BY = 935.15, 1.577

fig, ax = plt.subplots(figsize=(4.7, 3.95))  # スライド左パネル用 (大きめフォント)
XX, YY = np.meshgrid(X, Y)
vmin = np.nanmin(TAC); vmax = np.nanpercentile(TAC, 80)   # 谷のコントラストを出す
levels = np.linspace(vmin, vmax, 16)
cf = ax.contourf(XX, YY, np.clip(TAC, None, vmax), levels=levels,
                 cmap="YlGnBu_r", extend="max")
cb = fig.colorbar(cf, ax=ax, pad=0.02)
cb.set_label("TAC [億円/年]", fontsize=13)
cb.ax.tick_params(labelsize=10.5)
# 不可行セルを灰色ハッチ
dX = (X[1]-X[0]); dY = (Y[1]-Y[0])
for i in range(len(Y)):
    for j in range(len(X)):
        if not FEAS[i, j]:
            ax.add_patch(plt.Rectangle((X[j]-dX/2, Y[i]-dY/2), dX, dY,
                         facecolor="#9aa0a6", hatch="//", edgecolor="white",
                         linewidth=0.3, zorder=2))
# 谷底ライン (斜め = 相互作用)
ax.plot(floorX, floorY, "-o", color="#C0392B", lw=2.2, ms=5, zorder=4)
# 採用点 #201 (★のみ。注記はスライドのキャプションに置く)
ax.scatter([BX], [BY], marker="*", s=340, c="white",
           edgecolors="black", linewidths=1.1, zorder=5)
ax.set_xlabel("入口温度 $T_{\\mathrm{in}}$ [K]", fontsize=15)
ax.set_ylabel("浅床厚 $L_{\\mathrm{bed}}$ [m]", fontsize=15)
ax.tick_params(labelsize=12.5)
ax.set_xlim(X[0]-dX/2, X[-1]+dX/2)
ax.set_ylim(Y[0]-dY/2, Y[-1]+dY/2)
fig.tight_layout(pad=0.3)
out = os.path.join(HERE, "fig_interaction_map.pdf")
fig.savefig(out, bbox_inches="tight", pad_inches=0.03)
bi = int(np.nanargmin(TAC)); bii, bij = np.unravel_index(bi, TAC.shape)
print("wrote", out, f"| grid-min T_in={X[bij]} L_bed={Y[bii]} TAC={TAC[bii,bij]:.1f}")
