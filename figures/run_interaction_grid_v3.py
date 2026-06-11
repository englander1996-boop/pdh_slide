# -*- coding: utf-8 -*-
r"""run_interaction_grid_v3.py — スライド15 相互作用マップの新構成版グリッド評価。

新最適点 (exp3_202606101630) の方法論で全点を評価する:
  - Dist3 = HYSYS spec 固定 (Draw 1200 kmol/h + Comp Fraction 0.9952)
  - F_fresh は fresh-feedback で物質収支から決定 (生産量 spec は構成的に充足)
  - 背景 = 最良設計点の 22 変数、ペア変数のみ振る

旧 run_interaction_units.py との違い: 旧版は Dist3=SM(clamp 欠陥) + F_fresh 固定。

パネル (出力 CSV は make_interaction_panels.py がそのまま読める形式):
  fig_grid_p1.csv : T_in × L_bed       (7×7)
  m_a.csv         : A_mem × col3_n     (6×5)
  u_c3.csv        : col3_n × col3_p    (5×5)
  ucross.csv      : L_bed × col3_n     (5×5)

実行:
  python run_interaction_grid_v3.py            # 全パネル (行単位サブプロセス, resume 可)
  python run_interaction_grid_v3.py <csv> <y値>  # 単一行をこのプロセスで評価
"""
import os, sys, csv, time, subprocess

SIM = r"Z:\pdh_simulator"
if SIM not in sys.path:
    sys.path.insert(0, SIM)
HERE = os.path.dirname(os.path.abspath(__file__))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import numpy as np


def lin(a, b, n):
    return [round(a + (b - a) / (n - 1) * i, 4) for i in range(n)]


def ints(a, b, n):
    return sorted(set(int(round(v)) for v in np.linspace(a, b, n)))


# パネル定義: (csv, xkey, x格子, ykey, y格子, ヘッダ(x,y))
PANELS = [
    ("fig_grid_p1.csv", "T_in_K",        lin(930, 940, 7),       "L_bed_m",       lin(0.7, 1.95, 7),  ("T_in", "L_bed")),
    ("m_a.csv",         "A_mem_m2",      lin(8e4, 2.2e5, 6),     "col3_n_stages", ints(115, 160, 5),  ("x", "y")),
    ("u_c3.csv",        "col3_n_stages", ints(115, 160, 5),      "col3_p_kpa",    lin(1600, 1900, 5), ("x", "y")),
    ("ucross.csv",      "L_bed_m",       lin(0.9, 1.8, 5),       "col3_n_stages", ints(115, 160, 5),  ("x", "y")),
]
INTKEYS = {"col3_n_stages"}


def _fs(ratio, n, lo, hi):
    fs = int(round(ratio * n)); hi_eff = min(hi, n - 2); lo_eff = min(lo, hi_eff)
    return max(lo_eff, min(fs, hi_eff))


def build_design(over):
    """最良設計点をベースに、over = {key: value} を上書きした FlowsheetDesignVars。"""
    from flowsheet import FlowsheetDesignVars
    from src.distillation_core import ColumnTunables
    from units.reactors.catofin import CatofinDesignVars
    from units.separators.psa.psa_system import PSADesignVars
    from units.separators.membrane.membrane_system import MemDesignVars

    p = dict(
        T_in_K=935.1547623411832, t_cyc_min=14.004729913207157,
        D_reactor_m=10.762975573082075, L_bed_m=1.5774708671200912,
        N_online=7, d_p_mm=5.8428613525854365,
        D_psa_col_m=4.488136113874189, L_psa_bed_m=24.752751824975242,
        desorption_target=0.2537096066008174,
        P_H_Pa=843657.6171376609, A_mem_m2=127838.27553657915,
        col1_p_kpa=1952.1341890282515, col1_n_stages=36, col1_feed_stage=28,
        col1_comp_frac_2=0.9952068630724175,
        col2_p_kpa=788.1112783915734, col2_n_stages=61,
        col2_feed_ratio=0.5069007093513171, col2_reflux_ratio=11.800664770401722,
        col3_p_kpa=1674.9231485407379, col3_n_stages=117,
        col3_feed_ratio=0.8194105169730515,
    )
    p.update(over)
    n3 = int(p["col3_n_stages"])
    return FlowsheetDesignVars(
        swing=CatofinDesignVars(T_in=p["T_in_K"], t_cyc=p["t_cyc_min"],
                                D=p["D_reactor_m"], L_bed=p["L_bed_m"],
                                N_online=int(p["N_online"]), d_p=p["d_p_mm"] / 1000.0),
        psa=PSADesignVars(D_col=p["D_psa_col_m"], L_bed=p["L_psa_bed_m"],
                          desorption_target=p["desorption_target"]),
        mem=MemDesignVars(P_H=p["P_H_Pa"], P_L=1.0e5, A_mem=p["A_mem_m2"],
                          P_dist=p["col3_p_kpa"] * 1000.0),
        dist1=ColumnTunables(P_col=p["col1_p_kpa"] * 1000.0, N_stages=int(p["col1_n_stages"]),
                             N_feed=1, reflux_ratio=2.0, solver_method='sm',
                             hysys_spec_value=p["col1_comp_frac_2"],
                             hysys_feed_stage=int(p["col1_feed_stage"])),
        dist2=ColumnTunables(P_col=p["col2_p_kpa"] * 1000.0, N_stages=int(p["col2_n_stages"]),
                             N_feed=1, reflux_ratio=p["col2_reflux_ratio"], solver_method='hysys',
                             hysys_spec_value=p["col2_reflux_ratio"],
                             hysys_feed_stage=_fs(p["col2_feed_ratio"], int(p["col2_n_stages"]), 2, 9999)),
        dist3=ColumnTunables(P_col=p["col3_p_kpa"] * 1000.0, N_stages=n3, N_feed=1,
                             reflux_ratio=12.0, solver_method='hysys',
                             hysys_spec_value=1200.0, hysys_spec_value2=0.9952,
                             hysys_feed_stage=_fs(p["col3_feed_ratio"], n3, 70, 180)),
    )


def run_row(csv_name, y_val):
    """単一行 (y 固定, 全 x) をこのプロセスで評価して CSV に追記。"""
    os.environ['PDH_TRIAL_TIME_BUDGET_SEC'] = '600'   # 1 点 10 分で打ち切り
    # cold 必須 (2026-06-11 確定): FORCE_COLD=0 の warm 再解では、1 点失敗すると同一
    # セッションの後続点が 1s で連鎖即死する (偽 infeasible 8割)。cold で再評価した
    # (935.0, 1.5333) は feasible TAC=1123.2 で近傍トレンドにも整合。warm-start 不採用は
    # リポジトリ方針 (units/vle/hysys/README.md)。tear/F の行内連鎖は Python ソルバの
    # 初期値であり HYSYS warm とは無関係なので維持する。
    os.environ['PDH_HYSYS_FORCE_COLD'] = '1'
    import dataclasses as dc
    from config.load import load_operating_config
    from flowsheet import evaluate, TearState

    panel = next(pn for pn in PANELS if pn[0] == csv_name)
    _, xkey, xs, ykey, ys, hdr = panel
    y = (int(round(float(y_val))) if ykey in INTKEYS else float(y_val))

    config = load_operating_config()
    config = dc.replace(config, spec=dc.replace(config.spec, c3h6_min_wtfrac=0.9945))
    tear_init = TearState(
        tear_dist3={'A': 23.31, 'B': 775.51},
        tear_mem  ={'A': 2132.07, 'B': 1294.67},
        T_d3=273.15 + 41.0, T_mem=273.15 + 54.0,
    )

    path = os.path.join(HERE, csv_name)
    done = set()
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            for r in csv.reader(f):
                if r and r[0] != hdr[0]:
                    try:
                        done.add((float(r[0]), float(r[1])))
                    except ValueError:
                        pass

    # 行内連鎖: 直前の点の収束 tear / F* を次の点の初期値に使う (近傍なので数十反復で収束)
    cur_init, cur_F = tear_init, 1494.576
    for xv in xs:
        x = (int(round(float(xv))) if xkey in INTKEYS else float(xv))
        if (float(x), float(y)) in done:
            print(f"  skip ({x},{y})", flush=True)
            continue
        t0 = time.time()
        try:
            design = build_design({xkey: x, ykey: y})
            res = evaluate(design, config, verbose=False,
                           apply_hi=True, hi_dT_min_K=10.0, apply_stage2=False,
                           F_C3H8_override=cur_F, F_C3H8_feedback=True,
                           tear_init=cur_init)
            feas = bool(res.is_feasible)
            tac_hi = (f"{res.economics_hi.TAC:.1f}"
                      if (feas and res.economics_hi is not None) else "")
            eff = f"{res.effective_TAC:.1f}"
            funit = getattr(res, 'failure_unit', '') or ''
            reason = "" if feas else f"[{funit}] {(res.failure_reason or '')}"[:120]
            # 収束していれば (feasible でなくても solver が回っていれば) 連鎖を更新
            try:
                sv = res.solver
                if sv is not None and sv.inner_status.converged and sv.one_pass is not None:
                    from flowsheet import TearState as _TS
                    cur_init = _TS(
                        tear_dist3=dict(sv.one_pass['tear_dist3_new']),
                        tear_mem=dict(sv.one_pass['tear_mem_new']),
                        T_d3=sv.one_pass['T_d3_new'], T_mem=sv.one_pass['T_mem_new'],
                    )
                    cur_F = float(sv.fresh_C3H8)
            except Exception:
                pass
        except Exception as e:
            feas, tac_hi, eff, reason = False, "", "5000.0", f"exception: {type(e).__name__}: {e}"[:120]
        with open(path, 'a', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            if os.path.getsize(path) == 0:
                w.writerow(list(hdr) + ["feasible", "TAC_hi", "eff_TAC", "reason"])
            w.writerow([x, y, feas, tac_hi, eff, reason])
        print(f"  ({x},{y}) feas={feas} TAC={tac_hi or eff} [{time.time()-t0:.0f}s]", flush=True)

    try:
        from units.vle.hysys.provider import shutdown_default_provider
        shutdown_default_provider()
    except Exception:
        pass


def main():
    for csv_name, xkey, xs, ykey, ys, hdr in PANELS:
        path = os.path.join(HERE, csv_name)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(list(hdr) + ["feasible", "TAC_hi", "eff_TAC", "reason"])
        for y in ys:
            print(f"\n=== {csv_name}  {ykey}={y}  ({time.strftime('%H:%M:%S')}) ===", flush=True)
            r = subprocess.run([sys.executable, '-u', os.path.abspath(__file__),
                                csv_name, str(y)], cwd=SIM)
            print(f"=== row exit={r.returncode} ===", flush=True)
    print("\n==== ALL PANELS DONE ====", flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        run_row(sys.argv[1], sys.argv[2])
    else:
        main()
