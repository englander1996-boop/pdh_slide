# -*- coding: utf-8 -*-
"""
make_membrane_profile.py — 膜クロスフローの膜面積プロファイルを生成。
膜モデル(units/separators/membrane/membrane_system.py)の _y_local / _membrane_ode と
同一式を t_eval 付きで積分し、膜面積に沿った非透過側 C3H6 組成・累積透過純度を出す。
trial #201 条件。実行: Z:\pdh_simulator\.venv\Scripts\python.exe make_membrane_profile.py
"""
import os, csv, math
import numpy as np
from scipy.integrate import solve_ivp

# --- trial #201（top1_trial201.txt [Membrane] 由来）---
feed_kmolh = 5457.0      # 膜フィード総流量（permeate2024 / stage_cut0.371）
x0   = 0.607             # フィード C3H6 モル分率
P_H  = 8.44e5            # 供給側 [Pa]
P_L  = 1.013e5           # 透過側 [Pa]
A_mem= 1.278e5           # 総膜面積 [m^2]
Q_A  = 40 * 3.35e-10     # C3H6 透過度 [mol m^-2 s^-1 Pa^-1]
alpha= 90.0
gamma= P_L / P_H
Q_B  = Q_A / alpha

F   = feed_kmolh * 1000.0 / 3600.0   # mol/s
Fc0 = x0 * F
Fa0 = (1.0 - x0) * F

def y_local(x):
    if abs(alpha - 1.0) < 1e-10:
        return x
    a = (1.0 - alpha) * gamma
    b = (alpha - 1.0) * (x + gamma) + 1.0
    c = -alpha * x
    disc = max(0.0, b*b - 4.0*a*c)
    denom = -b - math.sqrt(disc)
    if abs(denom) < 1e-30:
        return x
    return max(0.0, min(1.0, (2.0*c)/denom))

def ode(A, Fv):
    fc = max(Fv[0], 1e-12); fa = max(Fv[1], 1e-12)
    x = fc/(fc+fa); y = y_local(x)
    Jc = Q_A*(x*P_H - y*P_L); Ja = Q_B*((1.0-x)*P_H - (1.0-y)*P_L)
    return [-max(Jc,0.0), -max(Ja,0.0)]

t = np.linspace(0.0, A_mem, 200)
sol = solve_ivp(ode, (0.0, A_mem), [Fc0, Fa0], method='Radau',
                rtol=1e-4, atol=1e-7, max_step=A_mem/200.0, t_eval=t)
Fc, Fa = sol.y[0], sol.y[1]
xret = Fc/(Fc+Fa)
perm_c = Fc0 - Fc; perm_a = Fa0 - Fa; perm_tot = perm_c + perm_a
ycum = np.where(perm_tot > 1e-9, perm_c/np.maximum(perm_tot,1e-12), np.nan)
scut = perm_tot / F

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prof_membrane.csv")
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["area_frac","x_C3H6_ret","y_C3H6_perm_cum","stage_cut"])
    for i in range(len(sol.t)):
        w.writerow([f"{sol.t[i]/A_mem:.5f}", f"{xret[i]:.5f}", f"{ycum[i]:.5f}", f"{scut[i]:.5f}"])
print("[out]", out)
print(f"retentate x: {xret[0]:.3f} -> {xret[-1]:.3f}")
print(f"cum permeate purity end: {ycum[-1]:.3f}")
print(f"stage_cut end: {scut[-1]:.3f}")
