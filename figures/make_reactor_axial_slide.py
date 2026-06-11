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
import matplotlib.lines as mlines
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
matplotlib.rcParams['font.size'] = 20          # スライド投影用に拡大（濃く・太く）
matplotlib.rcParams['font.weight'] = 'bold'    # 軸ラベル・目盛り文字を太く
matplotlib.rcParams['axes.labelweight'] = 'bold'
matplotlib.rcParams['axes.linewidth'] = 1.8
matplotlib.rcParams['xtick.major.width'] = 1.7
matplotlib.rcParams['ytick.major.width'] = 1.7
matplotlib.rcParams['xtick.major.size'] = 5
matplotlib.rcParams['ytick.major.size'] = 5
FIGDIR = os.path.dirname(os.path.abspath(__file__))

# ---- BO best (Catofin) 設計点・反応器入口 (exp3_202606101630 の収束解) ----
A0, B0 = 3649.2, 2070.2
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

fig, ax = plt.subplots(figsize=(7.4, 4.3))   # スライド右カラム用（横長・全高フィル）
axR = ax.twinx()
# 赤の実線（HGM補償の床温）が床温下限に張り付いた後、緑の下限線や twinx の青線の
# 下に隠れて「途中で切れた」ように見えるため、赤を最前面に出す:
#   (1) 緑の下限線は低 zorder で赤の下に敷く
#   (2) 温度軸 ax を twin 軸 axR より上に重ね、赤を青より前面にする
ax.axhline(floor_C, color='#2e7d32', lw=2.8, ls='-', zorder=2)
ax.plot(z_h, Th, color='#c0392b', lw=4.6, zorder=5)
ax.plot(z_a, Ta, color='#c0392b', lw=3.6, ls='--', zorder=4)
ax.text(Z_SHOW * 0.30, floor_C + 9, f'発熱材 床温下限 {floor_C:.0f}°C',
        color='#176e30', fontsize=17)
axR.plot(z_h, Xh, color='#1f4e79', lw=4.6)
axR.plot(z_a, Xa, color='#1f4e79', lw=3.6, ls='--')
ax.set_zorder(axR.get_zorder() + 1)   # 温度軸（赤）を転化率軸（青）より前面に
ax.patch.set_visible(False)           # 前面に出した ax の背景で axR を隠さない
ax.axvline(CAT['L_bed'], color='0.45', lw=1.8, ls=':')
ax.text(CAT['L_bed'] + 0.07, ax.get_ylim()[0] + 12, f'床末端 {CAT["L_bed"]:.2f}m',
        rotation=90, va='bottom', color='0.2', fontsize=15)
ax.set_xlabel('床軸方向位置 z [m]'); ax.set_ylabel('温度 [°C]', color='#c0392b')
axR.set_ylabel('単通転化率 [%]', color='#1f4e79')
ax.tick_params(axis='y', colors='#c0392b'); axR.tick_params(axis='y', colors='#1f4e79')
ax.set_xlim(0, Z_SHOW); axR.set_ylim(0, max(Xh.max(), Xa.max()) * 1.12)
# 凡例は色付き軸ラベル（温度=赤／単通転化率=青）と重複するため省略。
# 線種の意味のみ上部の空きスペースに明示（被り回避）。
ax.text(0.04, 0.96, '実線 発熱材補償　破線 無補償', transform=ax.transAxes,
        fontsize=16, color='0.12', va='top')
fig.tight_layout(pad=0.2)
# ベクタ PDF（スライドでぼやけない・スライドが優先採用）＋ 互換用 PNG
fig.savefig(os.path.join(FIGDIR, 'reactor_axial_TX.pdf'), bbox_inches='tight', pad_inches=0.01)
fig.savefig(os.path.join(FIGDIR, 'reactor_axial_TX.png'), dpi=400, bbox_inches='tight', pad_inches=0.01)
print('saved reactor_axial_TX.pdf/.png')

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

fig, ax = plt.subplots(figsize=(7.4, 4.3))   # TX と同寸・横長
ax.plot(zrel, Sdiff, color='#1f4e79', lw=4.6, label='微分選択率 $r_1/(r_1+r_2)$')
ax.plot(zrel, Sint,  color='#c0392b', lw=4.6, label='累積選択率')
S_exit0 = Sint[-1]
ax.axhline(S_REF, color='0.5', lw=1.8, ls=':')
ax.text(0.5, 99.3, f'サイクル時間平均 S={S_REF:.1f}%  失活込',
        color='0.18', fontsize=15, ha='center', va='top')
ax.set_xlabel('床内 相対位置 z / $L_{bed}$ [-]'); ax.set_ylabel('選択率 [%]')
ax.set_xlim(0, 1); ax.set_ylim(min(np.nanmin(Sdiff), S_REF) - 2.5, 100)
ax.legend(loc='lower left', fontsize=16, framealpha=1.0)
fig.tight_layout(pad=0.2)
fig.savefig(os.path.join(FIGDIR, 'reactor_axial_selectivity.pdf'), bbox_inches='tight', pad_inches=0.01)
fig.savefig(os.path.join(FIGDIR, 'reactor_axial_selectivity.png'), dpi=400, bbox_inches='tight', pad_inches=0.01)
print('saved reactor_axial_selectivity.pdf/.png')

# =====================================================================
# 図3: 上下結合・x軸共有版（床内 相対位置 z/L_bed = 0〜1 に統一）
#   上 = 温度(左軸)・単通転化率(右軸)、下 = 選択率。x軸は下サブプロットのみ表示。
#   上図は実床(0〜L_bed)のみに再積分（床外は描かない）→ 下図と完全に同一の x 軸。
#   床末端は z/L_bed=1（右端）。実床長は L_bed=1.58 m、浅床比 L_bed/D≈0.147。
# =====================================================================
zc_h, Yc_h, _ = integrate_axial(CAT, hgm=True,  t_min=0.0, z_max=CAT['L_bed'])
zc_a, Yc_a, _ = integrate_axial(CAT, hgm=False, t_min=0.0, z_max=CAT['L_bed'])
xr_h = zc_h / CAT['L_bed']; xr_a = zc_a / CAT['L_bed']
Xch = (FA0_pv - Yc_h[0]) / FA0_pv * 100.0; Tch = Yc_h[6] - 273.15
Xca = (FA0_pv - Yc_a[0]) / FA0_pv * 100.0; Tca = Yc_a[6] - 273.15

figC, (axT, axS) = plt.subplots(
    2, 1, sharex=True, figsize=(7.4, 7.4),
    gridspec_kw=dict(height_ratios=[1, 1], hspace=0.16))

# --- 上: 温度(左) ・ 単通転化率(右) ---
# 赤の実線（HGM補償の床温）は下限到達後に緑の下限線・青線と重なって途切れて見える
# ため、緑を低 zorder で下に敷き、温度軸ごと twin 軸より前面に出して赤を最上面にする。
axTR = axT.twinx()
axT.axhline(floor_C, color='#2e7d32', lw=2.6, ls='-', zorder=2)
axT.plot(xr_h, Tch, color='#c0392b', lw=4.6, zorder=5)
axT.plot(xr_a, Tca, color='#c0392b', lw=3.6, ls='--', zorder=4)
axT.text(0.30, floor_C + 9, f'発熱材 床温下限 {floor_C:.0f}°C', color='#176e30', fontsize=16)
axTR.plot(xr_h, Xch, color='#1f4e79', lw=4.6)
axTR.plot(xr_a, Xca, color='#1f4e79', lw=3.6, ls='--')
axT.set_zorder(axTR.get_zorder() + 1)   # 温度軸（赤）を転化率軸（青）より前面に
axT.patch.set_visible(False)            # 前面に出した axT の背景で axTR を隠さない
axT.set_ylabel('温度 [°C]', color='#c0392b')
axTR.set_ylabel('単通転化率 [%]', color='#1f4e79')
axT.tick_params(axis='y', colors='#c0392b'); axTR.tick_params(axis='y', colors='#1f4e79')
axTR.set_ylim(0, max(Xch.max(), Xca.max()) * 1.12)
axT.text(0.04, 0.96, '実線 発熱材補償　破線 無補償', transform=axT.transAxes,
         fontsize=15, color='0.12', va='top')
axT.set_title('床内の温度・単通転化率', fontsize=18, fontweight='bold', pad=4)

# --- 下: 選択率（微分・累積）---
axS.plot(zrel, Sdiff, color='#1f4e79', lw=4.6, label='微分選択率 $r_1/(r_1+r_2)$')
axS.plot(zrel, Sint,  color='#c0392b', lw=4.6, label='累積選択率')
axS.axhline(S_REF, color='0.5', lw=1.8, ls=':')
axS.text(0.60, 99.3, f'平均 S={S_REF:.1f}%（失活込）', color='0.18', fontsize=14, ha='center', va='top')
axS.set_ylabel('選択率 [%]')
axS.set_ylim(min(np.nanmin(Sdiff), S_REF) - 2.5, 100)
axS.legend(loc='lower left', fontsize=14, framealpha=1.0)
axS.set_title('床内の選択率', fontsize=18, fontweight='bold', pad=4)

# --- 共有 x 軸（下サブプロットのみラベル）---
axS.set_xlabel('床内 相対位置 $z/L_{bed}$ [-]')

# --- 床末端（z/L_bed = 1 ＝ 実床長 1.58 m）を上下サブプロットで縦線連結 ---
#   相対位置の右端が実床の末端であることを明示し、上下図を同一位置でつなぐ。
from matplotlib.patches import ConnectionPatch
for _a in (axT, axS):
    _a.set_xlim(0, 1.05)
    _a.axvline(1.0, color='0.5', lw=1.6, ls=(0, (5, 4)), zorder=1.5)
_con = ConnectionPatch(
    xyA=(1.0, axT.get_ylim()[0]), coordsA=axT.transData,
    xyB=(1.0, axS.get_ylim()[1]), coordsB=axS.transData,
    color='0.5', lw=1.6, ls=(0, (5, 4)), zorder=1.5)
figC.add_artist(_con)
axT.text(0.985, 0.45, '床末端 $z/L_{bed}{=}1$',
         transform=axT.get_xaxis_transform(), rotation=90,
         ha='right', va='center', color='0.32', fontsize=13)

# --- HGM 補償開始点を上下貫通の縦線で明示 ---
#   床温が下限 (T_in−ΔT_max) に到達して dT/dz=0 にクランプされる位置。
#   下段の微分選択率の折れ曲がりは「ここで温度低下が止まり速度定数が一定になる」
#   ことに対応するため、床末端と同様に上下サブプロットを縦線でつなぐ。
if Tch.min() <= floor_C + 0.5:
    x_hgm = float(xr_h[int(np.argmax(Tch <= floor_C + 0.5))])
    for _a in (axT, axS):
        _a.axvline(x_hgm, color='#2e7d32', lw=1.6, ls=(0, (5, 4)), zorder=1.5)
    _con_hgm = ConnectionPatch(
        xyA=(x_hgm, axT.get_ylim()[0]), coordsA=axT.transData,
        xyB=(x_hgm, axS.get_ylim()[1]), coordsB=axS.transData,
        color='#2e7d32', lw=1.6, ls=(0, (5, 4)), zorder=1.5)
    figC.add_artist(_con_hgm)
    axS.text(x_hgm + 0.015, 0.975, '発熱材 補償開始',
             transform=axS.get_xaxis_transform(),
             ha='left', va='top', color='#176e30', fontsize=13)

figC.tight_layout(pad=0.2)
figC.savefig(os.path.join(FIGDIR, 'reactor_axial_combined.pdf'), bbox_inches='tight', pad_inches=0.01)
figC.savefig(os.path.join(FIGDIR, 'reactor_axial_combined.png'), dpi=400, bbox_inches='tight', pad_inches=0.01)
print('saved reactor_axial_combined.pdf/.png')
