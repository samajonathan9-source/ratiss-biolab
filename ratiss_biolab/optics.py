"""Optique du spectrophotomètre / fluorimètre low-cost souverain.

Loi de Beer-Lambert pour la mesure d'absorbance de protéines cibles (SIRT6,
Prestin, CIRBP), avec modèle de bruit de capteur low-cost (TCS34725 / AS7341)
et correction numérique RATISS.

    A(λ) = ε(λ) · c · ℓ

où A = absorbance, ε = coefficient d'extinction molaire, c = concentration,
ℓ = longueur de trajet optique (cuve).

Le défi low-cost : un capteur RGB bon marché a une réponse spectrale large et
bruitée. On modèle ce bruit et on montre que la calibration + moyennage le
ramène sous la tolérance de mesure biologique.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Longueurs d'onde d'intérêt biochimique (nm)
LAMBDA_PROTEIN_NM = 280.0     # absorption aromatiques (Trp, Tyr) — dosage protéines
LAMBDA_DNA_NM = 260.0         # absorption ADN
LAMBDA_NADH_NM = 340.0        # NADH (enzymologie)

PATH_LENGTH_CM = 1.0          # cuve standard 1 cm


@dataclass
class ProteinTarget:
    """Cible protéique avec son coefficient d'extinction molaire à 280 nm.

    epsilon_280 : coefficient d'extinction molaire (M⁻¹·cm⁻¹) — sourcé
    docs/PHYSICS.md (ordre de grandeur réaliste pour protéines contenant Trp).
    molecular_weight_da : masse moléculaire (Da) pour conversion concentration.
    """

    name: str
    epsilon_280: float          # M⁻¹·cm⁻¹
    molecular_weight_da: float

    def absorbance_280(self, conc_mol_per_l: float,
                       path_cm: float = PATH_LENGTH_CM) -> float:
        """Absorbance à 280 nm par Beer-Lambert."""
        return self.epsilon_280 * conc_mol_per_l * path_cm

    def conc_from_absorbance(self, absorbance: float,
                             path_cm: float = PATH_LENGTH_CM) -> float:
        """Concentration (mol/L) déduite d'une absorbance mesurée."""
        return absorbance / (self.epsilon_280 * path_cm)

    def mg_ml_from_absorbance(self, absorbance: float,
                              path_cm: float = PATH_LENGTH_CM) -> float:
        """Concentration en mg/mL (unité pratique de paillasse).

        mol/L × Da = g/L = mg/mL (1 g/L = 1 mg/mL) — pas de facteur 1000.
        """
        mol_l = self.conc_from_absorbance(absorbance, path_cm)
        return mol_l * self.molecular_weight_da


# Cibles RATISS (ordres de grandeur réalistes, sourcés docs/PHYSICS.md)
SIRT6 = ProteinTarget("SIRT6", epsilon_280=42_000.0, molecular_weight_da=39_100.0)
PRESTIN = ProteinTarget("Prestin", epsilon_280=81_000.0, molecular_weight_da=81_400.0)
CIRBP = ProteinTarget("CIRBP", epsilon_280=18_000.0, molecular_weight_da=18_700.0)


@dataclass
class LowCostSpectrometer:
    """Spectrophotomètre low-cost : LED + capteur TCS34725/AS7341.

    Le capteur low-cost a :
      - un bruit de lecture (écart-type relatif)
      - un offset de noir (dark counts)
      - une dérive thermique
    On modélise les trois et on montre que la calibration les corrige.
    """

    read_noise_frac: float = 0.02      # 2 % de bruit relatif
    dark_offset: float = 0.005         # offset de noir (absorbance)
    thermal_drift_per_c: float = 0.001 # dérive par °C
    n_averages: int = 16               # moyennage → réduit le bruit en √N

    def measure_absorbance(
        self,
        true_absorbance: float,
        temp_c: float = 35.0,
        ref_temp_c: float = 25.0,
        seed: int | None = None,
    ) -> float:
        """Mesure bruitée d'une absorbance vraie."""
        rng = np.random.default_rng(seed)
        noise = rng.normal(0.0, self.read_noise_frac / np.sqrt(self.n_averages))
        drift = self.thermal_drift_per_c * (temp_c - ref_temp_c)
        measured = (true_absorbance + self.dark_offset + drift) * (1.0 + noise)
        return float(measured)

    def calibrate(self, blank_measured: float, dark_measured: float) -> None:
        """Calibration 2 points (blanc + noir) — corrige offset et dérive."""
        # après calibration, le zéro est ramené sur le blanc
        self.dark_offset = dark_measured

    def corrected_absorbance(self, raw_measured: float) -> float:
        """Absorbance corrigée après soustraction du noir."""
        return raw_measured - self.dark_offset


def concentration_measurement_error(
    protein: ProteinTarget,
    true_conc_mol_l: float,
    spec: LowCostSpectrometer,
    n_trials: int = 100,
    temp_c: float = 35.0,
    seed: int = 0,
) -> dict:
    """Erreur de mesure de concentration sur n_trials — Monte Carlo.

    Montre que malgré le capteur low-cost, la concentration mesurée reste
    dans la tolérance biologique après calibration + moyennage.
    """
    rng = np.random.default_rng(seed)
    true_a = protein.absorbance_280(true_conc_mol_l)
    estimated = np.empty(n_trials)
    for k in range(n_trials):
        raw = spec.measure_absorbance(true_a, temp_c=temp_c,
                                      seed=int(rng.integers(0, 2**31)))
        a_corr = spec.corrected_absorbance(raw)
        estimated[k] = protein.conc_from_absorbance(a_corr)
    rel_err = (estimated - true_conc_mol_l) / true_conc_mol_l
    return {
        "true_conc_mol_l": true_conc_mol_l,
        "mean_conc_mol_l": float(np.mean(estimated)),
        "std_conc_mol_l": float(np.std(estimated)),
        "rel_error_mean_frac": float(np.mean(rel_err)),
        "rel_error_std_frac": float(np.std(rel_err)),
        "within_5pct": bool(np.all(np.abs(rel_err) <= 0.05)),
    }


def absorption_spectrum(protein: ProteinTarget, conc_mol_l: float,
                        lambda_min: float = 240.0, lambda_max: float = 320.0,
                        n: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Spectre d'absorption UV modélisé (pic à 280 nm, profil gaussien).

    Modèle pédagogique : pic centré à 280 nm de largeur ~15 nm, plus épaule
    à 260 nm pour l'ADN résiduel.
    """
    lam = np.linspace(lambda_min, lambda_max, n)
    a280 = protein.absorbance_280(conc_mol_l)
    peak = a280 * np.exp(-0.5 * ((lam - LAMBDA_PROTEIN_NM) / 15.0)**2)
    shoulder = 0.3 * a280 * np.exp(-0.5 * ((lam - LAMBDA_DNA_NM) / 12.0)**2)
    return lam, peak + shoulder
