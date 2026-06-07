# -*- coding: utf-8 -*-
r"""run_interaction_grid.py — スライド15用「相互作用=斜め谷」の 2D TAC マップ用データ生成。

trial #201 の最良設計を背景に、脱エタン塔(Dist2)の段数 N2 と還流比 R2 だけを 2D グリッドで
振り、全フローシート評価(HYSYS)で TAC_hi(HI後) と可行性を記録する。多段化すれば還流(=リボイラ
熱)を減らせ、その逆も成り立つ → 最小 TAC は両者の組合せ(斜め谷)。個別に最適化できない実証。

出力: fig_interaction_grid.csv  (N2, R2, feasible, TAC_hi, eff_TAC, reason)。逐次追記で保存。
実行: Z:\pdh_simulator\.venv\Scripts\python.exe run_interaction_grid.py
"""
import sys, os, time, csv
SIM = r"Z:\pdh_simulator"
if SIM not in sys.path:
    sys.path.insert(0, SIM)
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import main
from flowsheet import evaluate

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fig_interaction_grid.csv")

# --- 背景 = trial #201 の全23変数 ---
df = pd.read_csv(r"Z:\pdh_simulator\outputs\main_20260605_170938\trials.csv")
row = df[df["number"] == 201].iloc[0]
KEYS = ["T_in_K","t_cyc_min","D_reactor_m","L_bed_m","N_online","d_p_mm",
        "D_psa_col_m","L_psa_bed_m","desorption_target","P_H_Pa","A_mem_m2",
        "F_C3H8_fresh_kmol_h","col1_p_kpa","col1_n_stages","col1_feed_stage",
        "col1_comp_frac_2","col2_p_kpa","col2_n_stages","col2_feed_ratio",
        "col2_reflux_ratio","col3_p_kpa","col3_n_stages","col3_feed_ratio"]
INTS = {"N_online","col1_n_stages","col1_feed_stage","col2_n_stages","col3_n_stages"}
BASE = {k: (int(round(row[k])) if k in INTS else float(row[k])) for k in KEYS}

# --- グリッド: T_in (入口温度) × L_bed (浅床厚) ---
# どちらも #201 で範囲内部に最適点を持つ(T_in=935∈[930,940], L_bed=1.58∈[0.3,3.0])。
# 目標転化率は「床を厚く」or「高温」で達成でき等転化率線は斜め。だが高温は選択率を損なう
# ため、最小 TAC の谷は等転化率線に沿って斜めに走る = 両者は独立に選べない(相互作用)。
TIN_GRID  = [round(930.0 + (940.0-930.0)/10*i, 1) for i in range(11)]   # 930..940 (11)
LBED_GRID = [round(0.70 + (1.95-0.70)/10*i, 3) for i in range(11)]       # 0.70..1.95 (11)

def eval_point(tin, lbed):
    p = dict(BASE)
    p["T_in_K"] = float(tin)
    p["L_bed_m"] = float(lbed)
    design = main._build_design(p)
    res = evaluate(design, main._CONFIG, verbose=False, apply_hi=main.APPLY_HI,
                   hi_dT_min_K=main.HI_DT_MIN_K, apply_stage2=main.APPLY_STAGE2,
                   F_C3H8_override=p["F_C3H8_fresh_kmol_h"])
    feas = bool(res.is_feasible)
    tac_hi = float(res.economics_hi.TAC) if (feas and res.economics_hi) else float("nan")
    return feas, tac_hi, float(res.effective_TAC), (res.failure_reason or "")

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["T_in","L_bed","feasible","TAC_hi","eff_TAC","reason"])
total = len(TIN_GRID)*len(LBED_GRID); k = 0; t0 = time.time()
log(f"grid {len(TIN_GRID)}x{len(LBED_GRID)}={total} pts; base=#201 (T_in x L_bed)")
for tin in TIN_GRID:
    for lbed in LBED_GRID:
        k += 1; ts = time.time()
        try:
            feas, tac_hi, eff, reason = eval_point(tin, lbed)
        except Exception as e:
            feas, tac_hi, eff, reason = False, float("nan"), float("nan"), f"EXC:{type(e).__name__}"
        with open(OUT, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([tin, lbed, feas, f"{tac_hi:.2f}", f"{eff:.2f}", reason])
        eta = (time.time()-t0)/k*(total-k)/60
        log(f"{k}/{total} T_in={tin} L_bed={lbed} feas={feas} TAC_hi={tac_hi:.1f} "
            f"({time.time()-ts:.1f}s, ETA {eta:.0f}min)")
log(f"DONE in {(time.time()-t0)/60:.1f}min -> {OUT}")
