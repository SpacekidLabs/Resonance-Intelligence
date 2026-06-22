"""
Resonance Intelligence - Experiment 11: Dynamic Modal Resynthesis

This script uses the time-varying modal trajectories measured in Experiment 10A
to resynthesize the first 100 ms of each impact sound. It compares a static modal
model against a dynamic modal model with time-varying frequency, decay, and
amplitude trajectories.

Outputs:
- 11_dynamic_modal_resynthesis.png
- 11_dynamic_modal_resynthesis.json
- 11_dynamic_modal_resynthesis_report.md
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from resonance.extraction import detect_onset
try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit("Install matplotlib to generate plots.") from exc


def synthesize_material_impact(material: str, duration: float, fs: int = 44_100) -> np.ndarray:
    """Deterministically synthesize the reference impact sounds used throughout the lab."""
    t = np.arange(int(duration * fs)) / fs
    sig = np.zeros_like(t)
    rng = np.random.default_rng(123)

    if material == "glass":
        freqs = [1560.0, 2240.0, 3110.0, 4480.0]
        amps = [1.0, 0.6, 0.35, 0.15]
        decays = [7.0, 10.0, 14.0, 22.0]
    elif material == "mug":
        freqs = [820.0, 1340.0, 2080.0, 2920.0]
        amps = [0.9, 0.65, 0.4, 0.2]
        decays = [14.0, 20.0, 28.0, 40.0]
    elif material == "metal_bowl":
        freqs = [440.0, 650.0, 940.0, 1370.0]
        amps = [1.0, 0.8, 0.55, 0.3]
        decays = [1.5, 2.8, 4.2, 6.5]
    elif material == "wood":
        freqs = [180.0, 380.0, 620.0, 940.0]
        amps = [1.0, 0.45, 0.25, 0.08]
        decays = [48.0, 65.0, 85.0, 115.0]
    else:
        raise ValueError(f"Unknown material: {material}")

    for frequency, amplitude, decay_rate in zip(freqs, amps, decays):
        phase = rng.uniform(0.0, 2.0 * np.pi)
        sig += amplitude * np.exp(-decay_rate * t) * np.sin(2.0 * np.pi * frequency * t + phase)

    burst_len = int(0.005 * fs)
    hann_win = np.hanning(burst_len * 2)[burst_len:]
    noise = rng.normal(0.0, 0.1, burst_len) * hann_win
    sig[:burst_len] += noise

    max_val = np.max(np.abs(sig))
    if max_val > 0:
        sig = sig / max_val * 0.9

    return sig.astype(np.float32)


def load_material_signal(material: str, duration_s: float = 2.5) -> tuple[int, np.ndarray]:
    wav_path = PROJECT_ROOT / "experiments" / "test_sounds" / f"{material}.wav"
    if not wav_path.exists():
        test_sounds_dir = PROJECT_ROOT / "experiments" / "test_sounds"
        test_sounds_dir.mkdir(parents=True, exist_ok=True)
        synthesized = synthesize_material_impact(material, duration_s)
        wavfile.write(wav_path, 44_100, (np.clip(synthesized, -1.0, 1.0) * 32767).astype(np.int16))

    fs, sig_int = wavfile.read(wav_path)
    sig = sig_int.astype(np.float32) / 32767.0
    if sig.ndim > 1:
        sig = np.mean(sig, axis=1)
    return fs, sig


def load_time_varying_tracks() -> dict:
    path = PROJECT_ROOT / "experiments" / "results" / "10a_time_varying_mode_analysis.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing 10A results: {path}. Run Experiment 10A first.")

    with open(path, "r") as f:
        return json.load(f)


def load_consensus_modes() -> dict:
    path = PROJECT_ROOT / "experiments" / "results" / "03_observer_sweep.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing observer sweep results: {path}. Run Experiment 03 first.")

    with open(path, "r") as f:
        return json.load(f)


def interp(values_t_ms: list[float], values: list[float], query_ms: np.ndarray) -> np.ndarray:
    if len(values) == 0:
        return np.zeros_like(query_ms)
    if len(values) == 1:
        return np.full_like(query_ms, float(values[0]), dtype=float)
    return np.interp(query_ms, np.asarray(values_t_ms, dtype=float), np.asarray(values, dtype=float))


def build_static_design(
    freqs: list[float],
    decays: list[float],
    fs: int,
    duration_ms: float = 100.0,
) -> np.ndarray:
    sample_count = max(1, int(duration_ms * fs / 1000.0))
    t = np.arange(sample_count) / fs
    columns = []
    for frequency, decay_rate in zip(freqs, decays):
        envelope = np.exp(-decay_rate * t)
        columns.append(envelope * np.sin(2.0 * np.pi * frequency * t))
        columns.append(envelope * np.cos(2.0 * np.pi * frequency * t))
    return np.column_stack(columns)


def build_dynamic_design(
    tracks: list[dict],
    fs: int,
    duration_ms: float = 100.0,
) -> np.ndarray:
    sample_count = max(1, int(duration_ms * fs / 1000.0))
    t = np.arange(sample_count) / fs
    t_ms = t * 1000.0

    columns = []
    mode_count = len(tracks)

    for mode_index in range(mode_count):
        track = tracks[mode_index]["track"]
        track_times = track["times_ms"]
        freq_traj = interp(track_times, track["frequency_hz"], t_ms)
        amp_traj = np.maximum(0.0, interp(track_times, track["amplitude"], t_ms))

        amp_norm = amp_traj / (amp_traj[0] + 1e-12)
        phase = 2.0 * np.pi * np.cumsum(freq_traj) / fs

        columns.append(amp_norm * np.sin(phase))
        columns.append(amp_norm * np.cos(phase))

    return np.column_stack(columns)


def solve_modal_fit(design: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    coeffs, _, _, _ = np.linalg.lstsq(design, target, rcond=None)
    reconstruction = design @ coeffs
    return coeffs, reconstruction.astype(np.float32)


def static_synthesize(
    freqs: list[float],
    decays: list[float],
    amps: np.ndarray,
    phases: np.ndarray,
    fs: int,
    duration_ms: float = 100.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sample_count = max(1, int(duration_ms * fs / 1000.0))
    t = np.arange(sample_count) / fs
    reconstruction = np.zeros(sample_count, dtype=float)

    for frequency, decay_rate, amplitude, phase in zip(freqs, decays, amps, phases):
        reconstruction += amplitude * np.exp(-decay_rate * t) * np.sin(2.0 * np.pi * frequency * t + phase)

    return reconstruction.astype(np.float32), t * 1000.0, t


def local_rms_trace(sig: np.ndarray, reference: np.ndarray, fs: int, window_ms: float = 5.0, hop_ms: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    window_samples = max(8, int(window_ms * fs / 1000.0))
    hop_samples = max(1, int(hop_ms * fs / 1000.0))
    times_ms = []
    ratios = []
    ref_rms = float(np.sqrt(np.mean(reference**2)))

    for start in range(0, len(sig) - window_samples + 1, hop_samples):
        stop = start + window_samples
        error = reference[start:stop] - sig[start:stop]
        rms_error = float(np.sqrt(np.mean(error**2)))
        ratios.append(rms_error / (ref_rms + 1e-12))
        times_ms.append((start + window_samples / 2.0) / fs * 1000.0)

    return np.asarray(times_ms, dtype=np.float32), np.asarray(ratios, dtype=np.float32)


def compute_metrics(original: np.ndarray, reconstruction: np.ndarray) -> tuple[float, float]:
    error = original - reconstruction
    rms_original = float(np.sqrt(np.mean(original**2)))
    rms_error = float(np.sqrt(np.mean(error**2)))
    rms_ratio = rms_error / (rms_original + 1e-12)
    snr = 20.0 * np.log10(rms_original / (rms_error + 1e-12))
    return rms_ratio, snr


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    tracks_by_material = load_time_varying_tracks()
    consensus_by_material = load_consensus_modes()
    materials = ["glass", "mug", "metal_bowl", "wood"]

    fig, axes = plt.subplots(len(materials), 2, figsize=(16, 16))
    fig.suptitle("Experiment 11 - Dynamic Modal Resynthesis", fontsize=16, fontweight="bold")

    summary = {}
    report = []
    report.append("# Experiment 11: Dynamic Modal Resynthesis Report")
    report.append("")
    report.append("This experiment compares a static modal model against a dynamic modal model using the time-varying trajectories measured in Experiment 10A.")
    report.append("")

    for row_idx, material in enumerate(materials):
        fs, sig = load_material_signal(material)
        onset_idx = detect_onset(sig)
        window_samples = min(len(sig) - onset_idx, int(0.1 * fs))
        if window_samples <= 0:
            continue

        original = sig[onset_idx : onset_idx + window_samples]
        modes = consensus_by_material.get(material, [])
        track_records = tracks_by_material.get(material, [])

        if not modes or not track_records:
            summary[material] = {}
            continue

        mode_limit = min(4, len(modes), len(track_records))
        selected_tracks = track_records[:mode_limit]

        freqs = [float(m["consensus_frequency_hz"]) for m in selected_tracks]
        decays = [float(t["decay_start_1_s"]) for t in selected_tracks]

        static_design = build_static_design(freqs, decays, fs, duration_ms=100.0)
        dynamic_design = build_dynamic_design(selected_tracks, fs, duration_ms=100.0)

        _, static_model = solve_modal_fit(static_design, original)
        _, dynamic_model = solve_modal_fit(dynamic_design, original)

        static_rms, static_snr = compute_metrics(original, static_model)
        dynamic_rms, dynamic_snr = compute_metrics(original, dynamic_model)

        static_trace_t, static_trace = local_rms_trace(static_model, original, fs)
        dynamic_trace_t, dynamic_trace = local_rms_trace(dynamic_model, original, fs)

        improvement_pct = 100.0 * (static_rms - dynamic_rms) / (static_rms + 1e-12)

        summary[material] = {
            "onset_idx": onset_idx,
            "window_ms": 100.0,
            "static_rms_ratio": static_rms,
            "static_snr_db": static_snr,
            "dynamic_rms_ratio": dynamic_rms,
            "dynamic_snr_db": dynamic_snr,
            "improvement_pct": improvement_pct,
            "static_local_rms": static_trace.tolist(),
            "dynamic_local_rms": dynamic_trace.tolist(),
            "mode_count": mode_limit,
        }

        report.append(f"## {material.replace('_', ' ').title()}")
        report.append(f"Onset index: {onset_idx} samples ({onset_idx / fs * 1000.0:.2f} ms)")
        report.append(f"Static model RMS ratio: **{static_rms:.2%}**")
        report.append(f"Static model SNR: **{static_snr:.2f} dB**")
        report.append(f"Dynamic model RMS ratio: **{dynamic_rms:.2%}**")
        report.append(f"Dynamic model SNR: **{dynamic_snr:.2f} dB**")
        report.append(f"Relative improvement: **{improvement_pct:.2f}%**")
        report.append("")

        if dynamic_rms < static_rms:
            verdict = "Dynamic modal trajectories improve reconstruction over a static basis."
        else:
            verdict = "Dynamic trajectories do not yet outperform the static basis for this material."

        report.append(f"Verdict: {verdict}")
        report.append("")

        print(
            f"{material}: static RMS={static_rms:.2%}, dynamic RMS={dynamic_rms:.2%}, improvement={improvement_pct:.2f}%"
        )

        ax_wave = axes[row_idx, 0]
        ax_err = axes[row_idx, 1]

        plot_samples = min(window_samples, int(0.1 * fs))
        t_plot = np.arange(plot_samples) / fs * 1000.0
        ax_wave.plot(t_plot, original[:plot_samples], color="black", linewidth=1.1, label="Original")
        ax_wave.plot(t_plot, static_model[:plot_samples], color="tab:red", linewidth=1.0, alpha=0.9, label=f"Static ({static_snr:.1f} dB)")
        ax_wave.plot(t_plot, dynamic_model[:plot_samples], color="tab:green", linewidth=1.1, alpha=0.9, label=f"Dynamic ({dynamic_snr:.1f} dB)")
        ax_wave.set_title(f"{material.replace('_', ' ').title()} - Reconstruction")
        ax_wave.set_ylabel("Amplitude")
        ax_wave.grid(True, alpha=0.2)
        ax_wave.legend(fontsize=8, loc="upper right")

        ax_err.plot(static_trace_t, static_trace, color="tab:red", linewidth=1.2, label="Static local RMS")
        ax_err.plot(dynamic_trace_t, dynamic_trace, color="tab:green", linewidth=1.2, label="Dynamic local RMS")
        ax_err.set_title(f"{material.replace('_', ' ').title()} - Local Error")
        ax_err.set_ylabel("Local RMS Error / Signal RMS")
        ax_err.grid(True, alpha=0.2)
        ax_err.legend(fontsize=8, loc="best")

    for ax in axes[-1, :]:
        ax.set_xlabel("Time from Onset (ms)")

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    plot_path = results_dir / "11_dynamic_modal_resynthesis.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved dynamic modal resynthesis plot to: {plot_path}")

    report.append("## Scientific Interpretation")
    report.append("")
    report.append("If the dynamic model reduces the same residual metrics used in Experiment 09, then the data supports time-varying modal parameters rather than a strictly static basis.")
    report.append("A weaker or mixed result would indicate that excitation separation still dominates the error budget, or that the tracked trajectories need stronger regularization.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **Experiment 11 turns measured mode drift into a dynamic synthesizer. If the dynamic model outperforms the static one, the modal system is evolving in time rather than remaining fixed.**")

    report_path = results_dir / "11_dynamic_modal_resynthesis_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    json_path = results_dir / "11_dynamic_modal_resynthesis.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved dynamic modal summary to: {json_path}")
    print(f"Saved report to: {report_path}")


if __name__ == "__main__":
    main()