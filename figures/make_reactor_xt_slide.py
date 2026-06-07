# -*- coding: utf-8 -*-
"""
スライド8（転化率の天井）用 X-T 線図のクリーン版。
レポートの make_reactor_charts.make_xt_diagram のロジックを再利用し、スライド向けに:
  - タイトル無し（スライド見出しと重複を避ける）
  - グリッド無し
  - 内向き目盛り・四辺
  - 大きめフォント / dpi 300
出力: figures/reactor_xt_slide.png
実行: Z:\\pdh_simulator\\.venv\\Scripts\\python.exe figures\\make_reactor_xt_slide.py
"""
import os
import sys

_GRAPH = r"Z:\report_for_processdesign\graph"
sys.path.insert(0, _GRAPH)
import make_reactor_charts as mrc  # 大域: A0,B0,T_IN,P,th,THERMO_DATA,brentq,np,plt

np = mrc.np
plt = mrc.plt
brentq = mrc.brentq
th = mrc.th
THERMO_DATA = mrc.THERMO_DATA
A0, B0, T_IN, P = mrc.A0, mrc.B0, mrc.T_IN, mrc.P

# --- スライド向けスタイル（内向き四辺・グリッド無し・太く大きく・くっきり）---
plt.rcParams["font.size"] = 19
plt.rcParams["font.weight"] = "bold"
plt.rcParams["axes.labelweight"] = "bold"
plt.rcParams["axes.grid"] = False
plt.rcParams["xtick.direction"] = "in"
plt.rcParams["ytick.direction"] = "in"
plt.rcParams["xtick.top"] = True
plt.rcParams["ytick.right"] = True
plt.rcParams["axes.linewidth"] = 1.8          # 枠線を太く
plt.rcParams["xtick.major.width"] = 1.7
plt.rcParams["ytick.major.width"] = 1.7
plt.rcParams["xtick.major.size"] = 6
plt.rcParams["ytick.major.size"] = 6
plt.rcParams["lines.antialiased"] = True
plt.rcParams["savefig.dpi"] = 400

F_IN = {"A": A0, "B": B0, "C": 0.0, "D": 0.0, "E": 0.0, "F": 0.0}


def H_stream(F, T):
    return sum(f * 1000.0 * (THERMO_DATA[c].dHf_298 + th.calc_enthalpy_change(c, 298.15, T))
               for c, f in F.items() if f != 0)


H_in = H_stream(F_IN, T_IN)


def comp_r1(xi):
    return {"A": A0 - xi, "B": B0 + xi, "C": xi, "D": 0, "E": 0, "F": 0}


def T_adiabatic(xi):
    return brentq(lambda T: H_stream(comp_r1(xi), T) - H_in, 150.0, T_IN + 50.0)


def X_eq_isothermal(T):
    Keq = th.calc_keq(T)

    def g(xi):
        Fa, Fb, Fc, Ft = A0 - xi, B0 + xi, xi, A0 + B0 + xi
        return P * (Fb / Ft) * (Fc / Ft) / (Fa / Ft) - Keq

    if g(1.0) > 0:
        return 0.0
    return brentq(g, 1.0, A0 - 1.0) / A0 * 100


def resid(xi):
    T = T_adiabatic(xi)
    Fa, Fb, Fc, Ft = A0 - xi, B0 + xi, xi, A0 + B0 + xi
    Q = P * (Fb / Ft) * (Fc / Ft) / (Fa / Ft)
    return Q - th.calc_keq(T)


xi_ad = brentq(resid, 1.0, 2500.0)
T_ad = T_adiabatic(xi_ad)
X_ad = xi_ad / A0 * 100
X_iso = X_eq_isothermal(T_IN)

Tplot = np.linspace(420, 700, 160)
Xeq = np.array([X_eq_isothermal(t + 273.15) for t in Tplot])
xi_line = np.linspace(1, 2400, 160)
Top = np.array([T_adiabatic(x) - 273.15 for x in xi_line])
Xop = xi_line / A0 * 100

fig, ax = plt.subplots(figsize=(8.3, 4.3))   # 横長（スライドで2図スタック用）
ax.plot(Tplot, Xeq, color="teal", lw=4.8, solid_capstyle="round", label=r"平衡線 $X_{eq}(T)$")
ax.plot(Top, Xop, color="darkorange", lw=4.8, solid_capstyle="round", label=r"断熱操作線 $X_{op}(T)$")
ax.plot(T_ad - 273.15, X_ad, "*", color="#c0392b", ms=34, zorder=5,
        markeredgecolor="white", markeredgewidth=1.4,
        label=f"断熱平衡 {T_ad-273.15:.0f}℃ / {X_ad:.0f}%")

ax.plot(T_IN - 273.15, X_iso, "D", color="purple", ms=16, zorder=5,
        markeredgecolor="white", markeredgewidth=1.2)
ax.annotate(f"等温なら {X_iso:.0f}%", xy=(T_IN - 273.15, X_iso), xycoords="data",
            xytext=(602, 45), textcoords="data",
            fontsize=18, color="purple", fontweight="bold", ha="center",
            arrowprops=dict(arrowstyle="-|>", color="purple", lw=2.4))

ax.plot(T_IN - 273.15, 0, "ko", ms=12)
ax.annotate("反応器入口", (T_IN - 273.15, 0), fontsize=15,
            xytext=(-96, 32), textcoords="offset points",
            arrowprops=dict(arrowstyle="-|>", color="dimgray", lw=1.8))

ax.set_xlabel("温度 [℃]", fontsize=20)
ax.set_ylabel("単通転化率 [%]", fontsize=20)
ax.legend(fontsize=16, loc="upper left", framealpha=0.95, borderpad=0.6, labelspacing=0.35)
ax.set_xlim(420, 700)
ax.set_ylim(0, 90)
ax.tick_params(labelsize=16)
fig.tight_layout(pad=0.3)

_d = os.path.dirname(os.path.abspath(__file__))
fig.savefig(os.path.join(_d, "reactor_xt_slide.pdf"), bbox_inches="tight", pad_inches=0.01)
out = os.path.join(_d, "reactor_xt_slide.png")
fig.savefig(out, dpi=400, bbox_inches="tight", pad_inches=0.01)
print("[out]", out)
print(f"[info] X_ad={X_ad:.1f}%  T_ad={T_ad-273.15:.0f}C  X_iso={X_iso:.1f}%")
