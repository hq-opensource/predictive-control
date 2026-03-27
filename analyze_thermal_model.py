"""
Thermal Model Analysis & Simulation
====================================
Loads the learned thermal model, simulates temperature evolution over 2-3 hours
with all heaters at maximum capacity (1.6 kW), and computes per-zone sensitivity.
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# 1. Configuration
# ──────────────────────────────────────────────────────────────────────────────
MODEL_PATH = Path(__file__).parent / "data" / "thermal_models" / "latest"
OUTPUT_PLOT = Path(__file__).parent / "thermal_model_simulation.png"

ZONE_NAMES = [
    "chambre_2",    # 0 — priority 2
    "cuisine",      # 1 — priority 5
    "salle_manger", # 2 — priority 6
    "salon",        # 3 — priority 7
    "chambre_3",    # 4 — priority 8
    "salle_bain",   # 5 — priority 9
    "salle_eau",    # 6 — priority 9 (PADDED — no sensor data)
    "sous_sol_1",   # 7 — priority 10
    "sous_sol_2",   # 8 — priority 11
    "garage",       # 9 — priority 12
]

TIMESTEP_MIN = 10          # minutes per step
SIM_HOURS    = 3.0         # simulation horizon
T0           = 17.0        # initial temperature all zones (°C)
T_OUT        = -5.0        # outdoor temperature (°C, typical March Quebec night)
U_MAX        = 1.6         # max heater power per zone (kW)

# ──────────────────────────────────────────────────────────────────────────────
# 2. Load model
# ──────────────────────────────────────────────────────────────────────────────
with open(MODEL_PATH) as f:
    model = json.load(f)

Ax = np.array(model["x_internal_states"])   # (n, n)
Au = np.array(model["u_heaters"])           # (n, n) diagonal
Aw = np.array(model["w_external_variables"]) # (n, 1)

n = len(ZONE_NAMES)
Au_diag = np.diag(Au)        # diagonal entries only
Ax_diag = np.diag(Ax)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Simulation: all heaters at max for full horizon
# ──────────────────────────────────────────────────────────────────────────────
K = int(SIM_HOURS * 60 / TIMESTEP_MIN)   # number of steps
times_min = np.arange(0, (K + 1) * TIMESTEP_MIN, TIMESTEP_MIN)

x = np.full(n, T0)        # initial state
u = np.full(n, U_MAX)     # heaters at max
w = np.array([[T_OUT]])   # outdoor temp

trajectory = np.zeros((K + 1, n))
trajectory[0] = x

for k in range(K):
    x = Ax @ x + Au @ u + (Aw @ w).flatten()
    trajectory[k + 1] = x

# ──────────────────────────────────────────────────────────────────────────────
# 4. Simulation: natural cooling (heaters OFF)
# ──────────────────────────────────────────────────────────────────────────────
x_off = np.full(n, T0)
u_off = np.zeros(n)

cooling = np.zeros((K + 1, n))
cooling[0] = x_off
for k in range(K):
    x_off = Ax @ x_off + Au @ u_off + (Aw @ w).flatten()
    cooling[k + 1] = x_off

# ──────────────────────────────────────────────────────────────────────────────
# 5. Steady-state analysis at max heating
# ──────────────────────────────────────────────────────────────────────────────
# X_ss = (I - Ax)^-1 * (Au*U + Aw*W)
IminAx = np.eye(n) - Ax
X_ss = np.linalg.solve(IminAx, Au @ u + (Aw @ w).flatten())

# ──────────────────────────────────────────────────────────────────────────────
# 6. Sensitivity table (steady-state kW per °C — using only diagonal of Ax, Au)
#    dT_ss/du = Au_ii / (1 - Ax_ii)  → kW per °C = (1 - Ax_ii) / Au_ii
# ──────────────────────────────────────────────────────────────────────────────
kw_per_degC_ss = (1 - Ax_diag) / Au_diag
degC_per_kw_ss = Au_diag / (1 - Ax_diag)

# Instantaneous sensitivity: after 1 step, ΔT from ΔU (only Au term matters)
degC_per_kw_inst = Au_diag  # °C rise per kW in first 10-min step

# Temperature rise after 10 min at U_MAX
dT_10min = Au_diag * U_MAX

# Temperature rise after 30 min at U_MAX (3 steps, simplified as Ax_diag^2 * Au * U
# + Ax_diag * Au * U + Au * U)
sum_ax = (1 - Ax_diag**3) / (1 - Ax_diag + 1e-12)   # geometric sum
dT_30min = Au_diag * U_MAX * sum_ax

# ──────────────────────────────────────────────────────────────────────────────
# 7. Print tables
# ──────────────────────────────────────────────────────────────────────────────
PADDED = {"salle_eau"}
AU_FLOOR = 0.0015

header = (
    f"\n{'Zone':<14} {'Ax (diag)':>10} {'Au (diag)':>10} {'Aw':>8} "
    f"{'kW/°C (SS)':>11} {'°C/kW (SS)':>11} "
    f"{'ΔT @1.6kW':>10} {'T_ss @1.6kW':>12}  Note"
)
sep = "-" * len(header)
print(sep)
print("LEARNED THERMAL MODEL — ZONE PARAMETERS")
print(sep)
print(header)
print(sep)

for i, zone in enumerate(ZONE_NAMES):
    ax_i  = Ax_diag[i]
    au_i  = Au_diag[i]
    aw_i  = float(Aw[i, 0])
    kw_pc = kw_per_degC_ss[i]
    dc_kw = degC_per_kw_ss[i]
    dt10  = dT_10min[i]
    tss   = X_ss[i]

    note = ""
    if zone in PADDED:
        note = "PADDED (no sensor)"
    elif abs(au_i - AU_FLOOR) < 1e-4:
        note = "⚠ Au at floor (broken sensor)"

    print(f"{zone:<14} {ax_i:>10.4f} {au_i:>10.4f} {aw_i:>8.4f} "
          f"{kw_pc:>11.2f} {dc_kw:>11.4f} "
          f"{dt10:>10.3f}°C {tss:>11.1f}°C  {note}")

print(sep)
print(f"\nNotes:")
print(f"  - Ax (diag)  : heat retained per 10-min step (1.0 = no loss)")
print(f"  - Au (diag)  : °C rise per kW per 10-min step (instantaneous heating gain)")
print(f"  - kW/°C (SS) : kW needed to maintain +1°C above equilibrium (steady-state)")
print(f"  - °C/kW (SS) : °C gain per kW of constant heating at steady state")
print(f"  - ΔT @1.6kW  : temperature rise in first 10 min at 1.6 kW (from Au)")
print(f"  - T_ss @1.6kW: predicted steady-state temp at 1.6 kW, T_out={T_OUT}°C")
print(f"\n  ⚠  Au floor = 0.0015 → sensor broken, model cannot learn real heating gain")
print(f"     These zones will appear nearly unresponsive to heating in the MPC.\n")

# Zone grouping for discussion
print(sep)
print("SENSITIVITY SUMMARY")
print(sep)
print(f"{'Zone':<14}  {'ΔT in 10min':>12}  {'ΔT in 30min':>12}  {'Full 3h range':>20}")
print(sep)
for i, zone in enumerate(ZONE_NAMES):
    dt_10 = dT_10min[i]
    dt_30 = dT_30min[i]
    t_min = trajectory[:, i].min()
    t_max = trajectory[:, i].max()
    print(f"{zone:<14}  {dt_10:>11.3f}°C  {dT_30min[i]:>11.3f}°C  {t_min:.1f} → {t_max:.1f}°C")
print(sep)

# ──────────────────────────────────────────────────────────────────────────────
# 8. Plot
# ──────────────────────────────────────────────────────────────────────────────
colors = plt.cm.tab10(np.linspace(0, 1, n))

fig = plt.figure(figsize=(16, 14))
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

# ── 8a. Temperature with heaters at max ──────────────────────────────────────
ax1 = fig.add_subplot(gs[0, :])
for i, zone in enumerate(ZONE_NAMES):
    lw = 1.5 if zone not in PADDED else 1.0
    ls = "--" if zone in PADDED else "-"
    alpha = 0.5 if "⚠" in (
        "⚠" if abs(Au_diag[i] - AU_FLOOR) < 1e-4 else ""
    ) else 0.9
    label = f"{zone} [Au={Au_diag[i]:.4f}]"
    ax1.plot(times_min, trajectory[:, i], color=colors[i], lw=lw, ls=ls,
             label=label, alpha=0.85)

ax1.axhline(20, color="gray", ls=":", lw=1, label="20°C comfort")
ax1.axhline(T0, color="black", ls="--", lw=0.8, alpha=0.4)
ax1.set_xlabel("Time (minutes)")
ax1.set_ylabel("Temperature (°C)")
ax1.set_title(
    f"Simulation: ALL heaters at max ({U_MAX} kW each) — T₀={T0}°C, T_out={T_OUT}°C\n"
    f"Zones with Au at floor (≤0.0015) barely respond — sensor issue"
)
ax1.legend(fontsize=7, ncol=2, loc="upper left")
ax1.set_xlim(0, times_min[-1])
ax1.grid(True, alpha=0.3)

# ── 8b. Natural cooling (heaters OFF) ────────────────────────────────────────
ax2 = fig.add_subplot(gs[1, 0])
for i, zone in enumerate(ZONE_NAMES):
    ls = "--" if zone in PADDED else "-"
    ax2.plot(times_min, cooling[:, i], color=colors[i], lw=1.5, ls=ls,
             label=zone, alpha=0.85)
ax2.axhline(T_OUT, color="red", ls=":", lw=1, label=f"T_out={T_OUT}°C")
ax2.set_xlabel("Time (minutes)")
ax2.set_ylabel("Temperature (°C)")
ax2.set_title(f"Natural cooling — heaters OFF, T₀={T0}°C, T_out={T_OUT}°C")
ax2.legend(fontsize=7, ncol=1, loc="upper right")
ax2.set_xlim(0, times_min[-1])
ax2.grid(True, alpha=0.3)

# ── 8c. Au diagonal bar chart ─────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 1])
bar_colors = [colors[i] for i in range(n)]
bars = ax3.bar(ZONE_NAMES, Au_diag, color=bar_colors)
ax3.axhline(AU_FLOOR, color="red", ls="--", lw=1.5, label=f"Floor = {AU_FLOOR}")
ax3.set_xticks(range(n))
ax3.set_xticklabels(ZONE_NAMES, rotation=40, ha="right", fontsize=8)
ax3.set_ylabel("Au diagonal (°C / kW / step)")
ax3.set_title("Heating gain coefficient (Au diagonal)\nHigher = more responsive to heater")
ax3.legend(fontsize=9)
ax3.grid(True, axis="y", alpha=0.3)

# Annotate bars
for bar, val in zip(bars, Au_diag):
    ax3.text(bar.get_x() + bar.get_width() / 2, val + 0.002,
             f"{val:.4f}", ha="center", va="bottom", fontsize=7, rotation=90)

# ── 8d. kW per °C bar chart (only good zones) ─────────────────────────────────
ax4 = fig.add_subplot(gs[2, 0])
kw_clipped = np.clip(kw_per_degC_ss, 0, 20)   # clip extreme values for readability
bar_colors2 = [colors[i] for i in range(n)]
bars2 = ax4.bar(ZONE_NAMES, kw_clipped, color=bar_colors2)
ax4.set_xticks(range(n))
ax4.set_xticklabels(ZONE_NAMES, rotation=40, ha="right", fontsize=8)
ax4.set_ylabel("kW needed to maintain +1°C (SS)\n[clipped at 20 for display]")
ax4.set_title("Steady-state: kW per °C above equilibrium\nZones clipped at 20 kW/°C have broken sensors")
ax4.grid(True, axis="y", alpha=0.3)
for bar, raw, clip in zip(bars2, kw_per_degC_ss, kw_clipped):
    label = f"{raw:.1f}" if raw < 20 else f">{20}"
    ax4.text(bar.get_x() + bar.get_width() / 2, clip + 0.2,
             label, ha="center", va="bottom", fontsize=7, rotation=90)

# ── 8e. Ax diagonal (heat retention) ──────────────────────────────────────────
ax5 = fig.add_subplot(gs[2, 1])
ax5.bar(ZONE_NAMES, Ax_diag, color=bar_colors)
ax5.set_xticks(range(n))
ax5.set_xticklabels(ZONE_NAMES, rotation=40, ha="right", fontsize=8)
ax5.set_ylabel("Ax diagonal (fraction retained / step)")
ax5.set_title("Heat retention per 10-min step (Ax diagonal)\nHigher = slower temperature change")
ax5.set_ylim(0.5, 1.05)
ax5.axhline(0.98, color="orange", ls="--", lw=1, label="Default (0.98)")
ax5.legend(fontsize=9)
ax5.grid(True, axis="y", alpha=0.3)
for i, (val, zone) in enumerate(zip(Ax_diag, ZONE_NAMES)):
    ax5.text(i, val + 0.002, f"{val:.3f}", ha="center", va="bottom", fontsize=7)

fig.suptitle(
    "Learned Thermal Model Analysis\n"
    f"(1384 data points, 10-day window, T_step=10min, T_out={T_OUT}°C)",
    fontsize=13, fontweight="bold", y=0.98
)

plt.savefig(OUTPUT_PLOT, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to: {OUTPUT_PLOT}")
