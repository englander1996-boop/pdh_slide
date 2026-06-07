# -*- coding: utf-8 -*-
"""分子ふるいの仕組み：運動直径とZIF-8細孔(4.0-4.2Å)。C3H6は通り、C3H8は阻まれる。"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
for _c in ["Yu Gothic","Meiryo","MS Gothic","Noto Sans CJK JP"]:
    try:
        font_manager.findfont(_c, fallback_to_default=False)
        matplotlib.rcParams["font.family"]=_c; break
    except Exception: continue
matplotlib.rcParams["axes.unicode_minus"]=False
matplotlib.rcParams["xtick.direction"]="in"; matplotlib.rcParams["ytick.direction"]="in"
matplotlib.rcParams["xtick.top"]=True; matplotlib.rcParams["ytick.right"]=True
matplotlib.rcParams["font.weight"]="bold"; matplotlib.rcParams["axes.linewidth"]=1.3

A = "Å"  # Å
fig, ax = plt.subplots(figsize=(5.2, 3.2))
ax.axvspan(4.0, 4.2, color="#2E9E5B", alpha=0.22)
ax.axvline(4.0, color="#2E9E5B", lw=1.2); ax.axvline(4.2, color="#2E9E5B", lw=1.2)
ax.text(4.1, 1.16, f"ZIF-8 細孔\n4.0–4.2 {A}", color="#1f7a43", fontsize=13,
        ha="center", va="center", fontweight="bold")
# C3H6: 通る
ax.text(4.0, 0.88, "通る", color="#1f7a43", fontsize=14, ha="center", va="center", fontweight="bold")
ax.scatter([4.0], [0.56], s=520, color="#2E9E5B", zorder=5, edgecolor="black", linewidth=1.2)
ax.text(4.0, 0.26, f"$\\mathrm{{C_3H_6}}$\n4.0 {A}", color="#1f7a43", fontsize=13,
        ha="center", va="center", fontweight="bold")
# C3H8: 阻む
ax.text(4.3, 0.88, "阻む", color="#C0392B", fontsize=14, ha="center", va="center", fontweight="bold")
ax.scatter([4.3], [0.56], s=760, color="#C0392B", zorder=5, edgecolor="black", linewidth=1.2)
ax.text(4.3, 0.26, f"$\\mathrm{{C_3H_8}}$\n4.3 {A}", color="#C0392B", fontsize=13,
        ha="center", va="center", fontweight="bold")
ax.set_title("[ 分子ふるいの仕組み ]", fontsize=20, fontweight="bold")
ax.set_xlabel(f"運動直径 [{A}]", fontsize=14, color="black", fontweight="normal")
ax.set_xlim(3.85, 4.45); ax.set_ylim(0, 1.3)
ax.set_yticks([])
ax.set_xticks([3.9,4.0,4.1,4.2,4.3,4.4])
ax.tick_params(axis="x", labelsize=13, width=1.3, length=5, colors="black")
fig.tight_layout()
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"sieving.png")
fig.savefig(out, dpi=300, bbox_inches="tight"); plt.close(fig)
print("[out]", out)
