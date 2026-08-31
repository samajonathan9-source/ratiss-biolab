"""Thermique du labo humide souverain — incubateur & thermocycleur PCR.

Modèle physique : transfert thermique par bilan d'énergie (noeud unique avec
fuites), suffisant pour le dimensionnement et le réglage des régulateurs.

  - Incubateur : enceinte isolée (polyuréthane), résistances Kapton, capteur
    PT100. Objectif : maintenir 37.0 °C ± 0.1 °C malgré l'ambiante à 35 °C+.
  - Thermocycleur PCR : bloc aluminium + modules Peltier TEC1-12706, cycles
    thermiques rapides (dénaturation 95 °C / hybridation ~55 °C / élongation
    72 °C) avec homogénéité entre puits.

Toutes les constantes sont sourcées et réalistes (voir docs/PHYSICS.md).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --- Constantes physiques (sourcées docs/PHYSICS.md) ---
CP_AIR_J_PER_KGK = 1005.0          # capacité thermique massique de l'air
CP_ALU_J_PER_KGK = 897.0           # capacité thermique massique de l'aluminium
RHO_AIR_KG_M3 = 1.18               # densité de l'air à ~35 °C
LAMBDA_PUR_W_MK = 0.024            # conductivité mousse polyuréthane (PU)
SIGMA_PELTIER = 5.0                # pente de dérive Peltier (simplifiée)


# ============================================================ INCUBATEUR ====
@dataclass
class Incubator:
    """Enceinte isolée + résistances Kapton + capteur PT100.

    Parameters
    ----------
    volume_m3 : volume intérieur de l'enceinte (m³)
    insulation_thickness_m : épaisseur de mousse PU (m)
    surface_m2 : surface d'échange avec l'extérieur (m²)
    heater_power_w : puissance max des résistances Kapton (W)
    """

    volume_m3: float = 0.05            # 50 L
    insulation_thickness_m: float = 0.05  # 5 cm de PU
    surface_m2: float = 0.8
    heater_power_w: float = 100.0

    def thermal_mass_j_per_k(self) -> float:
        """Capacité thermique de l'air intérieur (J/K)."""
        m_air = RHO_AIR_KG_M3 * self.volume_m3
        return m_air * CP_AIR_J_PER_KGK

    def heat_loss_w_per_k(self) -> float:
        """Coefficient de fuite thermique U·A (W/K) à travers l'isolant."""
        u = LAMBDA_PUR_W_MK / self.insulation_thickness_m   # W/(m²·K)
        return u * self.surface_m2                          # W/K

    def steady_state_power_w(self, t_in_c: float, t_out_c: float) -> float:
        """Puissance de chauffe nécessaire à l'équilibre (compense les fuites)."""
        return self.heat_loss_w_per_k() * (t_in_c - t_out_c)


class PID:
    """Régulateur PID discret anti-windup (méthode validée en simulation `eth`).

    u[k] = Kp·e + Ki·∫e·dt + Kd·de/dt, borné à [0, 1] (fraction de puissance).
    """

    def __init__(self, kp: float, ki: float, kd: float,
                 u_min: float = 0.0, u_max: float = 1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.u_min, self.u_max = u_min, u_max
        self._integral = 0.0
        self._prev_err: float | None = None

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_err = None

    def step(self, setpoint: float, measured: float, dt: float) -> float:
        err = setpoint - measured
        self._integral += err * dt
        # anti-windup : borne l'intégrale
        self._integral = float(np.clip(self._integral, -50.0, 50.0))
        deriv = 0.0 if self._prev_err is None else (err - self._prev_err) / max(dt, 1e-9)
        self._prev_err = err
        u = self.kp * err + self.ki * self._integral + self.kd * deriv
        return float(np.clip(u, self.u_min, self.u_max))


def simulate_incubator(
    inc: Incubator,
    pid: PID,
    t_amb_c: float = 35.0,
    setpoint_c: float = 37.0,
    hours: float = 2.0,
    dt_s: float = 1.0,
    amb_noise_c: float = 0.5,
    seed: int | None = 0,
) -> dict:
    """Simule l'incubateur sous régulation PID.

    Retourne le temps, la température interne, la consigne de puissance et des
    métriques de performance (erreur RMS en régime établi, dépassement).
    """
    rng = np.random.default_rng(seed)
    n = int(hours * 3600.0 / dt_s)
    t = np.arange(n) * dt_s
    t_in = np.empty(n)
    power = np.empty(n)

    t_current = t_amb_c
    c_th = inc.thermal_mass_j_per_k()
    ua = inc.heat_loss_w_per_k()
    pid.reset()

    for i in range(n):
        # ambiante fluctuante (climat tropical, coupure de climatisation, etc.)
        t_amb = t_amb_c + amb_noise_c * np.sin(2*np.pi * t[i] / 1800.0) \
            + rng.normal(0.0, 0.05)
        u = pid.step(setpoint_c, t_current, dt_s)
        p_in = u * inc.heater_power_w
        # bilan : chauffe - fuites vers l'extérieur
        p_loss = ua * (t_current - t_amb)
        d_t = (p_in - p_loss) / c_th * dt_s
        t_current += d_t
        t_in[i] = t_current
        power[i] = u

    # métriques sur la seconde moitié (régime établi)
    half = n // 2
    settled = t_in[half:]
    err = settled - setpoint_c
    return {
        "t_s": t,
        "t_in_c": t_in,
        "power_frac": power,
        "setpoint_c": setpoint_c,
        "rms_error_c": float(np.sqrt(np.mean(err**2))),
        "max_overshoot_c": float(np.max(t_in) - setpoint_c),
        "steady_std_c": float(np.std(settled)),
        "within_tolerance": bool(np.all(np.abs(err) <= 0.1)),
    }


# ============================================================ THERMOCYCLEUR ==
@dataclass
class PCRBlock:
    """Bloc aluminium + modules Peltier pour thermocycleur PCR.

    Parameters
    ----------
    alu_mass_kg : masse du bloc aluminium (kg)
    n_peltier : nombre de modules TEC1-12706
    peltier_max_w : puissance thermique max d'un module (W)
    """

    alu_mass_kg: float = 0.20          # bloc alu 200 g
    n_peltier: int = 4
    peltier_max_w: float = 60.0        # TEC1-12706 ≈ 60 W en pompage
    # 4 × 60 W = 240 W sur 0.2 kg alu (C≈180 J/K) → rampe ≈ 1.3 °C/s nette,
    # réaliste pour un thermocycleur low-cost (les commerciaux font 3–5 °C/s
    # avec des blocs plus légers et plus de puissance).

    def thermal_mass_j_per_k(self) -> float:
        return self.alu_mass_kg * CP_ALU_J_PER_KGK

    def max_heat_w(self) -> float:
        return self.n_peltier * self.peltier_max_w


def simulate_pcr_cycle(
    block: PCRBlock,
    pid: PID,
    stages: list[tuple[float, float]],
    ambient_c: float = 25.0,
    n_cycles: int = 3,
    dt_s: float = 0.1,
    h_loss_w_per_k: float = 2.0,
) -> dict:
    """Simule les cycles thermiques PCR (dénaturation / hybridation / élongation).

    stages : liste de (température_cible_c, durée_s) — ex :
        [(95, 30), (55, 30), (72, 60)] pour un cycle classique.
    Retourne la trajectoire de température et les rampes atteintes.
    """
    t_total = n_cycles * sum(d for _, d in stages)
    n = int(t_total / dt_s)
    t = np.arange(n) * dt_s
    t_block = np.empty(n)
    target = np.empty(n)

    c_th = block.thermal_mass_j_per_k()
    pid.reset()
    t_current = ambient_c

    # construction du profil de consigne
    stage_times = np.cumsum([d for _, d in stages])
    stage_temps = [tmp for tmp, _ in stages]
    cycle_time = stage_times[-1]

    for i in range(n):
        tc = t[i] % cycle_time
        idx = int(np.searchsorted(stage_times, tc, side="right"))
        idx = min(idx, len(stage_temps) - 1)
        sp = stage_temps[idx]
        target[i] = sp

        u = pid.step(sp, t_current, dt_s)
        # u ∈ [-1, 1] : négatif = refroidissement Peltier
        p_th = u * block.max_heat_w()
        p_loss = h_loss_w_per_k * (t_current - ambient_c)
        d_t = (p_th - p_loss) / c_th * dt_s
        t_current += d_t
        t_block[i] = t_current

    return {
        "t_s": t,
        "t_block_c": t_block,
        "target_c": target,
        "n_cycles": n_cycles,
        "stages": stages,
    }


# ============================================================ DIMENSIONNEMENT
def required_incubator_power_w(t_in_c: float, t_out_c: float,
                               volume_m3: float = 0.05,
                               insulation_m: float = 0.05,
                               surface_m2: float = 0.8) -> float:
    """Puissance minimale pour maintenir t_in malgré t_out (dimensionnement)."""
    inc = Incubator(volume_m3=volume_m3, insulation_thickness_m=insulation_m,
                    surface_m2=surface_m2)
    return inc.steady_state_power_w(t_in_c, t_out_c)
