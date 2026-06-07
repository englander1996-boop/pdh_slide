# -*- coding: utf-8 -*-
"""スライド9（反応器分析）用の2図。
 (1) reactor_pressure_eq : 平衡転化率の圧力依存（純プロパン基準・等温）。
       モル数増加反応 C3H8⇌C3H6+H2 ゆえ低圧ほど平衡転化率が高い → 0.5bar 妥当性を一目で。
 (2) reactor_smax_T      : 固有選択率上限 S_max=k1/(k1+k2) の温度依存（選択率の天井）。
       Ea2≫Ea1 で昇温ほど低下。温度のみで決まる上限。
data: src.thermo.calc_keq / src.kinetics _k1,_k2（シミュレータ・コンテスト所与）。
スライド用に太字・大フォント・太線・ベクタPDF出力。
実行: Z:\\pdh_simulator\\.venv\\Scripts\\python.exe figures\\make_reactor_analysis_figs.py
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import brentq

SIM = r"Z:\pdh_simulator"
if SIM not in sys.path:
    sys.path.insert(0, SIM)
from src.thermo import PDHThermo
from src.kinetics import PDHKinetics
th = PDHThermo(); kin = PDHKinetics()

for _f in ['Yu Gothic', 'Meiryo', 'MS Gothic', 'Noto Sans CJK JP']:
    try:
        matplotlib.font_manager.findfont(_f, fallback_to_default=False)
        matplotlib.rcParams['font.family'] = _f; break
    except Exception:
        continue
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['axes.grid'] = False
matplotlib.rcParams['xtick.direction'] = 'in'; matplotlib.rcParams['ytick.direction'] = 'in'
matplotlib.rcParams['xtick.top'] = True; matplotlib.rcParams['ytick.right'] = True
matplotlib.rcParams['font.size'] = 20
matplotlib.rcParams['font.weight'] = 'bold'
matplotlib.rcParams['axes.labelweight'] = 'bold'
matplotlib.rcParams['axes.linewidth'] = 1.8
matplotlib.rcParams['xtick.major.width'] = 1.7
matplotlib.rcParams['ytick.major.width'] = 1.7
matplotlib.rcParams['xtick.major.size'] = 5
matplotlib.rcParams['ytick.major.size'] = 5
FIGDIR = os.path.dirname(os.path.abspath(__file__))


def _save(fig, name):
    fig.tight_layout(pad=0.2)
    fig.savefig(os.path.join(FIGDIR, name + '.pdf'), bbox_inches='tight', pad_inches=0.01)
    fig.savefig(os.path.join(FIGDIR, name + '.png'), dpi=400, bbox_inches='tight', pad_inches=0.01)
    print('saved', name)


# ===== (1) 平衡転化率 vs 圧力（純プロパン基準・等温）=====
T_EQ = 873.15   # 600℃ 代表反応温度


def X_eq_pure(P_pa, T):
    Keq = th.calc_keq(T)
    def g(xi):  # A0=1 基準: P*xi^2/(1-xi^2) = Keq
        return P_pa * xi * xi / (1.0 - xi * xi) - Keq
    if g(1e-9) > 0:
        return 0.0
    return brentq(g, 1e-9, 1 - 1e-9) * 100.0


Pbar = np.linspace(0.1, 5.0, 240)
Xeq = np.array([X_eq_pure(p * 1e5, T_EQ) for p in Pbar])
X_05 = X_eq_pure(0.5e5, T_EQ)
X_1 = X_eq_pure(1.0e5, T_EQ)
X_5 = X_eq_pure(5.0e5, T_EQ)
print(f'[press] 600C  0.5bar={X_05:.1f}%  1bar={X_1:.1f}%  5bar={X_5:.1f}%')

fig, ax = plt.subplots(figsize=(7.6, 4.0))
ax.plot(Pbar, Xeq, color='teal', lw=4.8, solid_capstyle='round')
ax.axvline(0.5, color='#c0392b', lw=2.6, ls='--')
ax.plot(0.5, X_05, 'o', color='#c0392b', ms=17, zorder=5,
        markeredgecolor='white', markeredgewidth=1.5)
ax.annotate(f'0.5 bar　{X_05:.0f}%', xy=(0.5, X_05), xytext=(0.95, 80),
            fontsize=20, color='#c0392b', fontweight='bold', ha='left', va='center',
            arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=2.4))
ax.text(2.55, 40, f'1 bar {X_1:.0f}%　／　5 bar {X_5:.0f}%',
        fontsize=16, color='0.3', ha='left', va='center')
ax.set_xlabel('圧力 [bar]'); ax.set_ylabel('平衡転化率 [%]')
ax.set_xlim(0, 5); ax.set_ylim(0, 100)
_save(fig, 'reactor_pressure_eq')


# ===== (2) 固有選択率上限 S_max=k1/(k1+k2) vs 温度 =====
Tc = np.linspace(450, 800, 320)
Tk = Tc + 273.15
k1 = np.array([kin._k1(t) for t in Tk])
k2 = np.array([kin._k2(t) for t in Tk])
Smax = k1 / (k1 + k2) * 100.0
def smax_at(tc):
    return kin._k1(tc + 273.15) / (kin._k1(tc + 273.15) + kin._k2(tc + 273.15)) * 100.0
print(f'[smax] 520C={smax_at(520):.1f}%  662C={smax_at(662):.1f}%  750C={smax_at(750):.1f}%')

fig2, ax2 = plt.subplots(figsize=(7.6, 4.0))
ax2.plot(Tc, Smax, color='#1f4e79', lw=4.8, solid_capstyle='round')
# 運転温度帯（床温 612〜入口 662℃）を帯で
ax2.axvspan(612, 662, color='#1f4e79', alpha=0.12)
for tt in (520, 750):
    ax2.plot(tt, smax_at(tt), 'o', color='#c0392b', ms=14, zorder=5,
             markeredgecolor='white', markeredgewidth=1.3)
ax2.annotate(f'520℃ {smax_at(520):.0f}%', xy=(520, smax_at(520)),
             xytext=(455, smax_at(520) - 16), fontsize=17, color='#c0392b', fontweight='bold',
             arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=2.0))
ax2.annotate(f'750℃ {smax_at(750):.0f}%', xy=(750, smax_at(750)),
             xytext=(640, smax_at(750) - 16), fontsize=17, color='#c0392b', fontweight='bold',
             arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=2.0))
ax2.text(637, 101, '運転帯', fontsize=15, color='#1f4e79', ha='center', va='bottom')
ax2.set_xlabel('温度 [℃]'); ax2.set_ylabel('固有選択率上限 $S_{max}$ [%]')
ax2.set_xlim(450, 800); ax2.set_ylim(60, 100)
_save(fig2, 'reactor_smax_T')
