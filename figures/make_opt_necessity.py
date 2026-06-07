# -*- coding: utf-8 -*-
r"""make_opt_necessity.py — スライド15用「23変数を同時最適化する必要性」を主張する図。

実データ出典:
  Z:\pdh_simulator\outputs\main_20260605_170938\trials.csv  (TPE 300 試行, 最良 #201)
  - value=TAC_eff(penalty込), attr.TAC_hi_okuyen=HI後TAC, attr.is_feasible

生成物 (ベクトル PDF, JP フォント埋込):
  fig_var_importance.pdf : 23 変数の fANOVA 重要度を工程別に色分け
                           → 重要度が全工程に分散 = どの変数も無視できない
  fig_opt_history.pdf    : TAC vs 試行。可行 100/300、最良#201。
                           → 制約で可行域が狭く、23 次元の誘導探索が要る

実行:
  Z:\pdh_simulator\.venv\Scripts\python.exe make_opt_necessity.py
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# ---- JP フォント (deck と整合する Gothic を優先) ----
for _cand in ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP", "HaranoAjiGothic"]:
    try:
        font_manager.findfont(_cand, fallback_to_default=False)
        matplotlib.rcParams["font.family"] = _cand
        print(f"[font] {_cand}")
        break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["pdf.fonttype"] = 42        # TrueType 埋込 (ボヤけ防止・ベクトル)
matplotlib.rcParams["xtick.direction"] = "in"
matplotlib.rcParams["ytick.direction"] = "in"
matplotlib.rcParams["xtick.top"] = True
matplotlib.rcParams["ytick.right"] = True

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = r"Z:\pdh_simulator\outputs\main_20260605_170938\trials.csv"

# ---- 23 変数: 列名 → (記号ラベル, 工程) ----  記号は slide14 の探索範囲表で定義済み
# 工程: rx=反応器, psa=PSA, mem=膜, feed=原料, d1/d2/d3=蒸留塔
VARS = [
    ("T_in_K",              "$T_{in}$",     "rx"),
    ("t_cyc_min",           "$t_{cyc}$",    "rx"),
    ("D_reactor_m",         "$D$",          "rx"),
    ("L_bed_m",             "$L_{bed}$",    "rx"),
    ("N_online",            "$N_{on}$",     "rx"),
    ("d_p_mm",              "$d_p$",        "rx"),
    ("D_psa_col_m",         "$D_P$",        "psa"),
    ("L_psa_bed_m",         "$L_P$",        "psa"),
    ("desorption_target",   "$\\beta$",      "psa"),
    ("P_H_Pa",              "$P_H$",        "mem"),
    ("A_mem_m2",            "$A_{mem}$",    "mem"),
    ("F_C3H8_fresh_kmol_h", "$F_{fresh}$",  "feed"),
    ("col1_p_kpa",          "$P_1$",        "d1"),
    ("col1_n_stages",       "$N_1$",        "d1"),
    ("col1_feed_stage",     "$N_{f1}$",     "d1"),
    ("col1_comp_frac_2",    "$\\phi_1$",     "d1"),
    ("col2_p_kpa",          "$P_2$",        "d2"),
    ("col2_n_stages",       "$N_2$",        "d2"),
    ("col2_feed_ratio",     "$f_2$",        "d2"),
    ("col2_reflux_ratio",   "$R_2$",        "d2"),
    ("col3_p_kpa",          "$P_3$",        "d3"),
    ("col3_n_stages",       "$N_3$",        "d3"),
    ("col3_feed_ratio",     "$f_3$",        "d3"),
]
# 探索範囲 (SEARCH_SPACE と一致)。(low, high, is_int, is_log)
BOUNDS = {
    "T_in_K": (930.0, 940.0, False, False),
    "t_cyc_min": (12.0, 25.0, False, False),
    "D_reactor_m": (9.0, 12.0, False, False),
    "L_bed_m": (0.3, 3.0, False, False),
    "N_online": (6, 8, True, False),
    "d_p_mm": (4.0, 6.0, False, False),
    "D_psa_col_m": (2.9, 5.0, False, False),
    "L_psa_bed_m": (22.0, 30.0, False, False),
    "desorption_target": (0.22, 0.40, False, False),
    "P_H_Pa": (7.5e5, 9.5e5, False, False),
    "A_mem_m2": (5.0e4, 3.0e5, False, True),
    "F_C3H8_fresh_kmol_h": (1450.0, 1750.0, False, False),
    "col1_p_kpa": (1600.0, 2000.0, False, False),
    "col1_n_stages": (30, 60, True, False),
    "col1_feed_stage": (22, 28, True, False),
    "col1_comp_frac_2": (0.90, 0.999, False, False),
    "col2_p_kpa": (770.0, 820.0, False, False),
    "col2_n_stages": (60, 80, True, False),
    "col2_feed_ratio": (0.40, 0.60, False, False),
    "col2_reflux_ratio": (10.0, 15.0, False, False),
    "col3_p_kpa": (1600.0, 1900.0, False, False),
    "col3_n_stages": (115, 160, True, False),
    "col3_feed_ratio": (0.60, 0.90, False, False),
}
# 工程 → (色, 凡例名)。色は意味(工程)を担う。
PROC = {
    "rx":   ("#1F5FC4", "反応器"),
    "psa":  ("#7A4FB5", "PSA"),
    "mem":  ("#1FB24D", "膜分離"),
    "feed": ("#C0392B", "原料"),
    "d1":   ("#E8821E", "蒸留塔"),
    "d2":   ("#E8821E", "蒸留塔"),
    "d3":   ("#E8821E", "蒸留塔"),
}

df = pd.read_csv(CSV)
feas = df[df["attr.is_feasible"] == True].dropna(subset=["attr.TAC_hi_okuyen"]).copy()
print(f"feasible n={len(feas)}")

# =====================================================================
# Fig 1: fANOVA 変数重要度 (可行試行・目的=HI後TAC)
# =====================================================================
import optuna
from optuna.distributions import FloatDistribution, IntDistribution
from optuna.trial import create_trial
from optuna.importance import FanovaImportanceEvaluator

dists = {}
for name, (lo, hi, is_int, is_log) in BOUNDS.items():
    if is_int:
        dists[name] = IntDistribution(int(lo), int(hi))
    else:
        dists[name] = FloatDistribution(float(lo), float(hi), log=is_log)

study = optuna.create_study(direction="minimize")
trials = []
for _, r in feas.iterrows():
    params = {}
    for name, (lo, hi, is_int, is_log) in BOUNDS.items():
        v = r[name]
        params[name] = int(round(v)) if is_int else float(v)
    trials.append(create_trial(params=params, distributions=dists,
                               value=float(r["attr.TAC_hi_okuyen"])))
study.add_trials(trials)

imp = optuna.importance.get_param_importances(
    study, evaluator=FanovaImportanceEvaluator(seed=0))
print("importances:", {k: round(v, 3) for k, v in imp.items()})

label_of = {n: lab for n, lab, _ in VARS}
proc_of = {n: p for n, _, p in VARS}
names = list(imp.keys())
vals = np.array([imp[n] for n in names]) * 100.0   # %
order = np.argsort(vals)                            # 昇順 (barh は下から)
names = [names[i] for i in order]
vals = vals[order]
labels = [label_of[n] for n in names]
colors = [PROC[proc_of[n]][0] for n in names]

fig, ax = plt.subplots(figsize=(4.3, 6.5))   # 縦長: スライド左パネル用
y = np.arange(len(names))
ax.barh(y, vals, color=colors, height=0.78, edgecolor="white", linewidth=0.4)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=15)
ax.set_ylim(-0.7, len(names) - 0.3)
ax.set_xlabel("TAC への寄与度 fANOVA [%]", fontsize=14)
ax.set_xlim(0, max(vals) * 1.17)
for yi, v in zip(y, vals):
    ax.text(v + max(vals) * 0.015, yi, f"{v:.0f}", va="center", ha="left", fontsize=12)
ax.tick_params(axis="x", labelsize=12)
# 凡例 (工程, 重複排除)
seen, handles = set(), []
from matplotlib.patches import Patch
for p in ["rx", "mem", "d1", "psa", "feed"]:
    c, nm = PROC[p]
    if nm in seen:
        continue
    seen.add(nm)
    handles.append(Patch(facecolor=c, label=nm))
ax.legend(handles=handles, loc="lower right", fontsize=12.5, frameon=True,
          title="工程", title_fontsize=12.5, handlelength=1.1, handleheight=1.1,
          borderpad=0.4, labelspacing=0.3)
fig.tight_layout(pad=0.3)
out1 = os.path.join(HERE, "fig_var_importance.pdf")
fig.savefig(out1, bbox_inches="tight", pad_inches=0.02)
print("wrote", out1)

# =====================================================================
# Fig 2: 探索履歴 (TAC vs 試行)
# =====================================================================
all_n = df["number"].values
is_feas = df["attr.is_feasible"].fillna(False).values.astype(bool)
tac_hi = df["attr.TAC_hi_okuyen"].values

fn = all_n[is_feas]
ft = tac_hi[is_feas]
# 可行のみで run しの最良 (試行番号順)
ordn = np.argsort(fn)
fn_s, ft_s = fn[ordn], ft[ordn]
run_best = np.minimum.accumulate(ft_s)
best_i = int(np.argmin(ft_s))
best_n, best_t = int(fn_s[best_i]), float(ft_s[best_i])

fig2, ax2 = plt.subplots(figsize=(5.0, 2.4))   # スライド右上パネル用 (横長)
top = np.nanmax(ft) * 1.03
# 不可行: 上部の帯に灰色 × (制約違反で評価不能/罰則大)
infn = all_n[~is_feas]
ax2.scatter(infn, np.full_like(infn, top, dtype=float), marker="x",
            s=13, c="#B0B0B0", linewidths=0.7, label="不可行 200")
# 可行点
ax2.scatter(fn, ft, s=18, c="#1FB24D", edgecolors="white", linewidths=0.3,
            label="可行 100", zorder=3)
# run しの最良
ax2.step(fn_s, run_best, where="post", color="black", linewidth=1.7,
         label="逐次最良", zorder=4)
# 最良点
ax2.scatter([best_n], [best_t], marker="*", s=300, c="#C0392B",
            edgecolors="black", linewidths=0.6, zorder=5)
ax2.annotate(f"最良 #{best_n}  TAC {best_t:.0f}",
             xy=(best_n, best_t), xytext=(best_n - 150, best_t + 58),
             fontsize=12, fontweight="bold", color="#C0392B",
             arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.2))
ax2.set_xlabel("試行番号 (TPE, 全 300)", fontsize=13)
ax2.set_ylabel("TAC [億円/年]", fontsize=13)
ax2.set_xlim(-6, 305)
ax2.tick_params(labelsize=11.5)
ax2.legend(loc="upper right", fontsize=11, frameon=True, ncol=1,
           handletextpad=0.4, labelspacing=0.3, borderpad=0.3)
fig2.tight_layout(pad=0.3)
out2 = os.path.join(HERE, "fig_opt_history.pdf")
fig2.savefig(out2, bbox_inches="tight", pad_inches=0.02)
print("wrote", out2)
print("DONE")
