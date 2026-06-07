# -*- coding: utf-8 -*-
"""膜面積プロファイル図（非透過側C3H6の低下／累積透過純度）。スライド統一スタイル。"""
import os, csv
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

HERE=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE,"prof_membrane.csv"),encoding="utf-8") as fh:
    r=list(csv.DictReader(fh))
a=[float(x["area_frac"]) for x in r]
xret=[float(x["x_C3H6_ret"]) for x in r]
yperm=[float(x["y_C3H6_perm_cum"]) for x in r]

FL,FT,FK,FTT=16,17,16,21
fig,ax=plt.subplots(figsize=(5.9,2.75))
ax.plot(a,yperm,color="#2E9E5B",lw=3.4,label="透過 $\\mathrm{C_3H_6}$",zorder=5)
ax.plot(a,xret,color="#E8821E",lw=2.6,label="非透過 $\\mathrm{C_3H_6}$",zorder=4)
ax.set_xlabel("モジュール内の位置　入口 → 出口",fontsize=FL,fontweight="normal",color="black")
ax.set_ylabel("$\\mathrm{C_3H_6}$ モル分率",fontsize=FL,fontweight="normal",color="black")
ax.set_xlim(0,1); ax.set_ylim(0,1.02)
ax.tick_params(labelsize=FT,width=1.3,length=5,colors="black")
ax.legend(fontsize=FK,frameon=False,loc="lower left",bbox_to_anchor=(0.02,0.02))
# 端点の値注記
ax.annotate("98.6%",xy=(0.5,0.986),fontsize=13,color="#1f7a43",fontweight="bold",ha="center",va="bottom")
ax.annotate("60.7%",xy=(0.02,0.607),fontsize=12,color="#b3601a",fontweight="bold",ha="left",va="bottom")
ax.annotate("38.2%",xy=(0.98,0.382),fontsize=12,color="#b3601a",fontweight="bold",ha="right",va="top")
fig.tight_layout()
out=os.path.join(HERE,"membrane_profile.png")
fig.savefig(out,dpi=300,bbox_inches="tight"); plt.close(fig)
print("[out]",out)
