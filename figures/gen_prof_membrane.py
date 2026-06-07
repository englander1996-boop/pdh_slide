"""
Generate the membrane crossflow PROFILE for trial #201 by re-integrating the
PDH simulator's OWN crossflow ODE (units/separators/membrane/membrane_system.py)
with dense output, so we can emit the composition profile ALONG the membrane area.

The model's _membrane_ode integrates the same ODE but only returns the endpoint.
Here we reuse the model's EXACT flux function (_y_local, Q_A_SI, alpha, gamma,
the same negative-flux clipping and the same Radau/rtol/atol/max_step settings)
and add dense_output to recover F(A) at any A. No physics is changed.

Conditions (trial #201, verified against top1_trial201.txt + best.json):
  feed C3H6 = 3305.2 kmol/h, C3H8 = 2144.3 kmol/h  (total 5449.5, 60.7% C3H6)
  P_H = 843657.62 Pa (8.44 bar), P_L = 1.01325e5 Pa (1 atm)
  Q_A = 40 GPU, alpha = 90, A_mem = 127838.28 m^2
"""
import csv
import math
import sys

import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, r"Z:\pdh_simulator")
sys.path.insert(0, r"Z:\pdh_simulator\units\separators\membrane")

import membrane_system as ms  # the model module

# ---- trial #201 exact conditions ----
F_C3H6_kmolh = 3305.2          # membrane feed C3H6 [kmol/h]  (Dist2 bottoms, top1_trial201.txt)
F_C3H8_kmolh = 2144.3          # membrane feed C3H8 [kmol/h]
P_H   = 843657.6171376609      # [Pa]  (best.json params/P_H_Pa)
P_L   = ms._ATM_BAR * 1e5      # [Pa]  1 atm, model's fixed P_L
A_mem = 127838.27553657915     # [m^2] (best.json params/A_mem_m2)
Q_A_GPU = 40.0
alpha   = 90.0

# mol/s feed (same conversion the model uses)
F_C3H6_0 = F_C3H6_kmolh * 1000.0 / 3600.0
F_C3H8_0 = F_C3H8_kmolh * 1000.0 / 3600.0
z_feed = F_C3H6_0 / (F_C3H6_0 + F_C3H8_0)

Q_A_SI = Q_A_GPU * ms._GPU_SI       # [mol/(m2 s Pa)]  exactly as model
gamma  = P_L / P_H
Q_B    = Q_A_SI / alpha

# ---- the model's EXACT ODE rhs (copied behaviour: clip negative flux) ----
def ode(A, F):
    fc = max(F[0], 1e-12)
    fa = max(F[1], 1e-12)
    x  = fc / (fc + fa)
    y  = ms._y_local(x, alpha, gamma)        # model's own local permeate comp
    J_c = Q_A_SI * (x * P_H - y * P_L)
    J_a = Q_B    * ((1.0 - x) * P_H - (1.0 - y) * P_L)
    return [-max(J_c, 0.0), -max(J_a, 0.0)]

def event_no_flux(A, F):
    fc = max(F[0], 1e-12); fa = max(F[1], 1e-12)
    x  = fc / (fc + fa)
    y  = ms._y_local(x, alpha, gamma)
    J_c = Q_A_SI * (x * P_H - y * P_L)
    J_a = Q_B    * ((1.0 - x) * P_H - (1.0 - y) * P_L)
    return min(J_c, J_a)
event_no_flux.terminal = True
event_no_flux.direction = -1

sol = solve_ivp(
    ode, t_span=(0.0, A_mem), y0=[F_C3H6_0, F_C3H8_0],
    method='Radau', rtol=1e-4, atol=1e-7,
    max_step=max(A_mem / 200.0, 0.1),
    events=event_no_flux, dense_output=True,
)
assert sol.status != -1, "ODE integration failed"
A_end = sol.t[-1]   # event may stop before A_mem if flux depletes

# ---- sample the dense solution on a uniform area grid ----
N = 150
A_grid = np.linspace(0.0, A_end, N)
Fc = np.empty(N); Fa = np.empty(N)
for i, A in enumerate(A_grid):
    if A <= sol.t[-1]:
        y = sol.sol(A)
    else:
        y = sol.y[:, -1]
    Fc[i] = max(y[0], 0.0)
    Fa[i] = max(y[1], 0.0)

# retentate-side mole fraction at each A
x_ret = Fc / np.maximum(Fc + Fa, 1e-12)

# cumulative permeate collected from 0..A  (feed - retentate at A)
Pc_cum = F_C3H6_0 - Fc           # cumulative permeated C3H6 [mol/s]
Pa_cum = F_C3H8_0 - Fa           # cumulative permeated C3H8 [mol/s]
y_perm_cum = np.where(
    (Pc_cum + Pa_cum) > 1e-12,
    Pc_cum / np.maximum(Pc_cum + Pa_cum, 1e-12),
    z_feed,                       # at A=0 nothing permeated yet -> define = feed comp
)

# local permeate composition at each A (model's _y_local at local x)
y_perm_local = np.array([ms._y_local(x, alpha, gamma) for x in x_ret])

area_frac = A_grid / A_mem        # normalize by TOTAL design area (A_mem)

# ---- write CSV ----
out = r"Y:\pdh_slide\figures\prof_membrane.csv"
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["area_frac", "x_C3H6_ret", "y_C3H6_perm_cum", "y_C3H6_perm_local"])
    for i in range(N):
        w.writerow([f"{area_frac[i]:.6f}", f"{x_ret[i]:.6f}",
                    f"{y_perm_cum[i]:.6f}", f"{y_perm_local[i]:.6f}"])

# ---- report ----
stage_cut = (Pc_cum[-1] + Pa_cum[-1]) / (F_C3H6_0 + F_C3H8_0)
print(f"CSV written: {out}  ({N} rows)")
print(f"A_end / A_mem = {A_end:.1f} / {A_mem:.1f}  (frac={A_end/A_mem:.4f})")
print()
print("first 3 rows:")
print("  area_frac  x_ret    y_cum    y_local")
for i in range(3):
    print(f"  {area_frac[i]:.4f}    {x_ret[i]:.4f}   {y_perm_cum[i]:.4f}   {y_perm_local[i]:.4f}")
print("last 3 rows:")
for i in range(N-3, N):
    print(f"  {area_frac[i]:.4f}    {x_ret[i]:.4f}   {y_perm_cum[i]:.4f}   {y_perm_local[i]:.4f}")
print()
print("=== ENDPOINTS ===")
print(f"  retentate C3H6 at A=0     : {x_ret[0]*100:.2f} %  (feed)")
print(f"  retentate C3H6 at A=A_mem : {x_ret[-1]*100:.2f} %")
print(f"  cumulative permeate C3H6  : {y_perm_cum[-1]*100:.2f} %")
print(f"  stage cut (Fperm/Ffeed)   : {stage_cut*100:.2f} %")

# ---- cross-check against the model's own solver endpoint ----
fixed = ms.MemFixedParams(Q_A_GPU=Q_A_GPU, alpha=alpha, vapor_feed=True)
design = ms.MemDesignVars(P_H=P_H, P_L=P_L, A_mem=A_mem, P_dist=16.7e5)
feed = ms.MemFeedStream(F_C3H6=F_C3H6_kmolh, F_C3H8=F_C3H8_kmolh,
                        T_in=323.15, P_in=P_H)
res = ms.simulate_membrane_system(design, feed, fixed)
print()
print("=== MODEL simulate_membrane_system() cross-check ===")
print(f"  stage_cut   = {res.stage_cut*100:.2f} %")
print(f"  perm_purity = {res.perm_purity*100:.2f} %")
print(f"  ret_purity  = {res.ret_purity*100:.2f} %")
