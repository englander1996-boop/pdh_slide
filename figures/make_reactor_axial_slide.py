# -*- coding: utf-8 -*-
"""スライド8（反応器プロファイル）用 内部プロファイル図の生成。

monitor/reactor_axial_profile.ipynb の積分機構（cell0,1）をそのまま流用し、
スライド投影用に (a) 埋め込みタイトルを削除（スライド側の太字見出しと重複回避）、
(b) フォント拡大・図を小さめにして相対的に大きく、(c) dpi=300 で出力する。
データ・式・色は notebook と同一（trial #201, Catofin 浅床軸流スイング）。

実行: Z:\\pdh_simulator\\.venv\\Scripts\\python.exe figures\\make_reactor_axial_slide.py
出力: figures/reactor_axial_TX.png, figures/reactor_axial_selectivity.png
"""
import os, sys, math, warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

ROOT = r"Z:\pdh_simulator"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from units.reactors.swing import (
    _ode_axial, calc_a, calc_rate_constants, _COMPS, FixedParams,
    FeedStream,
)
from units.reactors.catofin import CatofinDesignVars, simulate_catofin_reactor_system

# --- 図スタイル（rule.md準拠：グリッドなし・目盛り内向き・日本語フォント）---
for _f in ['Yu Gothic', 'Meiryo', 'MS Gothic', 'Noto Sans CJK JP']:
    if any(_f.lower() == e.name.lower() for e in matplotlib.font_manager.fontManager.ttflist):
        matplotlib.rcParams['font.family'] = _f; break
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['axes.grid'] = False
matplotlib.rcParams['xtick.direction'] = 'in'; matplotlib.rcParams['ytick.direction'] = 'in'
matplotlib.rcParams['xtick.top'] = True; matplotlib.rcParams['ytick.right'] = True
matplotlib.rcParams['font.size'] = 15          # スライド投影用に拡大
matplotlib.rcParams['axes.linewidth'] = 1.1
FIGDIR = os.path.dirname(os.path.abspath(__file__))

# ---- BO best #201 (Catofin) 設計点・反応器入口 ----
A0, B0 = 3612.5, 2128.8
F_IN_SYS = {'A': A0, 'B': B0, 'C': 0., 'D': 0., 'E': 0., 'F': 0.}
T_IN   = 935.15
P      = 50000.0
T_FEED = 307.0
CAT = dict(T_in=T_IN, t_cyc=14.005, D=10.763, L_bed=1.577, N_online=7, d_p=0.005843)

DT_MAX  = float(os.environ.get('PDH_CATOFIN_DTMAX',  '50'))
PHI_CAT = float(os.environ.get('PDH_CATOFIN_PHI_CAT','0.85'))
D_EFF   = float(os.environ.get('PDH_CATOFIN_DEFF',   '1e-5'))
_FX = FixedParams()
EPS, EPS_BED, SPH = _FX.eps, _FX.eps_bed, _FX.sphericity

N_ON = CAT['N_online']
F_IN_PV = {c: F_IN_SYS[c] / N_ON for c in _COMPS}
FA0_pv  = F_IN_PV['A'] * 1000.0 / 3600.0
FB0_pv  = F_IN_PV['B'] * 1000.0 / 3600.0


def integrate_axial(design, *, hgm=True, t_min=0.0, n_z=240, z_max=None):
    a = calc_a(t_min, design['T_in'], P)
    A_cross = math.pi / 4.0 * design['D']**2
    y0 = np.concatenate([
        np.array([F_IN_PV[c] * 1000.0 / 3600.0 for c in _COMPS]),
        [design['T_in']], [P],
    ])
    t_floor = (design['T_in'] - DT_MAX) if hgm else None
    phi     = PHI_CAT if hgm else 1.0
    deff    = D_EFF   if hgm else None
    L = design['L_bed'] if z_max is None else z_max
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        sol = solve_ivp(
            lambda z, y: _ode_axial(z, y, a, A_cross, EPS, EPS_BED, design['d_p'], SPH, 1,
                                    t_floor_K=t_floor, phi_cat=phi, d_eff=deff),
            (0.0, L), y0, method='Radau', rtol=1e-7, atol=1e-9, dense_output=True)
    zz = np.linspace(0.0, L, n_z)
    Y = np.array([sol.sol(z) for z in zz]).T
    Y[:6] = np.maximum(Y[:6], 0.0)
    return zz, Y, a


def rates_at(y, a):
    F = np.maximum(y[:6], 0.0); T = float(np.clip(y[6], 300., 1500.)); Pl = max(float(y[7]), 1e3)
    Ft = float(F.sum())
    if Ft <= 0: return 0., 0., 0.
    Pp = {c: max(float(F[i]) / Ft * Pl, 0.0) for i, c in enumerate(_COMPS)}
    rc = calc_rate_constants(T)
    K_B = max(rc['K_B'], 1.0); K_eq = max(rc['K_eq'], 1.0)
    r1 = a * rc['k1'] * (Pp['A'] - Pp['B'] * Pp['C'] / K_eq) / (1.0 + Pp['B'] / K_B)
    r2 = rc['k2'] * Pp['A']
    r3 = rc['k3'] * Pp['D'] * Pp['C']
    return r1, r2, r3


with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    _ref = simulate_catofin_reactor_system(CatofinDesignVars(**CAT),
                                           FeedStream(F_in=F_IN_SYS, T_feed=T_FEED, P_in=P))
X_REF, S_REF = _ref.performance.Conversion, _ref.performance.Selectivity
print(f'設計点 #201: X={X_REF:.1f}%  S={S_REF:.1f}%')

# =====================================================================
# 図1: 軸方向 T(z)・X(z)  HGM補償 vs 無補償（タイトル無し）
# =====================================================================
Z_SHOW = max(2.5, CAT['L_bed'] * 2.4)
z_h, Yh, a0 = integrate_axial(CAT, hgm=True,  t_min=0.0, z_max=Z_SHOW)
z_a, Ya, _  = integrate_axial(CAT, hgm=False, t_min=0.0, z_max=Z_SHOW)
Xh = (FA0_pv - Yh[0]) / FA0_pv * 100.0;  Th = Yh[6] - 273.15
Xa = (FA0_pv - Ya[0]) / FA0_pv * 100.0;  Ta = Ya[6] - 273.15
floor_C = T_IN - 273.15 - DT_MAX

fig, ax = plt.subplots(figsize=(6.6, 4.5))
axR = ax.twinx()
lT_h, = ax.plot(z_h, Th, color='#c0392b', lw=2.8, label='温度  HGM補償')
lT_a, = ax.plot(z_a, Ta, color='#c0392b', lw=2.2, ls='--', label='温度  無補償')
ax.axhline(floor_C, color='#2e7d32', lw=1.6, ls='-')
ax.text(Z_SHOW * 0.50, floor_C + 4, f'HGM床温下限 {floor_C:.0f}°C',
        color='#2e7d32', fontsize=12)
lX_h, = axR.plot(z_h, Xh, color='#1f4e79', lw=2.8, label='転化率  HGM補償')
lX_a, = axR.plot(z_a, Xa, color='#1f4e79', lw=2.2, ls='--', label='転化率  無補償')
ax.axvline(CAT['L_bed'], color='0.45', lw=1.3, ls=':')
ax.text(CAT['L_bed'] + 0.05, ax.get_ylim()[0] + 8, f'床末端 {CAT["L_bed"]:.2f}m',
        rotation=90, va='bottom', color='0.4', fontsize=11)
ax.set_xlabel('床軸方向位置 z [m]'); ax.set_ylabel('温度 [°C]', color='#c0392b')
axR.set_ylabel('単通転化率 [%]', color='#1f4e79')
ax.tick_params(axis='y', colors='#c0392b'); axR.tick_params(axis='y', colors='#1f4e79')
ax.set_xlim(0, Z_SHOW); axR.set_ylim(0, max(Xh.max(), Xa.max()) * 1.12)
ax.legend(handles=[lT_h, lT_a, lX_h, lX_a], loc='center right',
          fontsize=11.5, framealpha=1.0)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, 'reactor_axial_TX.png'), dpi=300, bbox_inches='tight')
print('saved reactor_axial_TX.png')

# =====================================================================
# 図2: 軸方向 選択率（微分・累積、タイトル無し）
# =====================================================================
z, Y, a = integrate_axial(CAT, hgm=True, t_min=0.0)
Sdiff, Sint = [], []
for k in range(len(z)):
    r1, r2, r3 = rates_at(Y[:, k], a)
    Sdiff.append(r1 / (r1 + r2) * 100.0 if (r1 + r2) > 0 else np.nan)
    dA = FA0_pv - Y[0, k]; dB = Y[1, k] - FB0_pv
    Sint.append(dB / dA * 100.0 if dA > 1e-12 else np.nan)
Sdiff = np.array(Sdiff); Sint = np.array(Sint)
zrel = z / CAT['L_bed']

fig, ax = plt.subplots(figsize=(6.6, 4.0))
ax.plot(zrel, Sdiff, color='#1f4e79', lw=2.8, label='微分選択率 $r_1/(r_1+r_2)$')
ax.plot(zrel, Sint,  color='#c0392b', lw=2.8, label='累積選択率')
S_exit0 = Sint[-1]
ax.axhline(S_REF, color='0.5', lw=1.2, ls=':')
ax.text(0.97, S_REF - 2.0, f'サイクル時間平均 S={S_REF:.1f}%  失活込',
        color='0.4', fontsize=11, ha='right')
ax.set_xlabel('床内 相対位置 z / $L_{bed}$ [-]'); ax.set_ylabel('選択率 [%]')
ax.set_xlim(0, 1); ax.set_ylim(min(np.nanmin(Sdiff), S_REF) - 2.5, 100)
ax.legend(loc='lower left', fontsize=11.5, framealpha=1.0)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, 'reactor_axial_selectivity.png'), dpi=300, bbox_inches='tight')
print('saved reactor_axial_selectivity.png')
