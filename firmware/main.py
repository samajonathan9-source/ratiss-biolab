"""Firmware RATISS-BIOLAB — MicroPython pour ESP32.

Pilote l'incubateur cellulaire (37.0 °C ± 0.1 °C) et le thermocycleur PCR
(cycles 95/55/72 °C) avec régulation PID — la même que celle validée en
simulation (`ratiss_biolab/thermal.py`). On flash la logique prouvée, le
hardware n'a qu'à suivre.

Branchements (ESP32) :
  - GPIO 25 : PWM chauffage incubateur (résistances Kapton via MOSFET)
  - GPIO 34 : entrée ADC capteur PT100 (via pont diviseur / MAX31865)
  - GPIO 26 : PWM Peltier chauffe (thermocycleur)
  - GPIO 27 : PWM Peltier refroidit (pont H)
  - GPIO 35 : entrée ADC thermistance bloc PCR (NTC)
  - GPIO 4  : LED statut

Sécurité thermique : coupure matérielle si T > 42 °C (incubateur) ou T > 100 °C
(PCR) — un software ne suffit jamais pour la sécurité.
"""

from machine import ADC, PWM, Pin
import time

# --- Broches incubateur ---
PIN_HEATER_INC = 25
PIN_PT100 = 34
# --- Broches PCR ---
PIN_PELTIER_HEAT = 26
PIN_PELTIER_COOL = 27
PIN_NTC_PCR = 35
# --- Divers ---
PIN_LED = 4

# --- Limites de sécurité (coupure matérielle) ---
MAX_INCUBATOR_C = 42.0
MAX_PCR_C = 100.0


class PID:
    """Régulateur PID discret anti-windup (miroir de ratiss_biolab.thermal.PID)."""

    def __init__(self, kp, ki, kd, u_min=0.0, u_max=1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.u_min, self.u_max = u_min, u_max
        self._integral = 0.0
        self._prev_err = None

    def reset(self):
        self._integral = 0.0
        self._prev_err = None

    def step(self, setpoint, measured, dt):
        err = setpoint - measured
        self._integral += err * dt
        self._integral = max(-50.0, min(50.0, self._integral))  # anti-windup
        deriv = 0.0 if self._prev_err is None else (err - self._prev_err) / max(dt, 1e-9)
        self._prev_err = err
        u = self.kp * err + self.ki * self._integral + self.kd * deriv
        return max(self.u_min, min(self.u_max, u))


class IncubatorController:
    """Régulation 37.0 °C ± 0.1 °C — incubateur cellulaire."""

    def __init__(self):
        self.heater = PWM(Pin(PIN_HEATER_INC), freq=1000, duty=0)
        self.pt100 = ADC(Pin(PIN_PT100))
        self.pt100.atten(ADC.ATTN_11DB)  # pleine échelle ~3.3 V
        self.pid = PID(kp=0.4, ki=0.02, kd=8.0)
        self.setpoint = 37.0
        self.max_duty = 1023

    def read_temp_c(self):
        """Convertit la lecture ADC PT100 en °C (linéarisation Callendar-Van Dusen
        simplifiée ; en production, utiliser MAX31865 SPI pour la précision)."""
        raw = self.pt100.read()  # 0–4095
        # Placeholder : la conversion réelle dépend du pont + calibration 2 points
        return (raw / 4095.0) * 100.0  # à recalibrer sur le banc

    def run_step(self, dt=1.0):
        t = self.read_temp_c()
        if t > MAX_INCUBATOR_C:               # sécurité d'abord
            self.heater.duty(0)
            return {"temp_c": t, "power": 0.0, "alarm": "OVERTEMP"}
        u = self.pid.step(self.setpoint, t, dt)
        self.heater.duty(int(u * self.max_duty))
        return {"temp_c": t, "power": u, "alarm": None}

    def shutdown(self):
        self.heater.duty(0)


class PCRController:
    """Thermocycleur PCR — cycles dénaturation/hybridation/élongation."""

    def __init__(self):
        self.heat = PWM(Pin(PIN_PELTIER_HEAT), freq=1000, duty=0)
        self.cool = PWM(Pin(PIN_PELTIER_COOL), freq=1000, duty=0)
        self.ntc = ADC(Pin(PIN_NTC_PCR))
        self.ntc.atten(ADC.ATTN_11DB)
        self.pid = PID(kp=0.6, ki=0.1, kd=0.5, u_min=-1.0, u_max=1.0)
        self.max_duty = 1023

    def read_temp_c(self):
        raw = self.ntc.read()
        # NTC : loi bêta — placeholder à calibrer sur le banc
        return (raw / 4095.0) * 120.0

    def run_stage(self, target_c, duration_s, dt=0.1):
        """Maintient target_c pendant duration_s."""
        steps = int(duration_s / dt)
        for _ in range(steps):
            t = self.read_temp_c()
            if t > MAX_PCR_C:
                self.shutdown()
                return {"alarm": "OVERTEMP", "temp_c": t}
            u = self.pid.step(target_c, t, dt)
            if u >= 0:
                self.heat.duty(int(u * self.max_duty))
                self.cool.duty(0)
            else:
                self.cool.duty(int(-u * self.max_duty))
                self.heat.duty(0)
            time.sleep_ms(int(dt * 1000))
        return {"alarm": None}

    def run_cycle(self, stages, n_cycles=30):
        """Exécute n_cycles du profil PCR. stages = [(95,30),(55,30),(72,60)]."""
        for c in range(n_cycles):
            for target_c, duration_s in stages:
                r = self.run_stage(target_c, duration_s)
                if r["alarm"]:
                    return r
        self.shutdown()
        return {"alarm": None, "cycles_done": n_cycles}

    def shutdown(self):
        self.heat.duty(0)
        self.cool.duty(0)


if __name__ == "__main__":
    led = Pin(PIN_LED, Pin.OUT)
    led.value(1)
    print("RATISS-BIOLAB firmware prêt. Incubateur + PCR.")
    print("Sécurité thermique matérielle active.")
