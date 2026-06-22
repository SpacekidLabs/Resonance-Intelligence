"""
Resonance Intelligence - Experiment 08: Frequency Precision Limit

This script sweeps frequency-estimation error levels for the dominant consensus
mode of each material and measures when prediction collapses. It compares two
reconstruction strategies:
1. Open loop fixed-frequency extrapolation.
2. Iterative PLL-style tracker that can correct phase drift over time.

Outputs:
- 08_frequency_precision_limit.json
- 08_frequency_precision_limit.png
- 08_frequency_precision_limit_report.md
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import scipy.signal as signal

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit("Install matplotlib to generate plots.") from exc


def wrap_phase(angle: np.ndarray | float) -> np.ndarray | float:
    return np.angle(np.exp(1j * angle))


def synthesize_drifting_mode(
    frequency: float,
    amplitude: float,
    decay_rate: float,
    phase: float,
    fs: int,
    duration_s: float,
    drift_strength: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create a single exponentially decaying mode with linear frequency drift."""
    sample_count = int(duration_s * fs)
    t = np.arange(sample_count) / fs
    drift_profile = 1.0 + drift_strength * (t / max(duration_s, 1e-12))
    inst_freq = frequency * drift_profile

    theta = 2.0 * np.pi * (frequency * t + 0.5 * frequency * drift_strength * (t**2) / max(duration_s, 1e-12)) + phase
    envelope = amplitude * np.exp(-decay_rate * t)
    signal_out = envelope * np.sin(theta)

    rng = np.random.default_rng(17)
    noise = 0.003 * rng.normal(size=sample_count) * np.exp(-decay_rate * t)
    signal_out = signal_out + noise

    return signal_out.astype(np.float32), inst_freq.astype(np.float32), theta.astype(np.float32)


def estimate_initial_state(
    sig: np.ndarray,
    frequency: float,
    decay_rate: float,
    fs: int,
    fit_samples: int,
) -> tuple[float, float]:
    """Estimate amplitude and phase against a fixed nominal frequency."""
    window = sig[:fit_samples]
    t = np.arange(window.size) / fs
    basis_sin = np.exp(-decay_rate * t) * np.sin(2.0 * np.pi * frequency * t)
    basis_cos = np.exp(-decay_rate * t) * np.cos(2.0 * np.pi * frequency * t)
    design = np.column_stack([basis_sin, basis_cos])
    coeffs, _, _, _ = np.linalg.lstsq(design, window, rcond=None)
    amplitude = float(np.hypot(coeffs[0], coeffs[1]))
    phase = float(np.arctan2(coeffs[1], coeffs[0]))
    return amplitude, phase


def reconstruct_open_loop(
    duration_s: float,
    fs: int,
    frequency: float,
    amplitude: float,
    decay_rate: float,
    phase: float,
) -> np.ndarray:
    t = np.arange(int(duration_s * fs)) / fs
    return amplitude * np.exp(-decay_rate * t) * np.sin(2.0 * np.pi * frequency * t + phase)


def pll_track_mode(
    sig: np.ndarray,
    fs: int,
    nominal_frequency: float,
    decay_rate: float,
    fit_samples: int = 2048,
    hop_samples: int = 128,
    loop_gain: float = 0.20,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Track a drifting mode by iteratively updating the frequency estimate."""
    window_samples = fit_samples
    sample_count = sig.size
    if sample_count < window_samples:
        raise ValueError("Signal is shorter than the PLL window.")

    reconstruction = np.zeros(sample_count, dtype=np.float64)
    weight = np.zeros(sample_count, dtype=np.float64)

    freq_est = float(nominal_frequency)
    previous_phase = None
    tracked_freqs = []
    tracked_phases = []
    tracked_centers = []

    hann = np.hanning(window_samples)

    for start in range(0, sample_count - window_samples + 1, hop_samples):
        stop = start + window_samples
        window = sig[start:stop]
        local_t = np.arange(window_samples) / fs

        basis_sin = np.exp(-decay_rate * local_t) * np.sin(2.0 * np.pi * freq_est * local_t)
        basis_cos = np.exp(-decay_rate * local_t) * np.cos(2.0 * np.pi * freq_est * local_t)
        design = np.column_stack([basis_sin, basis_cos])
        coeffs, _, _, _ = np.linalg.lstsq(design, window, rcond=None)

        amplitude = float(np.hypot(coeffs[0], coeffs[1]))
        phase = float(np.arctan2(coeffs[1], coeffs[0]))

        if previous_phase is not None:
            predicted_phase = previous_phase + 2.0 * np.pi * freq_est * (hop_samples / fs)
            phase_error = wrap_phase(phase - predicted_phase)
            freq_est = freq_est + loop_gain * phase_error * fs / (2.0 * np.pi * hop_samples)

        previous_phase = phase
        tracked_freqs.append(freq_est)
        tracked_phases.append(phase)
        tracked_centers.append((start + window_samples / 2.0) / fs)

        recon_window = amplitude * np.exp(-decay_rate * local_t) * np.sin(2.0 * np.pi * freq_est * local_t + phase)
        recon_window *= hann
        reconstruction[start:stop] += recon_window
        weight[start:stop] += hann

    valid = weight > 1e-12
    reconstruction[valid] /= weight[valid]
    reconstruction[~valid] = 0.0

    return (
        reconstruction.astype(np.float32),
        np.asarray(tracked_centers, dtype=np.float32),
        np.asarray(tracked_freqs, dtype=np.float32),
        np.asarray(tracked_phases, dtype=np.float32),
    )


def local_error_trace(
    original: np.ndarray,
    reconstruction: np.ndarray,
    fs: int,
    window_ms: float = 5.0,
    hop_ms: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    window_samples = max(8, int(window_ms * fs / 1000.0))
    hop_samples = max(1, int(hop_ms * fs / 1000.0))

    centers_ms = []
    local_rms_ratios = []
    original_rms = float(np.sqrt(np.mean(original**2)))

    for start in range(0, len(original) - window_samples + 1, hop_samples):
        stop = start + window_samples
        error = original[start:stop] - reconstruction[start:stop]
        rms_error = float(np.sqrt(np.mean(error**2)))
        local_rms_ratios.append(rms_error / (original_rms + 1e-12))
        centers_ms.append((start + window_samples / 2.0) / fs * 1000.0)

    return np.asarray(centers_ms, dtype=np.float32), np.asarray(local_rms_ratios, dtype=np.float32)


def prediction_horizon(centers_ms: np.ndarray, local_rms_ratios: np.ndarray, threshold: float = 1.0) -> float:
    """Return the first time at which local error reaches the collapse threshold."""
    above = np.where(local_rms_ratios >= threshold)[0]
    if len(above) == 0:
        return float(centers_ms[-1]) if len(centers_ms) else 0.0

    idx = int(above[0])
    if idx == 0:
        return float(centers_ms[0])

    x0 = float(centers_ms[idx - 1])
    x1 = float(centers_ms[idx])
    y0 = float(local_rms_ratios[idx - 1])
    y1 = float(local_rms_ratios[idx])

    if y1 == y0:
        return x1

    fraction = (threshold - y0) / (y1 - y0)
    fraction = float(np.clip(fraction, 0.0, 1.0))
    return x0 + fraction * (x1 - x0)


def compute_global_metrics(original: np.ndarray, reconstruction: np.ndarray) -> tuple[float, float]:
    error = original - reconstruction
    rms_original = float(np.sqrt(np.mean(original**2)))
    rms_error = float(np.sqrt(np.mean(error**2)))
    rms_ratio = rms_error / (rms_original + 1e-12)
    snr = 20.0 * np.log10(rms_original / (rms_error + 1e-12))
    return rms_ratio, snr


def phase_error_deg(original: np.ndarray, reconstruction: np.ndarray, max_samples: int | None = None) -> float:
    """Measure wrapped phase mismatch using analytic signals."""
    if max_samples is not None:
        original = original[:max_samples]
        reconstruction = reconstruction[:max_samples]

    if len(original) < 8:
        return 0.0

    phase_original = np.unwrap(np.angle(signal.hilbert(original)))
    phase_reconstruction = np.unwrap(np.angle(signal.hilbert(reconstruction)))
    delta = np.angle(np.exp(1j * (phase_original - phase_reconstruction)))
    return float(np.sqrt(np.mean(delta**2)) * 180.0 / np.pi)


def load_reference_modes() -> dict:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    sweep_json_path = results_dir / "03_observer_sweep.json"
    if not sweep_json_path.exists():
        raise FileNotFoundError(f"Sweep results '{sweep_json_path}' not found. Run Experiment 03 first.")

    with open(sweep_json_path, "r") as f:
        return json.load(f)


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    sweep_results = load_reference_modes()

    materials = ["glass", "mug", "metal_bowl", "wood"]
    perturbation_levels = [0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02]
    fs = 44_100
    duration_s = 0.25
    fit_samples = 2048
    hop_samples = 128
    drift_strength = 0.005
    collapse_threshold_ms = 50.0

    summary = {}

    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle("Experiment 08 - Prediction Horizon vs Frequency Error", fontsize=16, fontweight="bold")
    axes_flat = axes.flatten()

    report = []
    report.append("# Experiment 08: Frequency Precision Limit Report")
    report.append("")
    report.append("This experiment asks how much frequency-estimation error each resonant object can tolerate before waveform prediction collapses.")
    report.append("")
    report.append(f"Operational collapse definition: prediction horizon falls below **{collapse_threshold_ms:.0f} ms** or, equivalently, the local 5 ms RMS error ratio crosses **100%**.")
    report.append("")

    for axis_index, material in enumerate(materials):
        modes = sweep_results.get(material, [])
        if not modes:
            summary[material] = []
            continue

        reference_mode = modes[0]
        nominal_frequency = float(reference_mode["frequency"])
        decay_rate = float(reference_mode["decay_rate"])
        amplitude = float(reference_mode["amplitude"])

        target, true_freq, true_phase = synthesize_drifting_mode(
            nominal_frequency,
            amplitude,
            decay_rate,
            phase=0.0,
            fs=fs,
            duration_s=duration_s,
            drift_strength=drift_strength,
        )

        material_rows = []
        open_loop_horizons = []
        tracker_horizons = []

        for perturbation in perturbation_levels:
            perturbed_frequency = nominal_frequency * (1.0 + perturbation)

            init_amp, init_phase = estimate_initial_state(target, perturbed_frequency, decay_rate, fs, fit_samples)
            open_loop = reconstruct_open_loop(duration_s, fs, perturbed_frequency, init_amp, decay_rate, init_phase)
            tracker, _, _, _ = pll_track_mode(
                target,
                fs,
                perturbed_frequency,
                decay_rate,
                fit_samples=fit_samples,
                hop_samples=hop_samples,
                loop_gain=0.20,
            )

            open_centers_ms, open_local_rms = local_error_trace(target, open_loop, fs)
            tracker_centers_ms, tracker_local_rms = local_error_trace(target, tracker, fs)

            open_horizon = prediction_horizon(open_centers_ms, open_local_rms, threshold=1.0)
            tracker_horizon = prediction_horizon(tracker_centers_ms, tracker_local_rms, threshold=1.0)

            open_rms, open_snr = compute_global_metrics(target, open_loop)
            tracker_rms, tracker_snr = compute_global_metrics(target, tracker)

            open_phase_error = phase_error_deg(target, open_loop, max_samples=int(open_horizon * fs / 1000.0) if open_horizon > 0 else None)
            tracker_phase_error = phase_error_deg(target, tracker, max_samples=int(tracker_horizon * fs / 1000.0) if tracker_horizon > 0 else None)

            material_rows.append(
                {
                    "frequency_error": perturbation,
                    "frequency_error_percent": perturbation * 100.0,
                    "open_loop": {
                        "prediction_horizon_ms": open_horizon,
                        "rms_error_ratio": open_rms,
                        "snr_db": open_snr,
                        "phase_error_deg": open_phase_error,
                    },
                    "iterative_tracker": {
                        "prediction_horizon_ms": tracker_horizon,
                        "rms_error_ratio": tracker_rms,
                        "snr_db": tracker_snr,
                        "phase_error_deg": tracker_phase_error,
                    },
                }
            )

            open_loop_horizons.append(open_horizon)
            tracker_horizons.append(tracker_horizon)

        summary[material] = material_rows

        ax = axes_flat[axis_index]
        x_values = [row["frequency_error_percent"] for row in material_rows]
        ax.plot(x_values, open_loop_horizons, marker="o", linewidth=1.8, color="tab:red", label="Open Loop")
        ax.plot(x_values, tracker_horizons, marker="o", linewidth=1.8, color="tab:blue", label="Iterative Tracker")
        ax.axhline(collapse_threshold_ms, color="gray", linestyle="--", linewidth=1.0, alpha=0.7)
        ax.set_title(f"{material.replace('_', ' ').title()}")
        ax.set_xlabel("Frequency Estimation Error (%)")
        ax.set_ylabel("Prediction Horizon (ms)")
        ax.set_xlim(min(x_values) * 0.8, max(x_values) * 1.05)
        ax.set_ylim(0.0, duration_s * 1000.0 + 5.0)
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=8, loc="best")

        def collapse_point(rows: list[dict], method_key: str) -> float | None:
            for row in rows:
                if row[method_key]["prediction_horizon_ms"] <= collapse_threshold_ms:
                    return float(row["frequency_error_percent"])
            return None

        open_collapse = collapse_point(material_rows, "open_loop")
        tracker_collapse = collapse_point(material_rows, "iterative_tracker")

        report.append(f"## {material.replace('_', ' ').title()}")
        report.append(f"Dominant consensus mode: {nominal_frequency:.2f} Hz, decay {decay_rate:.2f} 1/s, amplitude {amplitude:.4f}")
        report.append(f"Injected baseline drift: {drift_strength:.2%} over {duration_s * 1000.0:.0f} ms")
        report.append("")
        report.append("| Frequency Error | Open Loop Horizon | Open Loop RMS | Open Loop SNR | Open Loop Phase Error | Tracker Horizon | Tracker RMS | Tracker SNR | Tracker Phase Error |")
        report.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for row in material_rows:
            report.append(
                f"| {row['frequency_error_percent']:.2f}% | {row['open_loop']['prediction_horizon_ms']:.2f} ms | {row['open_loop']['rms_error_ratio']:.2%} | {row['open_loop']['snr_db']:.2f} dB | {row['open_loop']['phase_error_deg']:.2f}° | "
                f"{row['iterative_tracker']['prediction_horizon_ms']:.2f} ms | {row['iterative_tracker']['rms_error_ratio']:.2%} | {row['iterative_tracker']['snr_db']:.2f} dB | {row['iterative_tracker']['phase_error_deg']:.2f}° |"
            )
        report.append("")

        if open_collapse is None:
            report.append(f"Open loop collapse threshold: not reached within the sweep; horizon remained above {collapse_threshold_ms:.0f} ms.")
        else:
            report.append(f"Open loop collapse threshold: approximately {open_collapse:.2f}% frequency error.")

        if tracker_collapse is None:
            report.append(f"Iterative tracker collapse threshold: not reached within the sweep; horizon remained above {collapse_threshold_ms:.0f} ms.")
        else:
            report.append(f"Iterative tracker collapse threshold: approximately {tracker_collapse:.2f}% frequency error.")

        report.append("")

        print(
            f"{material}: open loop collapse={open_collapse if open_collapse is not None else 'not reached'}, "
            f"tracker collapse={tracker_collapse if tracker_collapse is not None else 'not reached'}"
        )

    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    plot_path = results_dir / "08_frequency_precision_limit.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved prediction horizon plot to: {plot_path}")

    report.append("## Scientific Interpretation")
    report.append("")
    report.append("The prediction horizon shrinks as frequency estimation error grows because phase drift accumulates faster than the envelope decays.")
    report.append("The iterative tracker extends the horizon when the frequency error is still inside its capture range, but it cannot fully erase large initial misspecifications once the local phase error becomes too large.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **The frequency precision limit is object-dependent: the higher the resonance sensitivity to phase accumulation and envelope mismatch, the sooner the prediction horizon collapses.**")
    report.append("> Use the tracker for moderate errors; use tighter parameter estimation or richer models once the sweep shows horizon collapse inside the early transient window.")

    report_path = results_dir / "08_frequency_precision_limit_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    json_path = results_dir / "08_frequency_precision_limit.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved sweep data to: {json_path}")
    print(f"Saved report to: {report_path}")


if __name__ == "__main__":
    main()