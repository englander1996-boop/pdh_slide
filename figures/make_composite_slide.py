# -*- coding: utf-8 -*-
"""
make_composite_slide.py — スライド用 バランス複合線図（ベクトルPDF出力）。

与熱・受熱複合線（実温度, ΔTmin=10K）に全ユーティリティを挿入した
「バランス複合線」を 1 枚で描く（GCC パネルは廃止）:
  加熱側: LP スチームをリボイラ受熱フラットの +10℃ に水平挿入（ΔTmin を破らない
          最大量に自動キャップ）。残りの LP は 160℃、MP/HP は各水準、燃料（炉）は
          最高受熱温度 +10℃ に挿入。与熱線はユーティリティ線の右端から再開する。
  冷却側: エチレン冷媒をコンデンサ与熱フラットの −10℃ に挿入し、受熱線は
          その右端（x = Q_C）から再開する。
  → 両複合線の横幅（総エンタルピー）が一致し、外部加熱・冷却の入る温度水準が
    そのまま読める（低クオリティ熱を優先しエクセルギー損失を抑える表現）。

データ: Z:\\report_for_processdesign\\graph\\gcc_bestpoint.json
実行  : Z:\\pdh_simulator\\.venv\\Scripts\\python.exe make_composite_slide.py
出力  : composite_slide.pdf（ベクトル）
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _c in ["Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP"]:
    try:
        font_manager.findfont(_c, fallback_to_default=False)
        matplotlib.rcParams["font.family"] = _c
        break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["pdf.fonttype"] = 42

SRC = r"Z:\report_for_processdesign\graph\gcc_bestpoint.json"
HERE = os.path.dirname(os.path.abspath(__file__))
T0 = 273.15
RED = "#cc0000"; BLUE = "#1565c0"; BROWN = "#8a5a00"
ORF = "#e8821e"; TEAL = "#0e7c7b"

d = json.load(open(SRC, encoding="utf-8"))
QH = d["Q_H_min_kW"] / 1000.0
QC = d["Q_C_min_kW"] / 1000.0
H_hot = [p[0] / 1000.0 for p in d["composite_hot"]]
T_hot = [p[1] - T0 for p in d["composite_hot"]]
H_cold = [p[0] / 1000.0 + QC for p in d["composite_cold"]]
T_cold = [p[1] - T0 for p in d["composite_cold"]]
T_ph = d["T_pinch_hot_K"] - T0
T_pc = d["T_pinch_cold_K"] - T0
UB = {k: v / 1000.0 for k, v in d.get("utility_breakdown", {}).items()}  # MW
DT_MIN = 10.0


def _interp_x(H, T, t_query):
    """折れ線 (H,T) 上で温度 t_query の H を返す (最初に跨ぐ区間)。"""
    for i in range(len(T) - 1):
        t0, t1 = T[i], T[i + 1]
        if (t0 - t_query) * (t1 - t_query) <= 0 and t0 != t1:
            w = (t_query - t0) / (t1 - t0)
            return H[i] + w * (H[i + 1] - H[i])
    return None


def _longest_flat(H, T, tlo, thi):
    best = None
    for i in range(len(T) - 1):
        if abs(T[i + 1] - T[i]) < 1e-9 and tlo <= T[i] <= thi:
            if best is None or (H[i + 1] - H[i]) > (best[1] - best[0]):
                best = (H[i], H[i + 1], T[i])
    return best


def _t_at_x(H, T, x):
    """折れ線上の x における温度 (区間内線形, 垂直区間は高い方)。範囲外は None。"""
    if x < H[0] or x > H[-1]:
        return None
    t_best = None
    for i in range(len(H) - 1):
        if H[i] <= x <= H[i + 1]:
            if H[i + 1] - H[i] < 1e-12:
                t = max(T[i], T[i + 1])
            else:
                w = (x - H[i]) / (H[i + 1] - H[i])
                t = T[i] + w * (T[i + 1] - T[i])
            t_best = t if t_best is None else max(t_best, t)
    return t_best


_q_lp = UB.get("LP Steam", 0.0); _q_mp = UB.get("MP Steam", 0.0)
_q_hp = UB.get("HP Steam", 0.0); _q_fuel = UB.get("燃料燃焼", 0.0)
_q_eth = UB.get("エチレン冷媒-100C", 0.0)
_xh = max(H_hot); _xc = max(H_cold)

# ---- LP スチームの低温挿入量 (リボイラ +10℃)。ΔTmin を破らない最大シフトに自動キャップ ----
_flat = _longest_flat(H_cold, T_cold, 30.0, 60.0)        # リボイラ受熱フラット (~41℃)
x_fL, x_fR, T_flat = _flat
T_ins = T_flat + DT_MIN

def _max_shift_at(T_u):
    """温度 T_u より上の与熱線を右へずらせる最大量 (原カーブ基準, ΔTmin 維持)。"""
    s = float("inf")
    for hc, tc in zip(H_cold, T_cold):
        tn = tc + DT_MIN
        if tn <= T_u or tn > max(T_hot):
            continue
        xh = _interp_x(H_hot, T_hot, tn)
        if xh is not None:
            s = min(s, hc - xh)
    return max(s, 0.0)

_q_lp1 = round(min(_q_lp, _max_shift_at(T_ins)), 1)      # 51℃ に入れる LP
_q_lp2 = _q_lp - _q_lp1                                  # 160℃ に残す LP
T_FUEL = max(T_cold) + DT_MIN                            # 燃料 (炉): 最高受熱温度 +10℃

# (温度, 熱量, 色, ラベル) — 低温側から順に与熱線へ挿入
UTILS = [
    (T_ins,  _q_lp1, BROWN, f"LP スチーム {_q_lp1:.1f} MW"),
    (160.0,  _q_lp2, BROWN, f"LP {_q_lp2:.1f} MW"),
    (186.0,  _q_mp,  BROWN, f"MP {_q_mp:.1f} MW"),
    (230.0,  _q_hp,  BROWN, f"HP {_q_hp:.1f} MW"),
    (T_FUEL, _q_fuel, ORF,  f"燃料燃焼・炉 {_q_fuel:.1f} MW"),
]

# ---- バランス与熱線の構築: プロセス区間 (赤) とユーティリティ区間 (茶/橙) を交互に ----
proc_segs = []   # [(H_list, T_list)]
util_segs = []   # [(x0, x1, T, color, label)]
shift = 0.0
idx = 0
cur_H, cur_T = [], []
for T_u, Q_u, col, lab in UTILS:
    if Q_u <= 1e-9:
        continue
    if T_u <= max(T_hot):
        x_u = _interp_x(H_hot, T_hot, T_u)
        while idx < len(H_hot) and T_hot[idx] <= T_u:
            cur_H.append(H_hot[idx] + shift); cur_T.append(T_hot[idx]); idx += 1
        cur_H.append(x_u + shift); cur_T.append(T_u)
        proc_segs.append((cur_H, cur_T))
        util_segs.append((x_u + shift, x_u + shift + Q_u, T_u, col, lab))
        cur_H, cur_T = [x_u + shift + Q_u], [T_u]
        shift += Q_u
    else:
        # 与熱線最高温度より上 (燃料): 末尾に垂直接続 + 水平区間
        while idx < len(H_hot):
            cur_H.append(H_hot[idx] + shift); cur_T.append(T_hot[idx]); idx += 1
        proc_segs.append((cur_H, cur_T))
        x_end = _xh + shift
        util_segs.append((x_end, x_end + Q_u, T_u, col, lab))
        cur_H, cur_T = [], []
        shift += Q_u
if cur_H or idx < len(H_hot):
    while idx < len(H_hot):
        cur_H.append(H_hot[idx] + shift); cur_T.append(T_hot[idx]); idx += 1
    if cur_H:
        proc_segs.append((cur_H, cur_T))

x_hot_end = _xh + QH   # = _xc (バランスで右端一致)

# ---- ΔTmin の数値検証 (バランス与熱線 vs 受熱線) ----
bal_H, bal_T = [], []
for seg in proc_segs:
    bal_H += seg[0]; bal_T += seg[1]
for x0, x1, t, *_ in util_segs:
    bal_H += [x0, x1]; bal_T += [t, t]
order = sorted(range(len(bal_H)), key=lambda i: (bal_H[i], bal_T[i]))
bal_H = [bal_H[i] for i in order]; bal_T = [bal_T[i] for i in order]
# 注: x=Q_C はピンチ境界点 (与熱フラット終端と受熱線始点が同温で接する測度ゼロの点) の
#     ため検証から除外し、区間内部 (hc+0.5MW) で評価する。
_viol = 0.0; _varg = None
for hc, tc in zip(H_cold, T_cold):
    th = _t_at_x(bal_H, bal_T, hc + 0.5)
    if th is not None and (tc + DT_MIN) - th > _viol:
        _viol = (tc + DT_MIN) - th; _varg = (round(hc, 1), round(tc, 1), round(th, 1))
if _viol > 0.5:
    print(f"[warn] ΔTmin violation {_viol:.2f} K at {_varg}")
print(f"[balance] LP@{T_ins:.1f}C={_q_lp1:.1f} / LP@160C={_q_lp2:.1f} / 燃料@{T_FUEL:.0f}C={_q_fuel:.1f} MW"
      f"  右端 hot={x_hot_end:.1f} cold={_xc:.1f}  ΔTmin違反={max(_viol,0):.2f} K")

# ============ 描画 ============
YLIM = (-162, 760)
fig, ax = plt.subplots(figsize=(10.2, 7.07))

LW = 3.0   # 10K ギャップ (≈5pt) が見えるよう細めに
for seg_H, seg_T in proc_segs:
    ax.plot(seg_H, seg_T, color=RED, lw=LW, solid_capstyle="round")
for x0, x1, t, col, lab in util_segs:
    ax.plot([x0, x1], [t, t], color=col, lw=LW + 1.0, solid_capstyle="butt")
# 燃料区間への垂直接続 (零熱量) は点線で
_fuel = [u for u in util_segs if u[2] > max(T_hot)]
if _fuel:
    x0 = _fuel[0][0]
    ax.plot([x0, x0], [max(T_hot), _fuel[0][2]], color=ORF, ls=":", lw=1.6)

# 冷却側: エチレン冷媒 (コンデンサ −10℃, 0..Q_C) → 受熱線は x=Q_C から再開
T_cool = T_pc - DT_MIN
ax.plot([0.0, QC], [T_cool, T_cool], color=TEAL, lw=LW + 1.0, solid_capstyle="butt")
ax.plot(H_cold, T_cold, color=BLUE, lw=LW, solid_capstyle="round")
ax.plot([QC, QC], [T_cool, T_cold[0]], color=TEAL, ls=":", lw=2.0, zorder=6)

# ---- ユーティリティ ラベル ----
_lp1 = util_segs[0]
ax.text((_lp1[0] + _lp1[1]) / 2, T_ins + 14, _lp1[4],
        ha="center", va="bottom", fontsize=13.5, color=BROWN, fontweight="bold")
ax.text((_lp1[0] + _lp1[1]) / 2, T_ins + 52, "（リボイラの +10 ℃ で供給）",
        ha="center", va="bottom", fontsize=10.5, color=BROWN)
# LP残り/MP/HP (160/186/230℃): それぞれ個別の引出し線で示す
_mid = sorted([u for u in util_segs if 150 < u[2] < 250], key=lambda u: u[2])
_offsets = [(-62, 45), (-97, 76), (-42, 90)]   # (dx, dy): LP/MP/HP のラベル位置
for (u, (dx, dy)) in zip(_mid, _offsets):
    _xm = (u[0] + u[1]) / 2
    ax.annotate(u[4], xy=(_xm, u[2] + 3), xytext=(_xm + dx, u[2] + dy),
                fontsize=11.5, color=BROWN, fontweight="bold",
                ha="center", va="bottom",
                arrowprops=dict(arrowstyle="->", color=BROWN, lw=1.3))
if _fuel:
    ax.text((_fuel[0][0] + _fuel[0][1]) / 2, _fuel[0][2] + 14, _fuel[0][4],
            ha="center", va="bottom", fontsize=12.5, color=ORF, fontweight="bold")
ax.text(QC * 0.5, T_cool - 14, f"エチレン冷媒 {_q_eth:.1f} MW",
        ha="center", va="top", fontsize=13.5, color=TEAL, fontweight="bold")
ax.text(QC * 0.5, T_cool - 52, "（コンデンサの −10 ℃ で受熱）",
        ha="center", va="top", fontsize=10.5, color=TEAL)

# ---- 線ラベル ----
_x_hot_520 = None
for seg_H, seg_T in proc_segs:
    _x_hot_520 = _x_hot_520 or _interp_x(seg_H, seg_T, 520.0)
ax.text((_x_hot_520 or 250) - 28, 520, "与熱複合線", color=RED, fontsize=23,
        fontweight="bold", ha="right", va="center")
_x_cold_80 = _interp_x(H_cold, T_cold, 80.0) or 250.0
ax.text(_x_cold_80 + 30, 66, "受熱複合線", color=BLUE, fontsize=23,
        fontweight="bold", ha="left", va="center")

# ---- コンデンサ・リボイラ・ピンチ注記 ----
ax.annotate(f"コンデンサ {T_pc:.0f} ℃", xy=(QC * 0.45, T_pc + 6), xytext=(2, 148),
            fontsize=16, color="black", ha="left", va="center",
            arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
_x_reb = _interp_x(H_cold, T_cold, 41.5) or (QC + 80)
ax.annotate("リボイラ", xy=(_x_reb + 25, 38), xytext=(_x_reb + 105, 15),
            fontsize=16, color="black", ha="center", va="center",
            arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
# 本体では 10K ギャップが潰れて見えないため、ピンチ部の拡大インセットで示す
ax.annotate("最小接近温度差 10 ℃（ピンチ）", xy=(QC - 6, (T_pc + T_cool) / 2),
            xytext=(QC + 55, -40), fontsize=15, color="black",
            ha="left", va="center",
            arrowprops=dict(arrowstyle="->", color="black", lw=1.4))

# ---- ピンチ部 拡大インセット (左上の空白域) ----
axins = ax.inset_axes([0.055, 0.585, 0.235, 0.30])
for seg_H, seg_T in proc_segs:
    axins.plot(seg_H, seg_T, color=RED, lw=3.2, solid_capstyle="round")
axins.plot(H_cold, T_cold, color=BLUE, lw=3.2, solid_capstyle="round")
axins.plot([0.0, QC], [T_cool, T_cool], color=TEAL, lw=4.0, solid_capstyle="butt")
axins.plot([QC, QC], [T_cool, T_cold[0]], color=TEAL, ls=":", lw=2.2, zorder=6)
# 10K ギャップが見える対 = コンデンサ与熱フラット (−82.4℃) と冷媒線 (−92.4℃) の間
axins.annotate("", xy=(QC - 8, T_pc), xytext=(QC - 8, T_cool),
               arrowprops=dict(arrowstyle="<->", color="black", lw=1.8))
axins.text(QC - 6.2, (T_pc + T_cool) / 2, "10 ℃", fontsize=13.5,
           color="black", va="center", fontweight="bold")
axins.set_xlim(QC - 16, QC + 18); axins.set_ylim(-104, -56)
axins.tick_params(labelsize=9, direction="in", top=True, right=True)
axins.set_title("ピンチ部 拡大", fontsize=11.5, pad=2)
ax.indicate_inset_zoom(axins, edgecolor="0.45", lw=1.2)

ax.set_xlabel("累積エンタルピー  $H$ [MW]", fontsize=18)
ax.set_ylabel("温度  $T$ [℃]", fontsize=18, labelpad=1)
ax.set_xlim(-12, _xc * 1.05); ax.set_ylim(*YLIM)
ax.set_yticks(list(range(-100, 761, 100)))
ax.tick_params(labelsize=14.5, direction="in", top=True, right=True)

fig.savefig(os.path.join(HERE, "composite_slide.pdf"), bbox_inches="tight", pad_inches=0.0)
fig.savefig(os.path.join(HERE, "_composite_check.png"), bbox_inches="tight",
            pad_inches=0.0, dpi=110)
plt.close(fig)
print(f"[out] composite_slide.pdf  Q_H={QH:.1f} / Q_C={QC:.1f} MW  右端一致={abs(x_hot_end-_xc)<0.5}")
