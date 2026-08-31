"""Génère toutes les figures de RATISS-BIOLAB — plans de conception + marque.

Produit des PNG dans docs/images/ :
1. Plan de conception de l'incubateur (coupe thermique, régulation)
2. Plan de conception du thermocycleur PCR (bloc alu + Peltier)
3. Les 3 appareils une fois montés (rendu)
4. Courbes thermiques (incubateur 37°C, cycles PCR)
5. Spectres d'absorption des protéines cibles (SIRT6, Prestin, CIRBP)
6. Erreur de mesure spectro (Monte Carlo, capteur low-cost)
7. Logo / marque RATIS Labs

Usage : PYTHONPATH=. python scripts/generate_figures.py
Les courbes proviennent des vrais simulateurs, pas de données inventées.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "images")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "font.size": 11,
                     "axes.grid": True, "grid.alpha": 0.3})

RATIS_DARK = "#0b1f3a"
RATIS_GREEN = "#1f9d55"
RATIS_GOLD = "#e0a800"
RATIS_RED = "#c0392b"
RATIS_BLUE = "#4aa3df"


def save(fig, name, facecolor="white"):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", facecolor=facecolor)
    plt.close(fig)
    print("généré :", name)


def _box(ax, x, y, w, h, text, fc, fs=9, tc="black"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                facecolor=fc, edgecolor=RATIS_DARK,
                                linewidth=1.6, zorder=2))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fs, zorder=3, fontweight="bold", color=tc)


# ============================================ 1. PLAN INCUBATEUR (thermique)
def fig_plan_incubateur():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.axis("off")
    ax.set_title("PLAN DE CONCEPTION — Incubateur cellulaire 37.0 °C ± 0.1 °C\n"
                 "Coupe thermique + boucle de régulation PID",
                 fontsize=12.5, fontweight="bold", color=RATIS_DARK)

    # Enceinte isolée (coupe)
    ax.add_patch(Rectangle((1.0, 1.0), 5.5, 4.5, facecolor="#fff7e0",
                           edgecolor=RATIS_DARK, linewidth=2.5, zorder=1))
    ax.add_patch(Rectangle((1.3, 1.3), 4.9, 3.9, facecolor="#ffe9c9",
                           edgecolor=RATIS_GOLD, linewidth=1.5, zorder=1))
    ax.text(3.75, 5.0, "Enceinte 50 L — mousse polyuréthane 5 cm",
            ha="center", fontsize=9, style="italic", color=RATIS_DARK)

    # Intérieur : résistances + capteur + culture
    _box(ax, 1.6, 1.6, 1.5, 0.9, "Résistances\nKapton\n(chauffage)", "#ffb3b3")
    _box(ax, 4.5, 1.6, 1.5, 0.9, "Capteur\nPT100\n(précision)", "#cfe0ff")
    _box(ax, 3.0, 3.2, 1.5, 1.0, "Culture\ncellulaire\n37 °C", "#bfe6bf")
    # flux thermique
    ax.annotate("", xy=(3.4, 3.2), xytext=(2.4, 2.5),
                arrowprops=dict(arrowstyle="->", color=RATIS_RED, lw=2))
    ax.text(2.3, 2.9, "chaleur", fontsize=8, color=RATIS_RED)
    ax.annotate("", xy=(4.9, 3.0), xytext=(5.2, 2.5),
                arrowprops=dict(arrowstyle="->", color=RATIS_BLUE, lw=2))

    # Boucle de régulation (droite)
    _box(ax, 7.5, 4.3, 1.8, 1.0, "ESP32\nPID\n(validé simu)", "#fff3b0")
    _box(ax, 7.5, 2.5, 1.8, 1.0, "MOSFET\nPWM\n(puissance)", "#e0b3ff")
    ax.annotate("", xy=(7.5, 4.8), xytext=(6.0, 2.05),
                arrowprops=dict(arrowstyle="->", color=RATIS_BLUE, lw=1.5))
    ax.text(7.1, 3.6, "T mesurée", fontsize=8, color=RATIS_BLUE, rotation=35)
    ax.annotate("", xy=(7.5, 3.0), xytext=(8.4, 4.3),
                arrowprops=dict(arrowstyle="->", color=RATIS_RED, lw=1.5))
    ax.text(8.7, 3.6, "commande", fontsize=8, color=RATIS_RED, rotation=-55)
    ax.annotate("", xy=(3.1, 2.05), xytext=(7.5, 2.9),
                arrowprops=dict(arrowstyle="->", color=RATIS_RED, lw=1.5))

    ax.text(0.8, 0.3,
            "CONCEPTION : la mousse PU (λ=0.024 W/m·K) limite les fuites → ~0.8 W suffisent pour\n"
            "tenir 37 °C dans 35 °C ambiant. Le PID (Kp/Ki/Kd validés en simulation) compense les\n"
            "variations. Coupure matérielle si T > 42 °C (sécurité, pas négociable).",
            fontsize=8.5, style="italic",
            bbox=dict(boxstyle="round", facecolor="#fffbe6", edgecolor=RATIS_GOLD))
    save(fig, "01_plan_incubateur.png")


# ============================================ 2. PLAN THERMOCYCLEUR PCR
def fig_plan_pcr():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.axis("off")
    ax.set_title("PLAN DE CONCEPTION — Thermocycleur PCR (bloc alu + Peltier)\n"
                 "Cycles 95/55/72 °C, homogénéité inter-puits ±0.5 °C",
                 fontsize=12.5, fontweight="bold", color=RATIS_DARK)

    # Empilement vertical (coupe)
    ax.add_patch(Rectangle((2.0, 4.6), 4.0, 0.7, facecolor="#cfe0ff",
                           edgecolor=RATIS_DARK, linewidth=2, zorder=2))
    ax.text(4.0, 4.95, "Bloc aluminium 200 g + puits pour tubes PCR", ha="center",
            fontsize=9, fontweight="bold")
    for px in np.linspace(2.4, 5.6, 8):  # puits
        ax.add_patch(Circle((px, 4.95), 0.12, facecolor=RATIS_DARK, zorder=3))
    ax.add_patch(Rectangle((2.0, 3.9), 4.0, 0.7, facecolor="#ffd9b3",
                           edgecolor=RATIS_DARK, linewidth=2, zorder=2))
    ax.text(4.0, 4.25, "Pâte thermique haute performance", ha="center", fontsize=9)
    ax.add_patch(Rectangle((2.0, 3.2), 4.0, 0.7, facecolor="#e0b3ff",
                           edgecolor=RATIS_DARK, linewidth=2, zorder=2))
    ax.text(4.0, 3.55, "4× Modules Peltier TEC1-12706 (240 W)", ha="center",
            fontsize=9, fontweight="bold")
    ax.add_patch(Rectangle((2.0, 2.2), 4.0, 1.0, facecolor="#bfe6bf",
                           edgecolor=RATIS_DARK, linewidth=2, zorder=2))
    ax.text(4.0, 2.7, "Dissipateur + ventilateur (côté chaud)", ha="center", fontsize=9)

    # Électronique de contrôle
    _box(ax, 7.5, 4.3, 1.9, 1.1, "ESP32\nMPC/PID\nprédictif", "#fff3b0")
    _box(ax, 7.5, 2.5, 1.9, 1.0, "Pont H\n(inversion\npolarité)", "#f0f0f0")
    ax.annotate("", xy=(7.5, 4.8), xytext=(6.0, 4.95),
                arrowprops=dict(arrowstyle="->", color=RATIS_BLUE, lw=1.5))
    ax.annotate("", xy=(7.5, 3.0), xytext=(6.0, 3.55),
                arrowprops=dict(arrowstyle="->", color=RATIS_RED, lw=1.5))

    ax.text(0.8, 0.9,
            "CONCEPTION : l'aluminium diffuse la chaleur uniformément (λ=167 W/m·K) → tous les\n"
            "puits à la même température. Les Peltier POMPENT la chaleur dans les deux sens\n"
            "(chauffe/refroidit) via le pont H. Le contrôle prédictif (MPC) anticipe l'inertie\n"
            "thermique du bloc pour des rampes nettes sans dépassement.",
            fontsize=8.5, style="italic",
            bbox=dict(boxstyle="round", facecolor="#fffbe6", edgecolor=RATIS_GOLD))
    save(fig, "02_plan_pcr.png")


# ============================================ 3. APPAREILS MONTÉS
def fig_appareils_montes():
    fig, axs = plt.subplots(1, 3, figsize=(15, 6))
    fig.suptitle("RATISS-BIOLAB — Les 3 appareils du labo humide souverain, une fois montés",
                 fontsize=13, fontweight="bold", color=RATIS_DARK)

    # Incubateur
    ax = axs[0]; ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_title("Incubateur cellulaire", fontsize=11, fontweight="bold", color=RATIS_DARK)
    ax.add_patch(FancyBboxPatch((2.5, 1.5), 5, 6.5, boxstyle="round,pad=0.05",
                                facecolor="#fff7e0", edgecolor=RATIS_DARK, linewidth=2.5))
    ax.add_patch(Rectangle((3.2, 6.6), 3.6, 1.0, facecolor="#001a00",
                           edgecolor="lime", linewidth=2))
    ax.text(5.0, 7.3, "37.0 °C", ha="center", va="center", color="lime",
            fontsize=13, fontweight="bold", family="monospace")
    ax.text(5.0, 6.9, "PID stable", ha="center", va="center", color="lime",
            fontsize=8, family="monospace")
    ax.add_patch(Rectangle((3.2, 2.5), 3.6, 3.5, facecolor="#ffe9c9",
                           edgecolor=RATIS_GOLD, linewidth=2))
    ax.text(5.0, 4.2, "Porte\nvitrée", ha="center", va="center", fontsize=10,
            color=RATIS_DARK, fontweight="bold")

    # Thermocycleur PCR
    ax = axs[1]; ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_title("Thermocycleur PCR", fontsize=11, fontweight="bold", color=RATIS_DARK)
    ax.add_patch(FancyBboxPatch((2.0, 3.0), 6, 4.5, boxstyle="round,pad=0.05",
                                facecolor="#2c3e50", edgecolor="black", linewidth=2.5))
    ax.add_patch(Rectangle((2.8, 6.3), 4.4, 0.9, facecolor="#cfe0ff",
                           edgecolor=RATIS_DARK, linewidth=1.5))
    for px in np.linspace(3.3, 6.7, 8):
        ax.add_patch(Circle((px, 6.75), 0.14, facecolor=RATIS_DARK))
    ax.add_patch(Rectangle((2.8, 4.6), 2.0, 1.2, facecolor="#001a00",
                           edgecolor="lime", linewidth=2))
    ax.text(3.8, 5.5, "72 °C", ha="center", color="lime", fontsize=11,
            fontweight="bold", family="monospace")
    ax.text(3.8, 5.0, "cycle 12/30", ha="center", color="lime", fontsize=7,
            family="monospace")
    ax.add_patch(Rectangle((5.2, 4.6), 2.4, 1.2, facecolor="#3a3a3a",
                           edgecolor="#666", linewidth=1.5))
    ax.text(6.4, 5.2, "VENTILATION", ha="center", va="center", color="#aaa",
            fontsize=8)

    # Spectrophotomètre
    ax = axs[2]; ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_title("Spectrophotomètre", fontsize=11, fontweight="bold", color=RATIS_DARK)
    ax.add_patch(FancyBboxPatch((2.0, 3.5), 6, 3.5, boxstyle="round,pad=0.05",
                                facecolor="#1a1a1a", edgecolor="black", linewidth=2.5))
    ax.add_patch(Rectangle((3.0, 5.5), 1.2, 1.0, facecolor="#2a5a8a",
                           edgecolor="#9ad", linewidth=1.5))
    ax.text(3.6, 6.0, "LED\n280 nm", ha="center", va="center", color="white",
            fontsize=7, fontweight="bold")
    ax.add_patch(Rectangle((4.6, 5.6), 0.8, 0.8, facecolor="#e8f4ff",
                           edgecolor=RATIS_BLUE, linewidth=2))
    ax.text(5.0, 6.0, "cuve", ha="center", va="center", fontsize=7)
    ax.add_patch(Rectangle((5.8, 5.5), 1.4, 1.0, facecolor="#3d0d3d",
                           edgecolor="#c5c", linewidth=1.5))
    ax.text(6.5, 6.0, "capteur", ha="center", va="center", color="#e8e",
            fontsize=8)
    ax.annotate("", xy=(5.8, 6.0), xytext=(5.4, 6.0),
                arrowprops=dict(arrowstyle="->", color="#9df", lw=2))
    ax.add_patch(Rectangle((3.0, 4.0), 4.0, 1.0, facecolor="#001a00",
                           edgecolor="lime", linewidth=2))
    ax.text(5.0, 4.6, "A280 = 0.42", ha="center", color="lime", fontsize=10,
            fontweight="bold", family="monospace")
    ax.text(5.0, 4.2, "SIRT6 : 10 µM", ha="center", color="lime", fontsize=7,
            family="monospace")

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    save(fig, "03_appareils_montes.png")


# ============================================ 4. COURBES THERMIQUES
def fig_courbes_thermiques():
    from ratiss_biolab.thermal import (Incubator, PCRBlock, PID,
                                       simulate_incubator, simulate_pcr_cycle)

    fig, axs = plt.subplots(2, 1, figsize=(12, 9))
    fig.suptitle("Validation thermique — Incubateur 37 °C & cycles PCR",
                 fontsize=13, fontweight="bold", color=RATIS_DARK)

    # Incubateur
    inc = Incubator()
    pid = PID(kp=0.4, ki=0.02, kd=8.0)
    r = simulate_incubator(inc, pid, t_amb_c=35.0, setpoint_c=37.0, hours=1.0, seed=1)
    t_min = r["t_s"] / 60.0
    axs[0].plot(t_min, r["t_in_c"], color=RATIS_RED, lw=2, label="T interne")
    axs[0].axhline(37.0, color=RATIS_GREEN, linestyle="--", label="consigne 37 °C")
    axs[0].axhspan(36.9, 37.1, color=RATIS_GREEN, alpha=0.15, label="tolérance ±0.1 °C")
    axs[0].axhline(35.0, color=RATIS_BLUE, linestyle=":", label="ambiante 35 °C")
    axs[0].set_ylabel("Température (°C)")
    axs[0].set_title(f"Incubateur — erreur RMS {r['rms_error_c']*1000:.0f} mK, "
                     f"dans la tolérance : {r['within_tolerance']}")
    axs[0].set_xlabel("temps (min)"); axs[0].legend(fontsize=8); axs[0].set_ylim(34, 38.5)

    # PCR
    block = PCRBlock()
    pid2 = PID(kp=0.6, ki=0.1, kd=0.5, u_min=-1.0, u_max=1.0)
    stages = [(95.0, 30.0), (55.0, 30.0), (72.0, 60.0)]
    r2 = simulate_pcr_cycle(block, pid2, stages, ambient_c=25.0, n_cycles=2, dt_s=0.1)
    axs[1].plot(r2["t_s"], r2["t_block_c"], color=RATIS_RED, lw=2, label="T bloc alu")
    axs[1].plot(r2["t_s"], r2["target_c"], color=RATIS_DARK, lw=1, linestyle="--",
                label="consigne", alpha=0.7)
    axs[1].set_ylabel("Température (°C)"); axs[1].set_xlabel("temps (s)")
    axs[1].set_title("Thermocycleur PCR — 2 cycles (dénaturation 95 / hybridation 55 / élongation 72)")
    axs[1].legend(fontsize=8)
    for xc, lab in [(95, "95"), (55, "55"), (72, "72")]:
        axs[1].axhline(xc, color="#ccc", linestyle=":", lw=0.8)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save(fig, "04_courbes_thermiques.png")


# ============================================ 5. SPECTRES PROTÉINES
def fig_spectres():
    from ratiss_biolab.optics import CIRBP, PRESTIN, SIRT6, absorption_spectrum

    fig, ax = plt.subplots(figsize=(11, 6))
    conc = 10e-6  # 10 µM
    for protein, color in [(SIRT6, RATIS_GREEN), (PRESTIN, RATIS_BLUE),
                           (CIRBP, RATIS_GOLD)]:
        lam, a = absorption_spectrum(protein, conc)
        ax.plot(lam, a, lw=2.5, color=color,
                label=f"{protein.name} (ε280={protein.epsilon_280/1000:.0f}k M⁻¹cm⁻¹)")
    ax.axvline(280, color=RATIS_RED, linestyle="--", lw=1.5)
    ax.text(281, ax.get_ylim()[1]*0.9, "280 nm\n(dosage protéines)", color=RATIS_RED,
            fontsize=9)
    ax.set_xlabel("Longueur d'onde (nm)"); ax.set_ylabel("Absorbance (u.a.)")
    ax.set_title("Spectres d'absorption UV des protéines cibles RATISS (10 µM)\n"
                 "Loi de Beer-Lambert : A = ε·c·ℓ", fontsize=12.5,
                 fontweight="bold", color=RATIS_DARK)
    ax.legend(fontsize=9)
    fig.tight_layout()
    save(fig, "05_spectres_proteines.png")


# ============================================ 6. ERREUR MESURE SPECTRO
def fig_erreur_spectro():
    from ratiss_biolab.optics import (LowCostSpectrometer, SIRT6,
                                      concentration_measurement_error)

    fig, ax = plt.subplots(figsize=(10, 6))
    spec = LowCostSpectrometer()
    concs = np.array([1, 2, 5, 10, 20, 50]) * 1e-6  # 1 à 50 µM
    err_mean, err_std = [], []
    for c in concs:
        res = concentration_measurement_error(SIRT6, c, spec, n_trials=60, seed=0)
        err_mean.append(100*res["rel_error_mean_frac"])
        err_std.append(100*res["rel_error_std_frac"])
    ax.errorbar(concs*1e6, err_mean, yerr=err_std, fmt="o-", color=RATIS_GREEN,
                lw=2, capsize=5, label="erreur mesurée ± σ")
    ax.axhline(5, color=RATIS_RED, linestyle="--", label="tolérance biologique ±5 %")
    ax.axhline(-5, color=RATIS_RED, linestyle="--")
    ax.axhline(0, color="#888", linestyle=":", lw=1)
    ax.set_xscale("log")
    ax.set_xlabel("Concentration SIRT6 (µM)")
    ax.set_ylabel("Erreur relative (%)")
    ax.set_title("Précision du spectrophotomètre low-cost (capteur TCS34725)\n"
                 "Calibration 2 points + moyennage ×16 → erreur < 5 % pour la gamme de\n"
                 "travail (≥ 5 µM). Aux très faibles concentrations, l'offset d'absorbance\n"
                 "domine le signal : mesurer plus concentré ou diluer moins.",
                 fontsize=11.5, fontweight="bold", color=RATIS_DARK)
    ax.legend(fontsize=9)
    fig.tight_layout()
    save(fig, "06_erreur_spectro.png")


# ============================================ 7. LOGO RATIS LABS
def fig_logo():
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    fig.patch.set_facecolor(RATIS_DARK)
    ax.set_facecolor(RATIS_DARK)
    for angle, col in [(0, RATIS_GREEN), (60, RATIS_GOLD), (120, RATIS_BLUE)]:
        th = np.linspace(0, 2*np.pi, 200)
        x = 3.2*np.cos(th); y = 1.2*np.sin(th)
        a = np.radians(angle)
        xr = x*np.cos(a) - y*np.sin(a); yr = x*np.sin(a) + y*np.cos(a)
        ax.plot(5+xr, 5.6+yr, color=col, lw=3, alpha=0.9)
    ax.add_patch(Circle((5, 5.6), 0.7, facecolor=RATIS_GOLD,
                        edgecolor="white", linewidth=2, zorder=5))
    ax.text(5, 3.4, "RATIS LABS", ha="center", va="center", fontsize=34,
            fontweight="bold", color="white", family="sans-serif")
    ax.text(5, 2.7, "Souveraineté technologique · Cameroun",
            ha="center", va="center", fontsize=12, color=RATIS_GOLD, style="italic")
    save(fig, "07_logo_ratis_labs.png", facecolor=RATIS_DARK)


if __name__ == "__main__":
    print("Génération des figures RATISS-BIOLAB...")
    fig_plan_incubateur()
    fig_plan_pcr()
    fig_appareils_montes()
    fig_courbes_thermiques()
    fig_spectres()
    fig_erreur_spectro()
    fig_logo()
    print("Toutes les figures sont dans docs/images/")
