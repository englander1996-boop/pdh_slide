# -*- coding: utf-8 -*-
r"""run_interaction_units.py — スライド15用、収束に鈍感(=可行域が広く滑らか)な
サイジング変数のペアを、いろんなユニットで全フローシート HYSYS 評価する(trial #201 背景)。

  u_psa  PSA      塔径 D_psa × 層高 L_psa      (等吸着体積でトレードオフ)
  u_c3   C3スプリッタ 段数 col3_n × 圧力 col3_p
  u_c1   脱ブタン塔   段数 col1_n × 圧力 col1_p

出力: u_psa.csv / u_c3.csv / u_c1.csv (列 x,y,feasible,TAC_hi,eff_TAC,reason)
"""
import sys, os, time, csv
SIM = r"Z:\pdh_simulator"
if SIM not in sys.path:
    sys.path.insert(0, SIM)
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import main
from flowsheet import evaluate

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(r"Z:\pdh_simulator\outputs\main_20260605_170938\trials.csv")
row = df[df["number"] == 201].iloc[0]
KEYS = ["T_in_K","t_cyc_min","D_reactor_m","L_bed_m","N_online","d_p_mm",
        "D_psa_col_m","L_psa_bed_m","desorption_target","P_H_Pa","A_mem_m2",
        "F_C3H8_fresh_kmol_h","col1_p_kpa","col1_n_stages","col1_feed_stage",
        "col1_comp_frac_2","col2_p_kpa","col2_n_stages","col2_feed_ratio",
        "col2_reflux_ratio","col3_p_kpa","col3_n_stages","col3_feed_ratio"]
INTS = {"N_online","col1_n_stages","col1_feed_stage","col2_n_stages","col3_n_stages"}
BASE = {k: (int(round(row[k])) if k in INTS else float(row[k])) for k in KEYS}

def lin(a, b, n): return [round(a + (b-a)/(n-1)*i, 4) for i in range(n)]
def ints(a, b, n): return sorted(set(int(round(v)) for v in np.linspace(a, b, n)))
INTKEYS = {"col1_n_stages","col3_n_stages"}

PAIRS = [
    # 工程横断候補: 反応器 浅床厚 × C3塔 段数 (収束に効くが L_bed を 1.8 で頭打ちにし遅い点回避)
    ("ucross.csv", "L_bed_m", lin(0.9,1.8,7), "col3_n_stages", ints(115,160,7)),
]

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def eval_point(xk, xv, yk, yv):
    p = dict(BASE)
    p[xk] = int(round(xv)) if xk in INTKEYS else float(xv)
    p[yk] = int(round(yv)) if yk in INTKEYS else float(yv)
    design = main._build_design(p)
    res = evaluate(design, main._CONFIG, verbose=False, apply_hi=main.APPLY_HI,
                   hi_dT_min_K=main.HI_DT_MIN_K, apply_stage2=main.APPLY_STAGE2,
                   F_C3H8_override=p["F_C3H8_fresh_kmol_h"])
    feas = bool(res.is_feasible)
    tac = float(res.economics_hi.TAC) if (feas and res.economics_hi) else float("nan")
    return feas, tac, float(res.effective_TAC), (res.failure_reason or "")

t_all = time.time()
for out, xk, xg, yk, yg in PAIRS:
    with open(os.path.join(HERE, out), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["x", "y", "feasible", "TAC_hi", "eff_TAC", "reason"])
    total = len(xg)*len(yg); k = 0; t0 = time.time()
    log(f"=== {out}: {xk} x {yk} {len(xg)}x{len(yg)}={total} ===")
    for xv in xg:
        for yv in yg:
            k += 1; ts = time.time()
            try:
                feas, tac, eff, reason = eval_point(xk, xv, yk, yv)
            except Exception as e:
                feas, tac, eff, reason = False, float("nan"), float("nan"), f"EXC:{type(e).__name__}"
            with open(os.path.join(HERE, out), "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([xv, yv, feas, f"{tac:.2f}", f"{eff:.2f}", reason])
            log(f"  {k}/{total} feas={feas} TAC={tac:.1f} ({time.time()-ts:.0f}s)")
    nf = pd.read_csv(os.path.join(HERE, out))
    log(f"=== {out} DONE {(time.time()-t0)/60:.1f}min feasible={int(nf['feasible'].sum())}/{total} ===")
log(f"ALL DONE {(time.time()-t_all)/60:.1f}min")
