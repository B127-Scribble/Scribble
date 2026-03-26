import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

G0        = 9.80665
R_UNIV    = 8314.0
Q_E       = 1.602e-19
AMU       = 1.66054e-27
CP_AIR    = 1005.0
GAMMA_AIR = 1.4

def rocket_exhaust_velocity(gamma, R_spec, Tc, Pc, Pa):
    """
    Isentropic nozzle exit velocity (m/s).

    LEARN: Derived from energy conservation across the nozzle:
        ve = sqrt( 2γ/(γ-1) · R · Tc · [1 - (Pa/Pc)^((γ-1)/γ)] )

    gamma  : ratio of specific heats (~1.1-1.4 for rockets)
    R_spec : specific gas constant = R_universal / mol_weight (J/kg·K)
    Tc     : chamber temperature (K)
    Pc     : chamber pressure (Pa)
    Pa     : ambient pressure (Pa), use 0 for vacuum
    """
    if Pa >= Pc:
        return 0.0
    exponent = (gamma - 1.0) / gamma
    ve = np.sqrt(
        2.0 * gamma / (gamma - 1.0)
        * R_spec * Tc
        * (1.0 - (Pa / Pc) ** exponent)
    )
    return ve


def rocket_exit_pressure(gamma, Pc, area_ratio):
    """
    Estimate nozzle exit pressure from area ratio (approximation).

    LEARN: The real calculation requires iterating on the isentropic
    area-Mach relation A/A* = f(M). We use a log approximation here.
    In production you'd use scipy.optimize.brentq to solve it exactly.
    """
    if area_ratio <= 1.0:
        return Pc
    Me = 1.0 + 1.2 * np.log(area_ratio)
    Pe = Pc * (1.0 + (gamma - 1.0) / 2.0 * Me**2) ** (-gamma / (gamma - 1.0))
    return max(Pe, 100.0)


def rocket_thrust(mdot, ve, Pe, Pa, Ae):
    """
    Net rocket thrust (N).
    F = momentum_thrust + pressure_thrust
      = mdot·ve + (Pe - Pa)·Ae

    LEARN: Two contributions:
      1) Momentum thrust: mass flow × exhaust speed
      2) Pressure thrust: exit pressure difference × nozzle exit area
    At vacuum (Pa=0), both terms maximize thrust.
    """
    return mdot * ve + (Pe - Pa) * Ae


def tsiolkovsky(Isp, m0, mf):
    """
    Rocket equation: Δv = Isp · g0 · ln(m0/mf)

    LEARN: THE most important equation in rocketry.
    To double Δv you must square the mass ratio.
    That's why staging exists, and why Isp matters so much.
    """
    if mf <= 0 or m0 <= mf:
        return 0.0
    return Isp * G0 * np.log(m0 / mf)



def brayton_stations(T1, PR, TIT, eta_c, eta_t):
    """
    Brayton cycle temperatures at each station.

    LEARN: The 4 Brayton stations:
      1→2 Isentropic compression (real: divided by η_c)
      2→3 Constant-pressure combustion up to TIT
      3→4 Isentropic turbine expansion (real: multiplied by η_t)
      4→1 Heat rejection (exhaust)

    η_c = ideal_work / actual_work  → actual ΔT = ideal ΔT / η_c
    η_t = actual_work / ideal_work  → actual ΔT = η_t × ideal ΔT
    """
    g = GAMMA_AIR
    T2i = T1 * PR ** ((g - 1) / g)
    T2  = T1 + (T2i - T1) / eta_c
    T3  = TIT
    T4i = T3 * PR ** (-(g - 1) / g)
    T4  = T3 - eta_t * (T3 - T4i)
    return T1, T2, T3, T4


def jet_performance(V0, mdot_air, far, PR, TIT, eta_c, eta_t):
    T1, T2, T3, T4 = brayton_stations(288.0, PR, TIT, eta_c, eta_t)
    mdot_fuel = mdot_air * far
    Q_in = CP_AIR * (T3 - T2)
    Ve   = np.sqrt(max(0.0, 2 * CP_AIR * (T4 - 288.0) + V0**2))

    thrust  = (mdot_air + mdot_fuel) * Ve - mdot_air * V0
    tsfc    = mdot_fuel / max(thrust, 1.0)
    eta_th  = 0.5 * (Ve**2 - V0**2) / max(Q_in, 1.0)
    eta_p   = 2 * V0 / (V0 + Ve) if (V0 + Ve) > 0 else 0.0

    return {
        "thrust_kN":  thrust / 1000,
        "tsfc_mg":    tsfc * 1e6,
        "eta_th_pct": eta_th * 100,
        "eta_p_pct":  eta_p * 100,
        "eta_ov_pct": eta_th * eta_p * 100,
        "stations":   (T1, T2, T3, T4),
        "Ve": Ve,
    }



def ion_performance(mdot_mgs, Vb, mi_amu, power_kW, eta, dv, ms_kg):
    mdot_kg = mdot_mgs * 1e-6
    mi      = mi_amu * AMU
    ve      = np.sqrt(2.0 * Q_E * Vb / mi)
    thrust  = eta * mdot_kg * ve
    Isp     = ve / G0
    tp      = (thrust * 1000) / max(power_kW, 0.001)

    mass_ratio = np.exp(dv / (Isp * G0))
    mp_ion  = ms_kg * (mass_ratio - 1.0)
    mr_chem = np.exp(dv / (320.0 * G0))
    mp_chem = ms_kg * (mr_chem - 1.0)

    return {
        "thrust_mN":  thrust * 1000,
        "Isp":        Isp,
        "ve_kms":     ve / 1000,
        "tp":         tp,
        "mp_ion":     mp_ion,
        "mp_chem":    mp_chem,
        "savings_kg": max(0, mp_chem - mp_ion),
    }


class LabeledSlider(QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, label, min_val, max_val, default, steps, unit="", parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.steps   = steps
        self.unit    = unit

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(185)
        lbl.setFont(QFont("Courier New", 9))
        layout.addWidget(lbl)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(steps)
        self.slider.setValue(self._to_int(default))
        self.slider.valueChanged.connect(self._on_change)
        layout.addWidget(self.slider)

        self.readout = QLabel()
        self.readout.setFixedWidth(115)
        self.readout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.readout.setFont(QFont("Courier New", 9))
        layout.addWidget(self.readout)

        self._update_readout(default)

    def _to_int(self, val):
        ratio = (val - self.min_val) / (self.max_val - self.min_val)
        return int(round(ratio * self.steps))

    def _to_float(self, int_val):
        ratio = int_val / self.steps
        return self.min_val + ratio * (self.max_val - self.min_val)

    def _on_change(self, int_val):
        v = self._to_float(int_val)
        self._update_readout(v)
        self.valueChanged.emit(v)

    def _update_readout(self, v):
        if abs(v) >= 1000:
            text = f"{v:,.0f}"
        elif abs(v) >= 10:
            text = f"{v:.1f}"
        elif abs(v) >= 0.1:
            text = f"{v:.3f}"
        else:
            text = f"{v:.4f}"
        self.readout.setText(f"{text} {self.unit}")

    def value(self):
        return self._to_float(self.slider.value())


class MetricCard(QFrame):
    def __init__(self, title, unit="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame { border: 1px solid #cccccc; border-radius: 6px;
                     background: #f8f9fa; padding: 2px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(1)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Arial", 8))
        self.title_lbl.setStyleSheet("color: #666; border: none;")
        layout.addWidget(self.title_lbl)

        self.value_lbl = QLabel("—")
        self.value_lbl.setFont(QFont("Courier New", 15))
        self.value_lbl.setStyleSheet("color: #111; border: none;")
        layout.addWidget(self.value_lbl)

        self.unit_lbl = QLabel(unit)
        self.unit_lbl.setFont(QFont("Arial", 8))
        self.unit_lbl.setStyleSheet("color: #999; border: none;")
        layout.addWidget(self.unit_lbl)

    def set_value(self, v, decimals=1):
        self.value_lbl.setText(f"{v:.{decimals}f}" if isinstance(v, float) else str(v))


class RocketTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(12)

        left = QGroupBox("Engine Parameters")
        left.setFixedWidth(450)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(4)

        self.s_mdot  = LabeledSlider("Mass flow (kg/s)",       1,    500,   50,   200, "kg/s")
        self.s_tc    = LabeledSlider("Chamber temp (K)",        1000, 4000,  3200, 300, "K")
        self.s_pc    = LabeledSlider("Chamber press (MPa)",     1,    25,    7,    240, "MPa")
        self.s_ae    = LabeledSlider("Nozzle exit area (m²)",   0.05, 3.0,   0.5,  200, "m²")
        self.s_pa    = LabeledSlider("Ambient press (kPa)",     0,    101,   0,    101, "kPa")
        self.s_gamma = LabeledSlider("Gamma γ",                 1.10, 1.67,  1.20, 100, "")
        self.s_mw    = LabeledSlider("Mol. weight (g/mol)",     2,    32,    18,   150, "g/mol")
        self.s_m0    = LabeledSlider("Initial mass m₀ (kg)",    100,  50000, 5000, 200, "kg")
        self.s_mf    = LabeledSlider("Final (dry) mass mf (kg)",50,   10000, 2000, 200, "kg")

        for s in [self.s_mdot, self.s_tc, self.s_pc, self.s_ae, self.s_pa,
                  self.s_gamma, self.s_mw, self.s_m0, self.s_mf]:
            left_layout.addWidget(s)
            s.valueChanged.connect(lambda _: self.update())

        left_layout.addStretch()
        main_layout.addWidget(left)

        right = QVBoxLayout()

        cards_row = QHBoxLayout()
        self.c_thrust = MetricCard("Thrust",           "kN")
        self.c_isp    = MetricCard("Isp",              "s")
        self.c_ve     = MetricCard("Exit velocity",    "m/s")
        self.c_dv     = MetricCard("Δv (Tsiolkovsky)", "m/s")
        for c in [self.c_thrust, self.c_isp, self.c_ve, self.c_dv]:
            cards_row.addWidget(c)
        right.addLayout(cards_row)

        self.fig = Figure(figsize=(6, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.ax_thrust = self.fig.add_subplot(2, 2, 1)
        self.ax_isp    = self.fig.add_subplot(2, 2, 2)
        self.ax_dv     = self.fig.add_subplot(2, 1, 2)

        right.addWidget(self.canvas)
        main_layout.addLayout(right)

        self.update()

    def update(self):
        """Read all sliders → run physics → update cards and plots."""
        mdot  = self.s_mdot.value()
        Tc    = self.s_tc.value()
        Pc    = self.s_pc.value() * 1e6
        Ae    = self.s_ae.value()
        Pa    = self.s_pa.value() * 1e3
        gamma = self.s_gamma.value()
        MW    = self.s_mw.value()
        m0    = self.s_m0.value()
        mf    = self.s_mf.value()

        R_spec = R_UNIV / MW

        ve  = rocket_exhaust_velocity(gamma, R_spec, Tc, Pc, Pa)
        Pe  = rocket_exit_pressure(gamma, Pc, Ae / 0.1)
        F   = rocket_thrust(mdot, ve, Pe, Pa, Ae)
        Isp = ve / G0
        dv  = tsiolkovsky(Isp, m0, max(mf, 1))

        self.c_thrust.set_value(F / 1000, 1)
        self.c_isp.set_value(Isp, 0)
        self.c_ve.set_value(ve, 0)
        self.c_dv.set_value(dv, 0)

        mdots   = np.linspace(1, 500, 200)
        thrusts = [rocket_thrust(m, ve, Pe, Pa, Ae) / 1000 for m in mdots]
        self.ax_thrust.cla()
        self.ax_thrust.plot(mdots, thrusts, color="#2563eb", lw=2)
        self.ax_thrust.axvline(mdot, color="orange", ls="--", lw=1.5,
                               label=f"Now: {F/1000:.0f} kN")
        self.ax_thrust.set_xlabel("Mass flow (kg/s)", fontsize=8)
        self.ax_thrust.set_ylabel("Thrust (kN)", fontsize=8)
        self.ax_thrust.set_title("Thrust vs ṁ", fontsize=9)
        self.ax_thrust.legend(fontsize=7)
        self.ax_thrust.tick_params(labelsize=7)
        self.ax_thrust.grid(True, alpha=0.3)

        gammas = np.linspace(1.10, 1.67, 200)
        isps   = [rocket_exhaust_velocity(g, R_spec, Tc, Pc, Pa) / G0 for g in gammas]
        self.ax_isp.cla()
        self.ax_isp.plot(gammas, isps, color="#16a34a", lw=2)
        self.ax_isp.axvline(gamma, color="orange", ls="--", lw=1.5,
                            label=f"γ={gamma:.2f}  →  {Isp:.0f}s")
        self.ax_isp.set_xlabel("Gamma γ", fontsize=8)
        self.ax_isp.set_ylabel("Isp (s)", fontsize=8)
        self.ax_isp.set_title("Isp vs γ", fontsize=9)
        self.ax_isp.legend(fontsize=7)
        self.ax_isp.tick_params(labelsize=7)
        self.ax_isp.grid(True, alpha=0.3)

        ratios = np.linspace(1.01, 20, 300)
        dvs    = [Isp * G0 * np.log(r) / 1000 for r in ratios]
        curr_r = m0 / max(mf, 1)
        self.ax_dv.cla()
        self.ax_dv.plot(ratios, dvs, color="#dc2626", lw=2)
        self.ax_dv.axvline(curr_r, color="orange", ls="--", lw=1.5,
                           label=f"m₀/mf={curr_r:.1f}  →  Δv={dv/1000:.2f} km/s")
        self.ax_dv.set_xlabel("Mass ratio  m₀ / mf", fontsize=8)
        self.ax_dv.set_ylabel("Δv (km/s)", fontsize=8)
        self.ax_dv.set_title("Tsiolkovsky: Δv vs mass ratio", fontsize=9)
        self.ax_dv.legend(fontsize=7)
        self.ax_dv.tick_params(labelsize=7)
        self.ax_dv.grid(True, alpha=0.3)

        self.canvas.draw()

class JetTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(12)

        left = QGroupBox("Engine Parameters")
        left.setFixedWidth(450)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(4)

        self.s_v0   = LabeledSlider("Freestream vel (m/s)",   50,   700,  250,  200, "m/s")
        self.s_mdot = LabeledSlider("Air mass flow (kg/s)",   10,   800,  200,  200, "kg/s")
        self.s_far  = LabeledSlider("Fuel-to-air ratio",      0.005,0.07, 0.025,200, "")
        self.s_pr   = LabeledSlider("Pressure ratio",         2,    60,   30,   200, "")
        self.s_tit  = LabeledSlider("Turbine inlet temp (K)", 1000, 2200, 1650, 200, "K")
        self.s_ec   = LabeledSlider("Compressor efficiency",  0.60, 0.98, 0.88, 200, "")
        self.s_et   = LabeledSlider("Turbine efficiency",     0.60, 0.98, 0.90, 200, "")

        for s in [self.s_v0, self.s_mdot, self.s_far, self.s_pr,
                  self.s_tit, self.s_ec, self.s_et]:
            left_layout.addWidget(s)
            s.valueChanged.connect(lambda _: self.update())

        left_layout.addStretch()
        main_layout.addWidget(left)

        right = QVBoxLayout()

        cards_row = QHBoxLayout()
        self.c_thrust  = MetricCard("Net thrust",       "kN")
        self.c_tsfc    = MetricCard("TSFC",             "mg/N·s")
        self.c_eta_th  = MetricCard("Thermal eff.",     "%")
        self.c_eta_p   = MetricCard("Propulsive eff.",  "%")
        self.c_eta_ov  = MetricCard("Overall eff.",     "%")
        for c in [self.c_thrust, self.c_tsfc, self.c_eta_th, self.c_eta_p, self.c_eta_ov]:
            cards_row.addWidget(c)
        right.addLayout(cards_row)

        self.fig = Figure(figsize=(6, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.ax_bars = self.fig.add_subplot(2, 2, 1)
        self.ax_pr   = self.fig.add_subplot(2, 2, 2)
        self.ax_mach = self.fig.add_subplot(2, 1, 2)

        right.addWidget(self.canvas)
        main_layout.addLayout(right)
        self.update()

    def update(self):
        V0   = self.s_v0.value()
        mdot = self.s_mdot.value()
        far  = self.s_far.value()
        PR   = self.s_pr.value()
        TIT  = self.s_tit.value()
        ec   = self.s_ec.value()
        et   = self.s_et.value()

        res = jet_performance(V0, mdot, far, PR, TIT, ec, et)

        self.c_thrust.set_value(res["thrust_kN"], 1)
        self.c_tsfc.set_value(res["tsfc_mg"], 2)
        self.c_eta_th.set_value(res["eta_th_pct"], 1)
        self.c_eta_p.set_value(res["eta_p_pct"], 1)
        self.c_eta_ov.set_value(res["eta_ov_pct"], 1)

        T1, T2, T3, T4 = res["stations"]
        names  = ["1  Inlet", "2  Post-comp", "3  Turbine in", "4  Exhaust"]
        temps  = [T1, T2, T3, T4]
        bcolors = ["#93c5fd", "#fbbf24", "#ef4444", "#fb923c"]

        self.ax_bars.cla()
        bars = self.ax_bars.bar(names, temps, color=bcolors, width=0.5, edgecolor="white")
        for bar, t in zip(bars, temps):
            self.ax_bars.text(bar.get_x() + bar.get_width() / 2,
                              bar.get_height() + 15, f"{t:.0f}K",
                              ha="center", va="bottom", fontsize=7)
        self.ax_bars.set_ylabel("Temperature (K)", fontsize=8)
        self.ax_bars.set_title("Brayton cycle stations", fontsize=9)
        self.ax_bars.tick_params(labelsize=7)
        self.ax_bars.grid(True, axis="y", alpha=0.3)

        prs     = np.linspace(2, 60, 200)
        thrusts = [jet_performance(V0, mdot, far, p, TIT, ec, et)["thrust_kN"] for p in prs]
        self.ax_pr.cla()
        self.ax_pr.plot(prs, thrusts, color="#7c3aed", lw=2)
        self.ax_pr.axvline(PR, color="orange", ls="--", lw=1.5, label=f"PR={PR:.0f}")
        self.ax_pr.set_xlabel("Pressure ratio", fontsize=8)
        self.ax_pr.set_ylabel("Thrust (kN)", fontsize=8)
        self.ax_pr.set_title("Thrust vs PR", fontsize=9)
        self.ax_pr.legend(fontsize=7)
        self.ax_pr.tick_params(labelsize=7)
        self.ax_pr.grid(True, alpha=0.3)

        machs  = np.linspace(0.1, 3.0, 300)
        eta_ps = [jet_performance(m * 340, mdot, far, PR, TIT, ec, et)["eta_p_pct"]
                  for m in machs]
        self.ax_mach.cla()
        self.ax_mach.plot(machs, eta_ps, color="#0891b2", lw=2)
        self.ax_mach.axvline(V0 / 340, color="orange", ls="--", lw=1.5,
                             label=f"M={V0/340:.2f}  η_p={res['eta_p_pct']:.1f}%")
        self.ax_mach.set_xlabel("Mach number", fontsize=8)
        self.ax_mach.set_ylabel("Propulsive efficiency (%)", fontsize=8)
        self.ax_mach.set_title("Propulsive efficiency vs Mach", fontsize=9)
        self.ax_mach.legend(fontsize=7)
        self.ax_mach.tick_params(labelsize=7)
        self.ax_mach.grid(True, alpha=0.3)

        self.canvas.draw()


class IonTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(12)

        left = QGroupBox("Thruster Parameters")
        left.setFixedWidth(450)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(4)

        self.s_mdot = LabeledSlider("Mass flow (mg/s)",        0.1,  20,    2.0,  200, "mg/s")
        self.s_vb   = LabeledSlider("Beam voltage (V)",        200,  10000, 1500, 200, "V")
        self.s_mi   = LabeledSlider("Ion mass (amu)",          1,    200,   131,  200, "amu")
        self.s_pw   = LabeledSlider("Power (kW)",              0.1,  50,    3.0,  200, "kW")
        self.s_eff  = LabeledSlider("Thrust efficiency",       0.20, 0.90,  0.65, 200, "")
        self.s_dv   = LabeledSlider("Δv target (m/s)",        100,  20000, 3000, 200, "m/s")
        self.s_ms   = LabeledSlider("Spacecraft dry mass (kg)",10,   5000,  500,  200, "kg")

        for s in [self.s_mdot, self.s_vb, self.s_mi, self.s_pw,
                  self.s_eff, self.s_dv, self.s_ms]:
            left_layout.addWidget(s)
            s.valueChanged.connect(lambda _: self.update())

        left_layout.addStretch()
        main_layout.addWidget(left)

        right = QVBoxLayout()

        cards_row = QHBoxLayout()
        self.c_thrust = MetricCard("Thrust",          "mN")
        self.c_isp    = MetricCard("Isp",             "s")
        self.c_ve     = MetricCard("Exhaust vel.",    "km/s")
        self.c_tp     = MetricCard("T/P ratio",       "mN/kW")
        self.c_mp     = MetricCard("Propellant req.", "kg")
        self.c_save   = MetricCard("Saved vs chem.", "kg")
        for c in [self.c_thrust, self.c_isp, self.c_ve, self.c_tp, self.c_mp, self.c_save]:
            cards_row.addWidget(c)
        right.addLayout(cards_row)

        self.fig = Figure(figsize=(6, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.ax_isp_v = self.fig.add_subplot(2, 2, 1)
        self.ax_prop  = self.fig.add_subplot(2, 2, 2)
        self.ax_dv    = self.fig.add_subplot(2, 1, 2)

        right.addWidget(self.canvas)
        main_layout.addLayout(right)
        self.update()

    def update(self):
        mdot = self.s_mdot.value()
        Vb   = self.s_vb.value()
        mi   = self.s_mi.value()
        pw   = self.s_pw.value()
        eff  = self.s_eff.value()
        dv   = self.s_dv.value()
        ms   = self.s_ms.value()

        res = ion_performance(mdot, Vb, mi, pw, eff, dv, ms)

        self.c_thrust.set_value(res["thrust_mN"], 2)
        self.c_isp.set_value(res["Isp"], 0)
        self.c_ve.set_value(res["ve_kms"], 2)
        self.c_tp.set_value(res["tp"], 1)
        self.c_mp.set_value(res["mp_ion"], 1)
        self.c_save.set_value(res["savings_kg"], 1)

        vbs  = np.linspace(200, 10000, 200)
        isps = [ion_performance(mdot, v, mi, pw, eff, dv, ms)["Isp"] for v in vbs]
        self.ax_isp_v.cla()
        self.ax_isp_v.plot(vbs, isps, color="#7c3aed", lw=2)
        self.ax_isp_v.axvline(Vb, color="orange", ls="--", lw=1.5,
                              label=f"Vb={Vb:.0f}V → {res['Isp']:.0f}s")
        self.ax_isp_v.set_xlabel("Beam voltage (V)", fontsize=8)
        self.ax_isp_v.set_ylabel("Isp (s)", fontsize=8)
        self.ax_isp_v.set_title("Isp vs beam voltage", fontsize=9)
        self.ax_isp_v.legend(fontsize=7)
        self.ax_isp_v.tick_params(labelsize=7)
        self.ax_isp_v.grid(True, alpha=0.3)

        self.ax_prop.cla()
        labels  = ["Ion\n(this config)", "Chemical\n(Isp=320s)"]
        vals    = [res["mp_ion"], res["mp_chem"]]
        bcolors = ["#16a34a", "#dc2626"]
        bars = self.ax_prop.bar(labels, vals, color=bcolors, width=0.45, edgecolor="white")
        for bar, v in zip(bars, vals):
            self.ax_prop.text(bar.get_x() + bar.get_width() / 2,
                              bar.get_height() + 0.5, f"{v:.1f} kg",
                              ha="center", va="bottom", fontsize=8)
        self.ax_prop.set_ylabel("Propellant mass (kg)", fontsize=8)
        self.ax_prop.set_title("Propellant: ion vs chemical", fontsize=9)
        self.ax_prop.tick_params(labelsize=8)
        self.ax_prop.grid(True, axis="y", alpha=0.3)

        isps_sw = np.linspace(100, 10000, 300)
        dvs_ion = [i * G0 * np.log((ms + res["mp_ion"]) / ms) / 1000 for i in isps_sw]
        self.ax_dv.cla()
        self.ax_dv.plot(isps_sw, dvs_ion, color="#7c3aed", lw=2, label="Fixed mp, varying Isp")
        self.ax_dv.axhline(dv / 1000, color="orange", ls="--", lw=1.5,
                           label=f"Target = {dv/1000:.1f} km/s")
        self.ax_dv.axvline(res["Isp"], color="#7c3aed", ls=":", lw=1.2,
                           label=f"Current Isp = {res['Isp']:.0f}s")
        self.ax_dv.set_xlabel("Isp (s)", fontsize=8)
        self.ax_dv.set_ylabel("Achievable Δv (km/s)", fontsize=8)
        self.ax_dv.set_title("Δv capability vs Isp (Tsiolkovsky)", fontsize=9)
        self.ax_dv.legend(fontsize=7)
        self.ax_dv.tick_params(labelsize=7)
        self.ax_dv.grid(True, alpha=0.3)

        self.canvas.draw()

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget
from PyQt6.QtGui import QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Propulsion Engineering Simulator")
        self.resize(1250, 740)

        self.tabs = QTabWidget() 
        self.tabs.setFont(QFont("Arial", 10))

        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #ccc; 
                top: -1px; 
                background: white; 
            }
            QTabBar::tab { 
                background: #f0f0f0; 
                color: #333; 
                padding: 10px 20px; 
                border: 1px solid #ccc; 
                border-bottom-color: #ccc; 
                border-top-left-radius: 5px; 
                border-top-right-radius: 5px; 
            }
            QTabBar::tab:selected { 
                background: white; 
                border-bottom-color: white; 
                font-weight: bold; 
            }
            QTabBar::tab:hover { 
                background: #e0e0e0; 
            }
        """)

        self.tabs.addTab(RocketTab(), "Rocket Engine")
        self.tabs.addTab(JetTab(), "Jet Engine")
        self.tabs.addTab(IonTab(), "Ion Thruster")

        self.setCentralWidget(self.tabs)

        self.setStyleSheet("QMainWindow { background-color: #F5F5F5; }")
        
        self.statusBar().showMessage(
            "Move any slider to update calculations and plots in real time."
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())