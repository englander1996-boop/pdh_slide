# -*- coding: utf-8 -*-
r"""make_interaction_panels.py — スライド15用 2x2 相互作用マップ(工程横断ペア)。

各ペアで TAC 等高線を描く。どのペアでも最小 TAC の谷が斜め＝2変数の最適値が互いに
依存(相互作用) → 部分最適化では届かず全 23 変数を同時最適化が必要。★＝採用設計。
全点フローシート全体(HYSYS)で評価。

データ: fig_grid_p1.csv(入口温度×浅床厚)、p2(入口温度×膜面積)、p3(膜面積×C3塔段数)、
        p4(入口温度×C3塔段数)。出力: fig_interaction_panels.pdf
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _cand in ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP", "HaranoAjiGothic"]:
    try:
        font_manager.findfont(_cand, fallback_to_default=False)
        matplotlib.rcParams["font.family"] = _cand
        break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["xtick.direction"] = "out"
matplotlib.rcParams["ytick.direction"] = "out"

HERE = os.path.dirname(os.path.abspath(__file__))

def f_int(v):  return f"{v:.0f}"
def f_1f(v):   return f"{v:.1f}"
def f_bar(v):  return f"{v/100:.0f}"            # 圧力 kPa → bar
def f_man(v):  return f"{v/1e4:.0f}"            # 膜面積 m² → 万m²

# (csv, 見出し, x軸, y軸, x_fmt, y_fmt, x★, y★)  各ユニット 1 枚ずつ
PANELS = [
    ("fig_grid_p1.csv", "反応器：入口温度 $\\times$ 浅床厚", "$T_\\mathrm{in}$ [K]",  "$L_\\mathrm{bed}$ [m]", f_int, f_1f, 935.15, 1.577),
    ("m_a.csv",         "膜$\\times$C3塔：膜面積 $\\times$ 段数", "$A_\\mathrm{mem}$ [万m$^2$]", "$N_3$ [段]", f_man, f_int, 1.278e5, 117),
    ("u_c3.csv",        "C3塔：段数 $\\times$ 圧力",        "$N_3$ [段]",            "$P_3$ [bar]",           f_int, f_bar, 117, 1675.0),
    ("ucross.csv",      "反応器$\\times$C3塔：浅床厚 $\\times$ 段数", "$L_\\mathrm{bed}$ [m]", "$N_3$ [段]",   f_1f, f_int, 1.577, 117),
]

def load(csv):
    path = os.path.join(HERE, csv)
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path)
    if "x" not in d.columns:                       # p1 形式 (T_in/L_bed)
        cols = [c for c in d.columns if c not in ("feasible","TAC_hi","eff_TAC","reason")]
        d = d.rename(columns={cols[0]: "x", cols[1]: "y"})
    return d

def frac_index(val, arr):
    """連続値 val を、格子 arr 上の小数インデックス(0..n-1)へ写す。"""
    return float(np.interp(val, arr, np.arange(len(arr))))

fig, axes = plt.subplots(2, 2, figsize=(10.4, 6.0))
for ax, (csv, title, xl, yl, xfmt, yfmt, sx, sy) in zip(axes.ravel(), PANELS):
    d = load(csv)
    if d is None or d["x"].nunique() < 3 or d["y"].nunique() < 3:
        ax.text(0.5, 0.5, "計算中…", ha="center", va="center", fontsize=15,
                transform=ax.transAxes); ax.set_title(title, fontsize=14); continue
    X = np.array(sorted(d["x"].unique())); Y = np.array(sorted(d["y"].unique()))
    nx, ny = len(X), len(Y)
    TAC = np.full((ny, nx), np.nan); FEAS = np.zeros((ny, nx), bool)
    for _, r in d.iterrows():
        j = int(np.where(X == r["x"])[0][0]); i = int(np.where(Y == r["y"])[0][0])
        FEAS[i, j] = bool(r["feasible"])
        if bool(r["feasible"]): TAC[i, j] = r["TAC_hi"]
    XI, YI = np.meshgrid(np.arange(nx), np.arange(ny))        # 等間隔インデックス座標
    vmin = np.nanmin(TAC); vmax = np.nanpercentile(TAC, 80)
    levels = np.linspace(vmin, max(vmax, vmin+1e-6), 14)
    cf = ax.contourf(XI, YI, np.clip(TAC, None, vmax), levels=levels, cmap="YlGnBu_r", extend="max")
    cb = fig.colorbar(cf, ax=ax, pad=0.02, fraction=0.05, aspect=14)
    cb.ax.tick_params(labelsize=8.5); cb.set_label("TAC", fontsize=9)
    for i in range(ny):
        for j in range(nx):
            if not FEAS[i, j]:
                ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, facecolor="#9aa0a6",
                             hatch="//", edgecolor="white", linewidth=0.25, zorder=2))
    # 谷底 (各 x 列の最小 TAC) — 斜めを示す
    fx, fy = [], []
    for j in range(nx):
        col = TAC[:, j]
        if np.any(~np.isnan(col)):
            fx.append(j); fy.append(int(np.nanargmin(col)))
    ax.plot(fx, fy, "-o", color="#C0392B", lw=2.0, ms=3.5, zorder=4)
    # ★ 採用設計
    ax.scatter([frac_index(sx, X)], [frac_index(sy, Y)], marker="*", s=440,
               c="white", edgecolors="black", linewidths=1.0, zorder=5)
    # 軸目盛 (4 本, 実値ラベル)
    xt = np.linspace(0, nx-1, 4).round().astype(int)
    yt = np.linspace(0, ny-1, 4).round().astype(int)
    ax.set_xticks(xt); ax.set_xticklabels([xfmt(X[t]) for t in xt], fontsize=10)
    ax.set_yticks(yt); ax.set_yticklabels([yfmt(Y[t]) for t in yt], fontsize=10)
    ax.set_xlim(-0.5, nx-0.5); ax.set_ylim(-0.5, ny-0.5)
    ax.set_title(title, fontsize=14, pad=4)
    ax.set_xlabel(xl, fontsize=12.5); ax.set_ylabel(yl, fontsize=12.5)

fig.tight_layout(pad=0.5, h_pad=1.0, w_pad=0.8)
out = os.path.join(HERE, "fig_interaction_panels.pdf")
fig.savefig(out, bbox_inches="tight", pad_inches=0.03)
print("wrote", out)
