# -*- coding: utf-8 -*-
"""活性炭の吸着等温線（Langmuir, Choi et al. 2003）。H2はほぼ非吸着、CH4/C2は吸着。
なぜPSAでH2を分けられるかを一目で示す。スライド統一スタイル。"""
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
matplotlib.rcParams["font.weight"]="bold"; matplotlib.rcParams["axes.linewidth"]=1.3

# Langmuir: q = q_s*b*P/(1+b*P), b[1/bar] = a[m3/mol]/(R*T)*1e5,  R*T=2477 J/mol @298K
RT=8.314*298.0
def bbar(a): return a/RT*1e5
PAR={  # q_s[mol/kg], a[m3/mol]  (Choi et al., J. Chem. Eng. Data 2003)
 "C2H6":(5.66,0.0533,"#C0392B"),
 "C2H4":(6.20,0.0327,"#E8821E"),
 "CH4" :(5.23,0.00332,"#1F6FC4"),
}
p=np.linspace(0,10,200)
fig,ax=plt.subplots(figsize=(5.9,3.0))
lab={"C2H6":"$\\mathrm{C_2H_6}$","C2H4":"$\\mathrm{C_2H_4}$","CH4":"$\\mathrm{CH_4}$"}
for k,(qs,a,c) in PAR.items():
    b=bbar(a); q=qs*b*p/(1+b*p)
    ax.plot(p,q,color=c,lw=3.0,label=lab[k],zorder=4)
# H2: ほぼ非吸着
ax.plot(p,0.0*p+0.02,color="#2E9E5B",lw=3.4,label="$\\mathrm{H_2}$",zorder=5)
ax.text(7.0,0.35,"$\\mathrm{H_2}$ はほぼ吸着せず\n素通り＝製品へ",color="#1f7a43",
        fontsize=13,fontweight="bold",ha="center",va="bottom")
ax.set_xlabel("分圧 [bar]",fontsize=15,fontweight="normal",color="black")
ax.set_ylabel("吸着量 $q$ [mol/kg]",fontsize=15,fontweight="normal",color="black")
ax.set_xlim(0,10); ax.set_ylim(0,6.5)
ax.tick_params(labelsize=15,width=1.3,length=5,colors="black")
ax.legend(fontsize=14,frameon=False,loc="center right",ncol=1)
fig.tight_layout()
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"psa_isotherm.png")
fig.savefig(out,dpi=300,bbox_inches="tight"); plt.close(fig)
print("[out]",out)
