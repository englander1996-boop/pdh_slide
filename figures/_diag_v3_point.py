# -*- coding: utf-8 -*-
"""_diag_v3_point.py — v3 グリッドで infeasible になった点の単発再評価診断。

使い方: python _diag_v3_point.py <T_in> <L_bed> [cold|warm]
  cold (既定): PDH_HYSYS_FORCE_COLD=1 + 固定初期 tear (exp3 と同条件)
  warm       : v3 グリッドと同じ FORCE_COLD=0

目的: グリッド run の失敗が「設計が本当に infeasible」なのか
「warm 再解セッション汚染 / tear 連鎖の副作用」なのかを切り分ける。
"""
import os, sys, time

SIM = r"Z:\pdh_simulator"
if SIM not in sys.path:
    sys.path.insert(0, SIM)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

T_in = float(sys.argv[1]) if len(sys.argv) > 1 else 935.0
L_bed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5333
mode = sys.argv[3] if len(sys.argv) > 3 else 'cold'

os.environ['PDH_TRIAL_TIME_BUDGET_SEC'] = '900'
os.environ['PDH_HYSYS_FORCE_COLD'] = '1' if mode == 'cold' else '0'

import dataclasses as dc
from run_interaction_grid_v3 import build_design
from config.load import load_operating_config
from flowsheet import evaluate, TearState

config = load_operating_config()
config = dc.replace(config, spec=dc.replace(config.spec, c3h6_min_wtfrac=0.9945))
tear_init = TearState(
    tear_dist3={'A': 23.31, 'B': 775.51},
    tear_mem  ={'A': 2132.07, 'B': 1294.67},
    T_d3=273.15 + 41.0, T_mem=273.15 + 54.0,
)

print(f"=== diag point T_in={T_in} L_bed={L_bed} mode={mode} ===", flush=True)
t0 = time.time()
design = build_design({'T_in_K': T_in, 'L_bed_m': L_bed})
res = evaluate(design, config, verbose=False,
               apply_hi=True, hi_dT_min_K=10.0, apply_stage2=False,
               F_C3H8_override=1494.576, F_C3H8_feedback=True,
               tear_init=tear_init)
dt = time.time() - t0
print(f"feasible      = {res.is_feasible}")
print(f"effective_TAC = {res.effective_TAC:.2f}")
if res.economics_hi is not None:
    print(f"TAC_hi        = {res.economics_hi.TAC:.2f}")
print(f"failure_reason= {res.failure_reason}")
print(f"failure_unit  = {getattr(res, 'failure_unit', None)}")
sv = res.solver
if sv is not None:
    print(f"fresh_C3H8    = {sv.fresh_C3H8:.3f}")
    st = sv.inner_status
    print(f"inner: converged={st.converged} iters={getattr(st, 'iterations', '?')} "
          f"penalty_hit={st.penalty_hit} guard_hit={st.guard_hit}")
    op = sv.one_pass or {}
    if op.get('first_failed_unit'):
        print(f"first_failed_unit = {op['first_failed_unit']}")
print(f"[{dt:.0f}s]")

try:
    from units.vle.hysys.provider import shutdown_default_provider
    shutdown_default_provider()
except Exception:
    pass
