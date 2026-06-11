# -*- coding: utf-8 -*-
"""
make_econ_breakdown_slide.py — スライド16(経済分析)上段の 3 連図（ベクトルPDF）。
  左 : 費用 TAC と 収益 Revenue の積み上げ棒（赤字の可視化）
  中 : OPEX 構成 ドーナツ（HI 適用後, 4 区分）
  右 : CAPEX 装置別内訳 ドーナツ（装置合計, 上位 + その他）

レポート(graph/make_charts.py)と同一データを踏襲しつつ、スライド用に
全幅(122mm)・大きな文字へ最適化して視認性を最優先する。
OPEX は HI 後(合計 987 億円/年)に統一し、棒グラフの OPEX 987 と一致させて
「原料費が採算を支配する」という主張を直接補強する（用役費は HI で 214.7 削減）。
色はカテゴリ判別を目的に機能的に使用（rule.md 1.1 の例外条件）。

レイアウトは figsize と subplots_adjust で確定させ（bbox_inches=None）、
全幅表示時の高さを約 44mm に固定する（aspect 2.773）。
実行 : Z:\\pdh_simulator\\.venv\\Scripts\\python.exe make_econ_breakdown_slide.py
出力 : econ_breakdown_slide.pdf（ベクトル）
"""
import os
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

HERE = os.path.dirname(os.path.abspath(__file__))

C_CAPEX = "#4c72b0"   # CAPEX 償却（棒）
C_OPEX  = "#dd8452"   # OPEX（棒）
C_REV   = "#55a868"   # Revenue（棒）
RED     = "#c0392b"   # 赤字強調

# 文字サイズ（figsize 9.6in を全面ブリード 5.04in 表示＝×0.525 → 下記×0.525 が実寸 pt）
TITLE, CTR_T, CTR_V, PCT, LEG, BAR = 20, 19, 16, 16, 15, 19

fig = plt.figure(figsize=(9.6, 3.55))   # 縦を短縮（ドーナツは幅律速で縮まない）→全幅化で地図も拡大
gs = gridspec.GridSpec(1, 3, width_ratios=[1.0, 1.0, 1.22], wspace=0.10)
axB = fig.add_subplot(gs[0])
axO = fig.add_subplot(gs[1])
axC = fig.add_subplot(gs[2])

# ============ 左: 費用 TAC と 収益 Revenue ============
capex_amort, opex_total = 47.72, 1076.27
tac = capex_amort + opex_total       # 1124.0
rev = 833.88
deficit = tac - rev                  # 290.1
x0, x1 = 0, 1
W = 0.82
axB.bar(x0, capex_amort, width=W, color=C_CAPEX)
axB.bar(x0, opex_total, width=W, bottom=capex_amort, color=C_OPEX)
axB.bar(x1, rev, width=W, color=C_REV)
axB.text(x0, capex_amort + opex_total / 2, "OPEX\n1076", ha="center", va="center",
         fontsize=BAR + 1, color="white", fontweight="bold")
axB.text(x0, capex_amort / 2, "48", ha="center", va="center",
         fontsize=BAR - 4, color="white", fontweight="bold")
axB.text(x1, rev / 2, "Rev.\n834", ha="center", va="center",
         fontsize=BAR + 1, color="white", fontweight="bold")
axB.annotate("", xy=(x1, tac), xytext=(x1, rev),
             arrowprops=dict(arrowstyle="<->", color=RED, lw=3.0))
axB.text(x1 + 0.05, (rev + tac) / 2, f"赤字\n{deficit:.0f} 億円", ha="left",
         va="center", fontsize=BAR, color=RED, fontweight="bold")
axB.set_xticks([x0, x1])
axB.set_xticklabels(["費用", "収益"], fontsize=LEG + 1)
axB.set_ylabel("億円/年", fontsize=LEG + 1, labelpad=3)
axB.set_ylim(0, tac * 1.06)
axB.set_xlim(-0.62, 2.05)
axB.tick_params(labelsize=LEG - 2, direction="in", top=True, right=True)
axB.set_title("費用と収益", fontsize=TITLE, fontweight="bold", pad=3)

# ============ ドーナツ共通ヘルパ ============
def donut(ax, values, colors, center_title, center_val, pct_min=4.0):
    ax.set_aspect("equal")
    wedges, _t, autot = ax.pie(
        values, labels=None, startangle=90, counterclock=False, colors=colors,
        radius=1.0, center=(0, 0),
        autopct=lambda p: f"{p:.1f}%" if p >= pct_min else "",
        pctdistance=0.80,
        wedgeprops=dict(width=0.40, edgecolor="white", linewidth=1.2),
        textprops=dict(fontsize=PCT, color="black"),
    )
    for t in autot:
        t.set_fontweight("bold")
    ax.text(0, 0.12, center_title, ha="center", va="center", fontsize=CTR_T,
            fontweight="bold")
    ax.text(0, -0.16, center_val, ha="center", va="center", fontsize=CTR_V)
    ax.set_xlim(-1.02, 1.02)   # リングを軸いっぱいに広げ下の空きを排除
    ax.set_ylim(-1.02, 1.02)
    return wedges

# ============ 中: OPEX ドーナツ（HI 適用後, 合計 987, 用役・保全を細分）============
# 用役費(HI後) 223.7 を tier 別に分解: 冷媒144.3/電力38.0/燃料26.7/蒸気ほか14.6
#   (出典: exp3_202606101630 の HI後 utility tier 内訳。蒸気ほか=LP12.7+HP1.3+MP0.6)
# Hasebe 集計項 254.9 を 保全・諸経費(0.180·C_TM)68.7 と
#   一般経費・労務(0.23·(C_RM+C_UT)上乗せ+2.73·C_OL)186.1 に分離。合計 1076.3 で整合。
opex = [
    ("原料費",          574.27, "#66c2a5"),
    ("用役 冷媒",        144.34, "#e6550d"),
    ("用役 電力",         38.03, "#fd8d3c"),
    ("用役 燃料",         26.66, "#fdae6b"),
    ("用役 蒸気ほか",     14.62, "#fdd0a2"),
    ("保全・諸経費",      68.72, "#8da0cb"),
    ("一般経費・労務",   186.14, "#bcbddc"),
    ("触媒・吸着剤",      23.48, "#e78ac3"),
]
wO = donut(axO, [v for _, v, _ in opex], [c for *_, c in opex],
           "OPEX", "1076\n億円/年", pct_min=4.5)
axO.legend(wO, [l for l, *_ in opex], loc="upper center",
           bbox_to_anchor=(0.5, 0.02), ncol=2, fontsize=11.5, frameon=False,
           borderpad=0.0, labelspacing=0.18, handlelength=0.8,
           columnspacing=0.5, handletextpad=0.25)
axO.set_title("OPEX（事業運営費）", fontsize=TITLE, fontweight="bold", pad=2)

# ============ 右: CAPEX ドーナツ ============
capex = [
    ("C3 スプリッタ", 172.81, "#1f77b4"),
    ("脱エタン塔",     48.74, "#aec7e8"),
    ("反応器",         33.07, "#ff7f0e"),
    ("PSA 容器",       25.13, "#ffbb78"),
    ("膜本体",         24.14, "#2ca02c"),
    ("脱ブタン塔",     19.20, "#98df8a"),
    ("Cooler",         13.62, "#d62728"),
    ("その他",         45.08, "#ff9896"),
]
wC = donut(axC, [v for _, v, _ in capex], [c for *_, c in capex],
           "CAPEX", "382\n億円", pct_min=4.0)
axC.legend(wC, [l for l, *_ in capex], loc="upper center",
           bbox_to_anchor=(0.5, 0.02), ncol=2, fontsize=11.5, frameon=False,
           borderpad=0.0, labelspacing=0.18, handlelength=0.8,
           columnspacing=0.5, handletextpad=0.25)
axC.set_title("CAPEX（装置別内訳）", fontsize=TITLE, fontweight="bold", pad=2)

fig.subplots_adjust(left=0.092, right=0.995, top=0.90, bottom=0.205)
# 棒グラフは凡例を持たないので、下の空き(ドーナツ凡例域)まで軸を伸ばして縦長化する
_p = axB.get_position()
axB.set_position([_p.x0, 0.11, _p.width, _p.y1 - 0.11])
out = os.path.join(HERE, "econ_breakdown_slide.pdf")
fig.savefig(out, bbox_inches=None, pad_inches=0.0)
plt.close(fig)
print(f"[out] {out}")
