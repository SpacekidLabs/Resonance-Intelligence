"""
Experiment 17 - Causal Coupling vs Common Excitation

Test whether modal "coupling" is actually just shared excitation from the same
impact. We measure lagged correlations between modal band-energy traces and the
excitation envelope:

    corr(A_i(t), A_j(t + lag))
    corr(A_i(t), excitation(t + lag))

If the peaks sit near zero lag, the simplest explanation is a common strike
driving all modes together.
"""

from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from persistence.detectors import analyze_frames, normalize
from persistence.trackers import band_energy_trace


SAMPLE_RATE = 44_100
DURATION_SECONDS = 6.0
WINDOW_SIZE = 1024
HOP_SIZE = 64
LAG_MS = np.arange(-20.0, 20.01, 0.5)

MODES = [
    {"name": "mode 1", "frequency": 221.0, "amplitude": 1.00, "decay": 4.8},
    {"name": "mode 2", "frequency": 357.0, "amplitude": 0.70, "decay": 2.7},
    {"name": "mode 3", "frequency": 593.0, "amplitude": 0.50, "decay": 1.35},
    {"name": "mode 4", "frequency": 941.0, "amplitude": 0.36, "decay": 0.78},
]

PALETTE = {
    "mode 1": "#2364aa",
    "mode 2": "#d95d39",
    "mode 3": "#2a9d8f",
    "mode 4": "#6d597a",
}


def strike_envelope(times: np.ndarray) -> np.ndarray:
    """A short impact envelope used as the shared excitation proxy."""
    envelope = np.zeros_like(times)
    burst_samples = int(0.028 * SAMPLE_RATE)
    burst = np.hanning(burst_samples)
    envelope[:burst_samples] = burst
    envelope += 0.25 * np.exp(-times / 0.018)
    return normalize(envelope)


def generate_common_excitation_resonator() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    times = np.arange(int(SAMPLE_RATE * DURATION_SECONDS)) / SAMPLE_RATE
    rng = np.random.default_rng(71)
    excitation = strike_envelope(times)

    signal = np.zeros_like(times)
    for mode in MODES:
        phase = rng.uniform(0, 2 * np.pi)
        mode_envelope = excitation * np.exp(-times / mode["decay"])
        signal += mode["amplitude"] * mode_envelope * np.sin(
            2 * np.pi * mode["frequency"] * times + phase
        )

    # Keep the strike broadband, but only as a weak shared contact texture.
    signal += 0.03 * excitation * rng.normal(0, 1, size=times.shape)
    return times, normalize(signal), excitation


def lagged_pearson(
    x: np.ndarray,
    y: np.ndarray,
    times: np.ndarray,
    lag_ms: float,
) -> float:
    shifted = np.interp(times + lag_ms / 1000.0, times, y, left=np.nan, right=np.nan)
    mask = np.isfinite(x) & np.isfinite(shifted)
    if np.count_nonzero(mask) < 5:
        return float("nan")

    x_slice = x[mask]
    y_slice = shifted[mask]
    if np.std(x_slice) == 0 or np.std(y_slice) == 0:
        return float("nan")
    return float(np.corrcoef(x_slice, y_slice)[0, 1])


def lag_curve(x: np.ndarray, y: np.ndarray, times: np.ndarray) -> np.ndarray:
    return np.array([lagged_pearson(x, y, times, lag) for lag in LAG_MS])


def peak_lag(lag_ms: np.ndarray, correlation: np.ndarray) -> tuple[float, float]:
    valid = np.isfinite(correlation)
    if not np.any(valid):
        return float("nan"), float("nan")
    index = int(np.nanargmax(correlation))
    return float(lag_ms[index]), float(correlation[index])


def main() -> None:
    parser = argparse.ArgumentParser(description="Test common excitation vs causal coupling.")
    parser.add_argument("--save", help="Save plot instead of opening a window.")
    args = parser.parse_args()

    if args.save:
        import matplotlib

        matplotlib.use("Agg")

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Install dependencies with: pip install -r requirements.txt") from exc

    times, signal, excitation = generate_common_excitation_resonator()
    frames = analyze_frames(signal, SAMPLE_RATE, WINDOW_SIZE, HOP_SIZE)

    mode_traces = {
        mode["name"]: band_energy_trace(frames, mode["frequency"], 45)
        for mode in MODES
    }
    excitation_trace = np.interp(frames.frame_times, times, excitation)

    pair_curves = {
        (left["name"], right["name"]): lag_curve(
            mode_traces[left["name"]],
            mode_traces[right["name"]],
            frames.frame_times,
        )
        for left, right in combinations(MODES, 2)
    }
    excitation_curves = {
        mode["name"]: lag_curve(mode_traces[mode["name"]], excitation_trace, frames.frame_times)
        for mode in MODES
    }

    print("Causal coupling vs common excitation")
    print("mode pair                     peak_lag_ms  corr_at_peak")
    pair_peaks = []
    for (left, right), curve in pair_curves.items():
        peak_lag_ms, peak_corr = peak_lag(LAG_MS, curve)
        pair_peaks.append(peak_lag_ms)
        print(f"{left:8s} <-> {right:8s} {peak_lag_ms:11.2f}  {peak_corr:12.3f}")

    print("excitation comparison          peak_lag_ms  corr_at_peak")
    excitation_peaks = []
    for mode_name, curve in excitation_curves.items():
        peak_lag_ms, peak_corr = peak_lag(LAG_MS, curve)
        excitation_peaks.append(peak_lag_ms)
        print(f"{mode_name:8s} -> excitation {peak_lag_ms:11.2f}  {peak_corr:12.3f}")

    print()
    print(
        "Interpretation: if the strongest peaks cluster near 0 ms for both the "
        "mode pairs and the excitation comparison, the simplest explanation is a "
        "shared impact drive rather than direct mode-to-mode energy transfer."
    )
    print(
        f"Mean absolute pair peak lag: {np.nanmean(np.abs(pair_peaks)):.2f} ms; "
        f"mean absolute excitation peak lag: {np.nanmean(np.abs(excitation_peaks)):.2f} ms"
    )

    figure = plt.figure(figsize=(14, 10), constrained_layout=True)
    grid = figure.add_gridspec(2, 2, height_ratios=[1.0, 1.15], hspace=0.25, wspace=0.2)
    ax_signal = figure.add_subplot(grid[0, 0])
    ax_modes = figure.add_subplot(grid[0, 1])
    ax_pairs = figure.add_subplot(grid[1, 0])
    ax_excitation = figure.add_subplot(grid[1, 1])
    figure.suptitle("Experiment 17 - Causal Coupling vs Common Excitation", fontweight="bold")

    ax_signal.plot(times, signal, color="#243b53", linewidth=0.75, label="signal")
    ax_signal.set_xlim(0, 0.20)
    ax_signal.set_ylabel("signal")
    ax_signal.set_xlabel("time (seconds)")
    ax_signal.set_title("Struck resonator output, first 200 ms")
    ax_signal.grid(True, alpha=0.2)

    ax_signal_excitation = ax_signal.twinx()
    ax_signal_excitation.plot(
        times,
        excitation,
        color="#d95d39",
        linewidth=1.5,
        alpha=0.9,
        label="excitation",
    )
    ax_signal_excitation.set_ylabel("excitation", color="#d95d39")
    ax_signal_excitation.tick_params(axis="y", colors="#d95d39")
    ax_signal.legend(loc="upper right")

    for mode in MODES:
        ax_modes.plot(
            frames.frame_times,
            mode_traces[mode["name"]],
            label=f"{mode['name']} {mode['frequency']:.0f} Hz",
            color=PALETTE[mode["name"]],
            linewidth=1.8,
        )
    ax_modes.set_xlim(0, DURATION_SECONDS)
    ax_modes.set_ylim(-0.02, 1.05)
    ax_modes.set_title("Mode band-energy traces")
    ax_modes.set_xlabel("time (seconds)")
    ax_modes.set_ylabel("normalized energy")
    ax_modes.grid(True, alpha=0.2)
    ax_modes.legend(loc="upper right", ncol=2)

    for index, ((left, right), curve) in enumerate(pair_curves.items()):
        color = f"C{index}"
        peak_index = int(np.nanargmax(curve))
        ax_pairs.plot(LAG_MS, curve, color=color, linewidth=1.5, label=f"{left} vs {right}")
        ax_pairs.scatter(LAG_MS[peak_index], curve[peak_index], color=color, s=28)
    ax_pairs.axvline(0, color="#222222", linewidth=0.8, linestyle="--", alpha=0.7)
    ax_pairs.set_title("Pairwise lag correlation")
    ax_pairs.set_xlabel("lag (ms)")
    ax_pairs.set_ylabel("corr")
    ax_pairs.set_xlim(LAG_MS[0], LAG_MS[-1])
    ax_pairs.set_ylim(-1.0, 1.0)
    ax_pairs.grid(True, alpha=0.2)
    ax_pairs.legend(fontsize=8, ncol=2, loc="lower center")

    for mode in MODES:
        curve = excitation_curves[mode["name"]]
        peak_index = int(np.nanargmax(curve))
        ax_excitation.plot(
            LAG_MS,
            curve,
            color=PALETTE[mode["name"]],
            linewidth=1.8,
            label=mode["name"],
        )
        ax_excitation.scatter(LAG_MS[peak_index], curve[peak_index], color=PALETTE[mode["name"]], s=28)
    ax_excitation.axvline(0, color="#222222", linewidth=0.8, linestyle="--", alpha=0.7)
    ax_excitation.set_title("Mode vs excitation lag correlation")
    ax_excitation.set_xlabel("lag (ms)")
    ax_excitation.set_ylabel("corr")
    ax_excitation.set_xlim(LAG_MS[0], LAG_MS[-1])
    ax_excitation.set_ylim(-1.0, 1.0)
    ax_excitation.grid(True, alpha=0.2)
    ax_excitation.legend(loc="lower center", fontsize=8, ncol=2)

    if args.save:
        figure.savefig(args.save, dpi=160, bbox_inches="tight")
        print(f"Saved plot to {args.save}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
