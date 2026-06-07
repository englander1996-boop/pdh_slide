# -*- coding: utf-8 -*-
"""損益分岐図（スライド17）。最良設計点を固定しLPG単価を振って年間利益を評価。
分岐64.4円/kg・現行95円/kgで-224億円/年。線を濃く・文字大・分岐点を強調。"""
import os
import numpy as np
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
matplotlib.rcParams["font.weight"]="bold"; matplotlib.rcParams["axes.linewidth"]=1.5

BE=64.4; CUR=95.0; CURP=-224.0
slope=CURP/(CUR-BE)
p=np.linspace(40,130,200); profit=slope*(p-BE)
fig,ax=plt.subplots(figsize=(6.6,4.3))
ax.fill_between(p,profit,0,where=(profit>=0),color="#55a868",alpha=0.30,zorder=1)
ax.fill_between(p,profit,0,where=(profit<0),color="#c44e52",alpha=0.30,zorder=1)
ax.axhline(0,color="black",lw=1.4,zorder=2)
ax.plot(p,profit,color="black",lw=4.0,zorder=3)
# 損益分岐点を強調
ax.axvline(BE,color="black",ls=":",lw=1.6,zorder=2)
ax.plot([BE],[0],marker="o",ms=22,mfc="#f5c000",mec="black",mew=2.5,zorder=6)
ax.annotate("損益分岐点\n$64.4$ 円/kg",xy=(BE,0),xytext=(78,90),
            fontsize=22,fontweight="bold",color="black",ha="left",va="center",
            arrowprops=dict(arrowstyle="-|>",lw=2.2,color="black"),
            bbox=dict(boxstyle="round,pad=0.3",fc="#fff3c4",ec="black",lw=1.6),zorder=7)
# 現行
ax.plot([CUR],[CURP],marker="o",ms=11,color="black",zorder=5)
ax.annotate("現行 $95$ 円/kg\n$-224$ 億円/年",xy=(CUR,CURP),xytext=(99,-150),
            fontsize=17,fontweight="bold",color="#7a2b2e",ha="left",va="center")
ax.text(46,120,"黒字",color="#2f6b40",fontsize=22,fontweight="bold")
ax.text(116,-330,"赤字",color="#a52a2e",fontsize=22,fontweight="bold")
ax.set_xlabel("LPG 原料単価 [円/kg]",fontsize=19,fontweight="bold")
ax.set_ylabel("年間利益 [億円/年]",fontsize=19,fontweight="bold")
ax.set_xlim(40,130); ax.set_ylim(-500,200)
ax.tick_params(labelsize=17,width=1.5,length=6)
fig.tight_layout()
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"breakeven_slide.png")
fig.savefig(out,dpi=300,bbox_inches="tight"); plt.close(fig)
print("[out]",out)
