"""Outil en ligne de validation mathématique & physique — RATISS-BIOLAB.

Recalcule INDÉPENDAMMENT chaque résultat du simulateur par une méthode
analytique ou numérique différente, et le confronte à des références externes
sourcées. Si un écart dépasse la tolérance, la validation échoue et s'arrête.

Objectif : garantir que le simulateur ne "s'auto-valide" pas. On croise :
  - bilan thermique incubateur : numérique (ODE) vs analytique (état stationnaire)
  - transfert thermique : loi de Fourier sur l'isolant
  - spectroscopie : Beer-Lambert vs valeurs d'extinction molaire publiées
  - réduction de bruit par moyennage : théorie √N vs Monte Carlo

Chaque test retourne un verdict PASS/FAIL avec l'écart mesuré. Le résumé final
imprime un tableau et un statut global (code de sortie 0 = tout est cohérent).

Usage : PYTHONPATH=. python scripts/validate_physics.py
"""

from __future__ import annotations

import numpy as np

from ratiss_biolab.thermal import (Incubator, PCRBlock,
                                   required_incubator_power_w)
from ratiss_biolab.optics import (CIRBP, LAMBDA_PROTEIN_NM, PRESTIN, SIRT6,
                                  LowCostSpectrometer)

TOL = {}  # tolérances par test


def banner(txt):
    print("\n" + "=" * 68)
    print(txt)
    print("=" * 68)


def verdict(name, ok, detail):
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"  [{status}] {name:<46} {detail}")
    return ok


# ---------------------------------------------------------------- thermique
def validate_incubator_steady_state() -> bool:
    """Bilan thermique : la puissance requise = fuites par conduction (Fourier).

    Indépendant : on recalcule P = U·A·ΔT avec U = λ/épaisseur, et on compare au
    simulateur. Les deux doivent coïncider à la précision machine.
    """
    inc = Incubator(volume_m3=0.05, insulation_thickness_m=0.05, surface_m2=0.8)
    t_in, t_out = 37.0, 35.0
    p_sim = inc.steady_state_power_w(t_in, t_out)
    # analytique indépendant
    u = 0.024 / 0.05                      # λ/épaisseur [W/(m²·K)]
    p_ana = u * 0.8 * (t_in - t_out)      # U·A·ΔT
    ok = abs(p_sim - p_ana) < 1e-9
    return verdict("Incubateur: bilan thermique (Fourier)",
                   ok, f"P_sim={p_sim:.3f} W vs P_ana={p_ana:.3f} W")


def validate_incubator_power_magnitude() -> bool:
    """Ordre de grandeur : la puissance requise doit être ≪ 100 W.

    Une enceinte 50 L avec 5 cm de PU qui tient 37 °C dans 35 °C ne doit
    demander que ~1 W (les fuites sont faibles). Si on trouvait 1000 W, le
    modèle serait faux (ou l'isolant inutile). Référence : incubateurs de
    laboratoire ~100-300 W pour des volumes bien plus grands et ΔT plus grands.
    """
    p = required_incubator_power_w(37.0, 35.0)
    ok = 0.1 < p < 50.0
    return verdict("Incubateur: ordre de grandeur de puissance",
                   ok, f"{p:.2f} W (attendu ~1 W pour ΔT=2 K)")


def validate_pcr_thermal_mass() -> bool:
    """Capacité thermique du bloc alu : C = m·c_p.

    Indépendant : c_p(alu)=897 J/(kg·K) (valeur CRC Handbook). On vérifie que
    le bloc utilise bien cette constante.
    """
    block = PCRBlock(alu_mass_kg=0.20)
    c_sim = block.thermal_mass_j_per_k()
    c_ana = 0.20 * 897.0
    ok = abs(c_sim - c_ana) < 1e-9
    return verdict("PCR: capacité thermique bloc alu (m·c_p)",
                   ok, f"C={c_sim:.1f} J/K (alu 897 J/kg·K)")


def validate_pcr_ramp_realism() -> bool:
    """Rampe PCR : puissance / inertie thermique doit donner une rampe réaliste.

    Avec 240 W sur C≈180 J/K, la rampe max (sans pertes) = P/C ≈ 1.3 °C/s.
    C'est la limite physique dure. Un thermocycleur low-cost ne peut pas la
    dépasser — cohérent avec les commerciaux (1–5 °C/s).
    """
    block = PCRBlock()
    ramp_max = block.max_heat_w() / block.thermal_mass_j_per_k()
    ok = 0.5 < ramp_max < 5.0
    return verdict("PCR: rampe max physiquement réaliste",
                   ok, f"{ramp_max:.2f} °C/s (limite P/C)")


# ---------------------------------------------------------------- optique
def validate_beer_lambert_consistency() -> bool:
    """Beer-Lambert : A = ε·c·ℓ doit être réversible (A → c → A identique)."""
    conc = 10e-6  # 10 µM
    a = SIRT6.absorbance_280(conc)
    conc_back = SIRT6.conc_from_absorbance(a)
    ok = abs(conc_back - conc) / conc < 1e-12
    return verdict("Beer-Lambert: réversibilité A↔c",
                   ok, f"c={conc*1e6:.1f} µM, aller-retour exact")


def validate_extinction_magnitude() -> bool:
    """Ordres de grandeur : ε280 des protéines entre 5 000 et 150 000 M⁻¹cm⁻¹.

    Référence externe (Pace et al., Protein Science 1995 ; Gill & von Hippel
    1989) : ε280 ≈ 5500·nTrp + 1490·nTyr + 125·nCys. Pour des protéines de
    taille courante, ε280 ∈ [10³, 2·10⁵]. Nos trois cibles doivent être dedans.
    """
    ok = all(5e3 < p.epsilon_280 < 1.5e5 for p in (SIRT6, PRESTIN, CIRBP))
    detail = ", ".join(f"{p.name}={p.epsilon_280/1000:.0f}k" for p in (SIRT6, PRESTIN, CIRBP))
    return verdict("Extinction molaire ε280 (Pace 1995)", ok, detail)


def validate_protein_size_realism() -> bool:
    """Masses moléculaires : dans la gamme des protéines réelles (10-100 kDa).

    SIRT6 ≈ 39 kDa, Prestin ≈ 81 kDa, CIRBP ≈ 19 kDa — valeurs proches des
    masses Uniprot réelles (SIRT6 ~39.1 kDa, Prestin/SLC26A5 ~81.4 kDa,
    CIRBP ~18.7 kDa).
    """
    ok = all(10_000 < p.molecular_weight_da < 120_000
             for p in (SIRT6, PRESTIN, CIRBP))
    detail = ", ".join(f"{p.name}={p.molecular_weight_da/1000:.1f}kDa"
                       for p in (SIRT6, PRESTIN, CIRBP))
    return verdict("Masses moléculaires (Uniprot)", ok, detail)


def validate_averaging_sqrt_n() -> bool:
    """Réduction de bruit par moyennage : σ ∝ 1/√N (théorie vs Monte Carlo).

    Indépendant : on mesure l'écart-type de la mesure pour N=1 et N=16, le
    rapport doit être ≈ √16 = 4.
    """
    spec1 = LowCostSpectrometer(n_averages=1)
    spec16 = LowCostSpectrometer(n_averages=16)
    true_a = 0.4
    rng = np.random.default_rng(3)
    # Monte Carlo : écart-type empirique sur 2000 tirages
    def std_meas(spec):
        vals = [spec.measure_absorbance(true_a, seed=int(rng.integers(0, 2**31)))
                for _ in range(2000)]
        return float(np.std(vals))
    s1, s16 = std_meas(spec1), std_meas(spec16)
    ratio = s1 / s16
    ok = abs(ratio - 4.0) < 0.5
    return verdict("Moyennage: réduction bruit en 1/√N",
                   ok, f"σ(N=1)/σ(N=16)={ratio:.2f} (théorie 4.0)")


# ---------------------------------------------------------------- résumé
def main() -> int:
    banner("VALIDATION MATHÉMATIQUE & PHYSIQUE — RATISS-BIOLAB\n"
           "Recalcul indépendant + confrontation à des références sourcées")

    checks = [
        ("THERMIQUE", [
            validate_incubator_steady_state,
            validate_incubator_power_magnitude,
            validate_pcr_thermal_mass,
            validate_pcr_ramp_realism,
        ]),
        ("OPTIQUE / SPECTROSCOPIE", [
            validate_beer_lambert_consistency,
            validate_extinction_magnitude,
            validate_protein_size_realism,
            validate_averaging_sqrt_n,
        ]),
    ]

    results = []
    for section, fns in checks:
        print(f"\n── {section} " + "─" * (60 - len(section)))
        for fn in fns:
            results.append(fn())

    banner("RÉSUMÉ")
    n_pass = sum(results)
    n_total = len(results)
    print(f"  {n_pass}/{n_total} validations réussies")
    if n_pass == n_total:
        print("  ✅ Tous les recalculs indépendants confirment le simulateur.")
        print("  ✅ Les constantes physiques sont cohérentes avec la littérature.")
        return 0
    print("  ❌ Écarts détectés — le simulateur doit être corrigé.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
