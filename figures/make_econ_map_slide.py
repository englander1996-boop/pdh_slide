# -*- coding: utf-8 -*-
"""
make_econ_map_slide.py — スライド16(経済分析)下段の 世界 PDH 立地図（ベクトルPDF）。
  レポート graph/make_map.py と同一データ・同一分類を踏襲。
  スライド用に 2 パネルを左右に並べた横長・低背レイアウトとし、全幅(122mm)で
  マーカー・番号・凡例を大きくして視認性を最優先する。
    左 : 米州   右 : 欧州・中東・アジア
  原料調達の 2 パターンで色分け（カテゴリ判別; rule.md 1.1 例外）:
    産出地直結型(シェール／随伴ガス)=赤い三角  /  港湾・輸入型(VLGC 輸入)=青い丸

実行 : Z:\\pdh_simulator\\.venv\\Scripts\\python.exe make_econ_map_slide.py
出力 : econ_map_slide.pdf（ベクトル, figsize 9.6x2.44 → 全幅で高さ約 31mm）
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, gridspec
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature

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
C_SRC = "#c0392b"   # 産出地直結型
C_PORT = "#1f6fc4"  # 港湾・輸入型

TITLE, GL, NUM, LEG, SUP = 13, 11, 14, 12.5, 18   # ×0.525 が実寸 pt

plants = [
    (1,  "Fujian Meide",    25.4920, 119.3327, "P", ( 3.6,  1.8)),
    (2,  "Qingdao Jinneng", 35.5862, 119.7596, "P", (-3.8,  2.0)),
    (3,  "APOC (Jubail)",   27.0174,  49.5951, "S", ( 5.0,  2.0)),
    (4,  "Enterprise",      29.8602, -94.8745, "S", ( 2.1,  2.1)),
    (5,  "Borealis",        51.2500,   4.2833, "P", ( 5.0,  2.0)),
    (6,  "Guangxi Huayi",   21.7300, 108.6200, "P", ( 4.2, -2.4)),
    (7,  "Dow",             28.9435, -95.3682, "S", (-2.8, -2.4)),
    (8,  "Flint Hills",     29.7200, -95.2500, "S", (-3.2,  2.3)),
    (9,  "Oriental Energy", 29.9600, 121.9300, "P", ( 4.2,  2.0)),
    (10, "Formosa Ningbo",  29.9000, 121.8500, "P", ( 4.2, -2.4)),
    (11, "SK Advanced",     35.5000, 129.3500, "P", ( 4.2,  1.8)),
    (12, "Inter Pipeline",  53.7792,-113.1371, "S", ( 2.5,  2.1)),
]
STYLE = {"S": dict(marker="^", color=C_SRC), "P": dict(marker="o", color=C_PORT)}


def draw_panel(ax, extent, title):
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor="0.90", zorder=0)
    ax.add_feature(cfeature.OCEAN, facecolor="white", zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="0.45")
    ax.add_feature(cfeature.BORDERS, linewidth=0.4, edgecolor="0.6")
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="0.75", linestyle=":")
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": GL}
    gl.ylabel_style = {"size": GL}
    # 地域名はパネル内左上に置き、上部の見出し(suptitle)と干渉させない
    ax.text(0.015, 0.97, title, transform=ax.transAxes, ha="left", va="top",
            fontsize=TITLE, fontweight="bold", zorder=7,
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="0.6", lw=0.5,
                      alpha=0.9))


fig = plt.figure(figsize=(9.6, 2.84))   # 全面ブリード 128mm で高さ 41.6mm（見出し込み）
gs = gridspec.GridSpec(1, 2, width_ratios=[1.0, 1.85], wspace=0.05)
axA = fig.add_subplot(gs[0], projection=ccrs.PlateCarree())
axE = fig.add_subplot(gs[1], projection=ccrs.PlateCarree())

draw_panel(axA, [-126, -86, 24, 57], "米州")
draw_panel(axE, [-12, 138, 12, 57], "欧州・中東・アジア")

for n, name, lat, lon, cat, (dlon, dlat) in plants:
    ax = axA if lon < -50 else axE
    st = STYLE[cat]
    # スライド版は番号(表との対応)を持たないためマーカーのみ描く
    ax.plot(lon, lat, marker=st["marker"], color=st["color"], markersize=14,
            markeredgecolor="black", markeredgewidth=0.7,
            transform=ccrs.PlateCarree(), zorder=5)

legend_elems = [
    Line2D([0], [0], marker="^", color="w", markerfacecolor=C_SRC,
           markeredgecolor="black", markersize=15,
           label="産出地直結型（シェール・随伴ガス）"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=C_PORT,
           markeredgecolor="black", markersize=15,
           label="港湾・輸入型（VLGC 輸入）"),
]
fig.legend(handles=legend_elems, loc="lower center", ncol=2, fontsize=LEG,
           framealpha=0.95, bbox_to_anchor=(0.5, 0.02))

fig.suptitle("大規模 PDH は安価な原料を確保できる立地に集中、国内生産は原料面で不利",
             fontsize=SUP, fontweight="bold", y=0.985)
fig.subplots_adjust(left=0.035, right=0.995, top=0.86, bottom=0.255)
out = os.path.join(HERE, "econ_map_slide.pdf")
fig.savefig(out, bbox_inches=None, pad_inches=0.0)
plt.close(fig)
print(f"[out] {out}")
