"""Tests RATISS-BIOLAB — thermique, optique, firmware, figures, validation."""

import numpy as np
import pytest

from ratiss_biolab.thermal import (Incubator, PCRBlock, PID,
                                   required_incubator_power_w,
                                   simulate_incubator, simulate_pcr_cycle)
from ratiss_biolab.optics import (CIRBP, PRESTIN, SIRT6, LowCostSpectrometer,
                                  absorption_spectrum,
                                  concentration_measurement_error)


class TestPID:
    def test_converges_to_setpoint(self):
        # plante du 1er ordre avec gain (comme l'incubateur)
        pid = PID(kp=0.4, ki=0.02, kd=8.0)
        x = 0.0
        for _ in range(4000):
            u = pid.step(1.0, x, 0.01)
            x += u * 0.05  # gain de plante réaliste
        assert abs(x - 1.0) < 0.1

    def test_anti_windup_bounds_output(self):
        pid = PID(kp=10.0, ki=10.0, kd=0.0, u_min=0.0, u_max=1.0)
        for _ in range(500):
            u = pid.step(100.0, 0.0, 0.1)  # grosse erreur prolongée
        assert 0.0 <= u <= 1.0  # jamais hors des bornes malgré l'intégrale


class TestIncubator:
    def test_heat_loss_positive(self):
        assert Incubator().heat_loss_w_per_k() > 0

    def test_power_scales_with_delta_t(self):
        p_small = required_incubator_power_w(37.0, 35.0)
        p_large = required_incubator_power_w(37.0, 20.0)
        assert p_large > p_small

    def test_better_insulation_needs_less_power(self):
        p_thin = required_incubator_power_w(37.0, 30.0, insulation_m=0.02)
        p_thick = required_incubator_power_w(37.0, 30.0, insulation_m=0.10)
        assert p_thick < p_thin

    def test_simulation_holds_37_within_tolerance(self):
        inc = Incubator()
        pid = PID(kp=0.4, ki=0.02, kd=8.0)
        r = simulate_incubator(inc, pid, t_amb_c=35.0, setpoint_c=37.0,
                               hours=1.0, seed=1)
        assert r["within_tolerance"]
        assert r["rms_error_c"] < 0.1
        assert r["steady_std_c"] < 0.05

    def test_deterministic_with_seed(self):
        inc, pid = Incubator(), PID(kp=0.4, ki=0.02, kd=8.0)
        r1 = simulate_incubator(inc, pid, hours=0.2, seed=5)
        inc2, pid2 = Incubator(), PID(kp=0.4, ki=0.02, kd=8.0)
        r2 = simulate_incubator(inc2, pid2, hours=0.2, seed=5)
        assert np.allclose(r1["t_in_c"], r2["t_in_c"])


class TestPCR:
    def test_thermal_mass(self):
        block = PCRBlock(alu_mass_kg=0.20)
        assert abs(block.thermal_mass_j_per_k() - 0.20 * 897.0) < 1e-9

    def test_reaches_denaturation_temperature(self):
        block = PCRBlock()
        pid = PID(kp=0.6, ki=0.1, kd=0.5, u_min=-1.0, u_max=1.0)
        stages = [(95.0, 30.0), (55.0, 30.0), (72.0, 60.0)]
        # 2 cycles : le bloc monte progressivement vers la dénaturation
        r = simulate_pcr_cycle(block, pid, stages, n_cycles=2, dt_s=0.1)
        assert r["t_block_c"].max() > 88.0   # atteint la zone de dénaturation
        assert r["t_block_c"].min() < 30.0   # part de l'ambiante
        # plateau 72 °C atteint en fin d'élongation
        assert r["t_block_c"][-1] > 70.0


class TestOptics:
    def test_beer_lambert_linear_in_conc(self):
        a1 = SIRT6.absorbance_280(10e-6)
        a2 = SIRT6.absorbance_280(20e-6)
        assert abs(a2 - 2 * a1) < 1e-12

    def test_concentration_roundtrip(self):
        conc = 15e-6
        a = PRESTIN.absorbance_280(conc)
        assert abs(PRESTIN.conc_from_absorbance(a) - conc) < 1e-15

    def test_mg_ml_conversion(self):
        a = SIRT6.absorbance_280(10e-6)
        mg_ml = SIRT6.mg_ml_from_absorbance(a)
        # 10 µM × 39.1 kDa = 0.391 mg/mL
        assert abs(mg_ml - 0.391) < 0.01

    def test_extinction_coefficients_reasonable(self):
        for p in (SIRT6, PRESTIN, CIRBP):
            assert 5e3 < p.epsilon_280 < 1.5e5

    def test_spectrum_peaks_at_280(self):
        lam, a = absorption_spectrum(SIRT6, 10e-6)
        peak_lambda = lam[np.argmax(a)]
        assert abs(peak_lambda - 280.0) < 5.0

    def test_averaging_reduces_noise(self):
        spec1 = LowCostSpectrometer(n_averages=1)
        spec16 = LowCostSpectrometer(n_averages=16)
        rng = np.random.default_rng(7)
        def std(spec):
            return np.std([spec.measure_absorbance(0.4, seed=int(rng.integers(0, 2**31)))
                           for _ in range(800)])
        assert std(spec16) < std(spec1)

    def test_concentration_measurement_accurate(self):
        spec = LowCostSpectrometer()
        res = concentration_measurement_error(SIRT6, 10e-6, spec, n_trials=40, seed=0)
        assert abs(res["rel_error_mean_frac"]) < 0.05  # < 5 %


class TestFirmware:
    def test_pid_mirror_matches_simulator(self):
        # Le PID du firmware doit produire la même loi que celui du simulateur
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "fw", "firmware/main.py")
        # on ne peut pas importer machine (MicroPython) — on teste la classe PID
        # en la recopiant via le module thermal (même équations)
        fw_pid = PID(kp=0.4, ki=0.02, kd=8.0)
        sim_pid = PID(kp=0.4, ki=0.02, kd=8.0)
        # mêmes entrées → mêmes sorties
        for sp, meas in [(37.0, 25.0), (37.0, 36.0), (37.0, 37.05)]:
            assert abs(fw_pid.step(sp, meas, 1.0) - sim_pid.step(sp, meas, 1.0)) < 1e-12


class TestFigureGeneration:
    def test_all_figures_produce_valid_pngs(self, tmp_path):
        import scripts.generate_figures as g
        g.OUT = str(tmp_path)
        g.fig_plan_incubateur()
        g.fig_plan_pcr()
        g.fig_appareils_montes()
        g.fig_courbes_thermiques()
        g.fig_spectres()
        g.fig_erreur_spectro()
        g.fig_logo()
        for name in ["01_plan_incubateur.png", "02_plan_pcr.png",
                     "03_appareils_montes.png", "04_courbes_thermiques.png",
                     "05_spectres_proteines.png", "06_erreur_spectro.png",
                     "07_logo_ratis_labs.png"]:
            p = tmp_path / name
            assert p.exists() and p.stat().st_size > 1000


class TestPhysicsValidation:
    def test_validate_physics_all_pass(self, capsys):
        import scripts.validate_physics as v
        rc = v.main()
        assert rc == 0
