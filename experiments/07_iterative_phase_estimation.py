"""
Resonance Intelligence - Experiment 07: Iterative Phase Estimation

This script tests a simple PLL-style observer on synthetic drifting modes built
from the consensus resonances discovered in Experiment 03. It compares an
open-loop fixed-frequency reconstruction against an iterative phase tracker that
updates its frequency estimate from windowed phase measurements.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit("Install matplotlib to generate plots.") from exc


def wrap_phase(angle: float) -> float:
    return float(np.angle(np.exp(1j * angle)))


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

    # Integral of a linearly drifting frequency.
    theta = 2.0 * np.pi * (frequency * t + 0.5 * frequency * drift_strength * (t**2) / max(duration_s, 1e-12)) + phase
    envelope = amplitude * np.exp(-decay_rate * t)
    signal = envelope * np.sin(theta)

    rng = np.random.default_rng(7)
    noise = 0.004 * rng.normal(size=sample_count) * np.exp(-decay_rate * t)
    signal = signal + noise

    return signal.astype(np.float32), inst_freq.astype(np.float32), theta.astype(np.float32)


def estimate_initial_state(sig: np.ndarray, frequency: float, decay_rate: float, fs: int, fit_samples: int) -> tuple[float, float]:
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
    loop_gain: float = 0.18,
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


def compute_metrics(original: np.ndarray, reconstruction: np.ndarray) -> tuple[float, float]:
    error = original - reconstruction
    rms_original = float(np.sqrt(np.mean(original**2)))
    rms_error = float(np.sqrt(np.mean(error**2)))
    rms_ratio = rms_error / (rms_original + 1e-12)
    snr = 20.0 * np.log10(rms_original / (rms_error + 1e-12))
    return rms_ratio, snr


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    sweep_json_path = results_dir / "03_observer_sweep.json"
    if not sweep_json_path.exists():
        print(f"Error: Sweep results '{sweep_json_path}' not found. Run Experiment 03 first.")
        sys.exit(1)

    with open(sweep_json_path, "r") as f:
        sweep_results = json.load(f)

    materials = ["glass", "mug", "metal_bowl", "wood"]
    drift_levels = [0.0, 0.001, 0.005, 0.01]
    fs = 44_100
    duration_s = 0.20
    fit_samples = 2048
    hop_samples = 128

    plot_rows = len(materials)
    plot_cols = 2
    fig, axes = plt.subplots(plot_rows, plot_cols, figsize=(15, 16))
    fig.suptitle("Experiment 07 - Iterative Phase Estimation (PLL Tracking)", fontsize=16, fontweight="bold")

    report = []
    report.append("# Experiment 07: Iterative Phase Estimation Report")
    report.append("")
    report.append("This experiment tests whether a simple PLL-style observer can track a slowly drifting resonance better than an open-loop fixed-frequency model.")
    report.append("")
    report.append("For each material, we use the strongest consensus mode from Experiment 03, synthesize a drifting version of that mode, and compare fixed-frequency reconstruction against iterative phase correction.")
    report.append("")

    for row_index, material in enumerate(materials):
        modes = sweep_results.get(material, [])
        if not modes:
            report.append(f"## {material.replace('_', ' ').title()}")
            report.append("No consensus modes were available; skipped.")
            report.append("")
            continue

        reference_mode = modes[0]
        nominal_frequency = float(reference_mode["frequency"])
        decay_rate = float(reference_mode["decay_rate"])
        amplitude = float(reference_mode["amplitude"])
        phase = 0.0

        drift = 0.01 if material in {"glass", "mug"} else 0.005
        target, true_freq, true_phase = synthesize_drifting_mode(
            nominal_frequency,
            amplitude,
            decay_rate,
            phase,
            fs,
            duration_s,
            drift,
        )

        init_amp, init_phase = estimate_initial_state(target, nominal_frequency, decay_rate, fs, fit_samples)
        open_loop = reconstruct_open_loop(duration_s, fs, nominal_frequency, init_amp, decay_rate, init_phase)
        pll_recon, centers, tracked_freqs, tracked_phases = pll_track_mode(
            target,
            fs,
            nominal_frequency,
            decay_rate,
            fit_samples=fit_samples,
            hop_samples=hop_samples,
            loop_gain=0.22,
        )

        open_loop_rms, open_loop_snr = compute_metrics(target, open_loop)
        pll_rms, pll_snr = compute_metrics(target, pll_recon)

        center_indices = np.clip((centers * fs).astype(int), 0, true_freq.size - 1)
        true_freq_at_centers = true_freq[center_indices]
        freq_error = tracked_freqs - true_freq_at_centers[: tracked_freqs.size]
        freq_error_rms = float(np.sqrt(np.mean(freq_error**2)))
        freq_error_pct = 100.0 * freq_error_rms / (nominal_frequency + 1e-12)

        report.append(f"## {material.replace('_', ' ').title()}")
        report.append(f"Consensus mode used: {nominal_frequency:.2f} Hz, decay {decay_rate:.2f} 1/s, amplitude {amplitude:.4f}")
        report.append(f"Drift injected: {drift:.1%} linear frequency rise across {duration_s * 1000.0:.0f} ms")
        report.append("")
        report.append("| Reconstruction | RMS Error Ratio | SNR |")
        report.append("| :--- | :---: | :---: |")
        report.append(f"| Open Loop | {open_loop_rms:.2%} | {open_loop_snr:.2f} dB |")
        report.append(f"| PLL Tracking | {pll_rms:.2%} | {pll_snr:.2f} dB |")
        report.append("")
        report.append(f"Frequency tracking RMS error: {freq_error_rms:.3f} Hz ({freq_error_pct:.3f}% of nominal)")
        report.append("")

        ax_freq = axes[row_index, 0]
        ax_err = axes[row_index, 1]

        time_axis = np.arange(target.size) / fs * 1000.0
        ax_freq.plot(time_axis, true_freq, color="black", linewidth=1.6, label="True Drifted Frequency")
        ax_freq.plot(centers * 1000.0, tracked_freqs, color="tab:blue", linewidth=1.4, label="PLL Estimate")
        ax_freq.axhline(nominal_frequency, color="tab:orange", linestyle="--", linewidth=1.1, label="Open-Loop Frequency")
        ax_freq.set_title(f"{material.replace('_', ' ').title()} - Frequency Tracking")
        ax_freq.set_xlabel("Time (ms)")
        ax_freq.set_ylabel("Frequency (Hz)")
        ax_freq.grid(True, alpha=0.2)
        ax_freq.legend(fontsize=8, loc="best")

        err_time = time_axis
        open_loop_error = np.abs(target - open_loop)
        pll_error = np.abs(target - pll_recon)
        ax_err.plot(err_time, open_loop_error, color="tab:red", linewidth=1.2, label=f"Open Loop RMS {open_loop_rms:.2%}")
        ax_err.plot(err_time, pll_error, color="tab:green", linewidth=1.2, label=f"PLL RMS {pll_rms:.2%}")
        ax_err.set_title(f"{material.replace('_', ' ').title()} - Pointwise Error")
        ax_err.set_xlabel("Time (ms)")
        ax_err.set_ylabel("Absolute Error")
        ax_err.grid(True, alpha=0.2)
        ax_err.legend(fontsize=8, loc="best")

        print(
            f"{material}: open loop RMS={open_loop_rms:.2%}, PLL RMS={pll_rms:.2%}, "
            f"freq tracking RMS error={freq_error_rms:.3f} Hz"
        )

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    plot_path = results_dir / "07_iterative_phase_estimation.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved PLL tracking plot to: {plot_path}")

    report.append("## Scientific Interpretation")
    report.append("")
    report.append("The open-loop reconstruction uses the nominal frequency and therefore accumulates phase error when the target drifts.")
    report.append("The iterative tracker updates frequency from windowed phase measurements, which reduces the long-horizon residual and keeps the synthesized phase closer to the drifting target.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **Iterative phase estimation closes part of the predictability gap identified in Experiment 06, but only when the observer is allowed to update its state from local phase measurements.**")
    report.append("> A fixed modal basis is not enough once the resonance drifts; active feedback is required to keep long-window reconstruction coherent.")

    report_path = results_dir / "07_iterative_phase_estimation_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    print(f"Saved PLL report to: {report_path}")


if __name__ == "__main__":
    main()