"""
Resonance Intelligence - Experiment 10A: Time-Varying Mode Analysis

This script asks whether modal frequencies are stationary over the first 100 ms
of each impact sound. For the strongest consensus modes of each material, it
tracks instantaneous frequency, decay, and amplitude using a narrow-band analytic
signal measurement and reports the trajectories as f(t), d(t), and A(t).

Outputs:
- 10a_time_varying_mode_analysis.png
- 10a_time_varying_mode_analysis.json
- 10a_time_varying_mode_analysis_report.md
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


def load_sweep_results() -> dict:
    sweep_path = PROJECT_ROOT / "experiments" / "results" / "03_observer_sweep.json"
    if not sweep_path.exists():
        raise FileNotFoundError(f"Missing sweep results: {sweep_path}. Run Experiment 03 first.")

    with open(sweep_path, "r") as f:
        return json.load(f)


def bandpass_mode(sig: np.ndarray, fs: int, center_frequency: float, bandwidth_hz: float) -> np.ndarray:
    nyquist = fs / 2.0
    low = max(20.0, center_frequency - bandwidth_hz / 2.0)
    high = min(nyquist * 0.98, center_frequency + bandwidth_hz / 2.0)
    if low >= high:
        return sig.copy()

    sos = signal.butter(4, [low / nyquist, high / nyquist], btype="bandpass", output="sos")
    return signal.sosfiltfilt(sos, sig)


def track_mode_parameters(
    sig: np.ndarray,
    fs: int,
    center_frequency: float,
    onset_idx: int,
    analysis_ms: float = 100.0,
    window_ms: float = 12.0,
    hop_ms: float = 1.0,
) -> dict:
    analysis_samples = max(1, int(analysis_ms * fs / 1000.0))
    segment = sig[onset_idx : min(len(sig), onset_idx + analysis_samples)]
    if len(segment) < 16:
        return {
            "times_ms": [],
            "frequency_hz": [],
            "decay_1_s": [],
            "amplitude": [],
        }

    bandwidth_hz = max(60.0, min(center_frequency * 0.25, center_frequency * 0.9))
    filtered = bandpass_mode(sig, fs, center_frequency, bandwidth_hz)
    segment = filtered[onset_idx : min(len(filtered), onset_idx + analysis_samples)]

    window_samples = max(16, int(window_ms * fs / 1000.0))
    hop_samples = max(1, int(hop_ms * fs / 1000.0))

    times_ms = []
    frequency_hz = []
    decay_1_s = []
    amplitude = []

    eps = 1e-12
    for start in range(0, len(segment) - window_samples + 1, hop_samples):
        stop = start + window_samples
        window = segment[start:stop]
        local_time = np.arange(window.size) / fs
        analytic = signal.hilbert(window)
        envelope = np.abs(analytic)
        phase = np.unwrap(np.angle(analytic))

        inst_freq = np.gradient(phase, local_time, edge_order=1) / (2.0 * np.pi)
        freq_value = float(np.median(inst_freq[1:-1])) if window.size > 4 else float(np.mean(inst_freq))

        log_env = np.log(envelope + eps)
        slope, _ = np.polyfit(local_time, log_env, 1)
        decay_value = float(max(0.0, -slope))

        amplitude_value = float(np.mean(envelope))
        center_ms = (start + window_samples / 2.0) / fs * 1000.0

        times_ms.append(center_ms)
        frequency_hz.append(freq_value)
        decay_1_s.append(decay_value)
        amplitude.append(amplitude_value)

    def smooth(values: list[float]) -> list[float]:
        if len(values) < 7:
            return values
        length = len(values)
        window_length = 7 if length >= 7 else length | 1
        if window_length % 2 == 0:
            window_length -= 1
        if window_length < 5:
            return values
        return signal.savgol_filter(values, window_length=window_length, polyorder=2).tolist()

    frequency_hz = smooth(frequency_hz)
    decay_1_s = smooth(decay_1_s)
    amplitude = smooth(amplitude)

    return {
        "times_ms": times_ms,
        "frequency_hz": frequency_hz,
        "decay_1_s": decay_1_s,
        "amplitude": amplitude,
    }


def summarize_track(track: dict) -> dict:
    times = np.asarray(track["times_ms"], dtype=float)
    freq = np.asarray(track["frequency_hz"], dtype=float)
    decay = np.asarray(track["decay_1_s"], dtype=float)
    amp = np.asarray(track["amplitude"], dtype=float)

    def slope(values: np.ndarray) -> float:
        if len(times) < 2 or len(values) < 2:
            return 0.0
        return float(np.polyfit(times, values, 1)[0])

    def delta_pct(values: np.ndarray) -> float:
        if len(values) == 0:
            return 0.0
        start = float(values[0])
        end = float(values[-1])
        return float(100.0 * (end - start) / (abs(start) + 1e-12))

    return {
        "frequency_start_hz": float(freq[0]) if len(freq) else 0.0,
        "frequency_end_hz": float(freq[-1]) if len(freq) else 0.0,
        "frequency_delta_hz": float((freq[-1] - freq[0])) if len(freq) else 0.0,
        "frequency_drift_pct": delta_pct(freq),
        "frequency_slope_hz_per_ms": slope(freq),
        "decay_start_1_s": float(decay[0]) if len(decay) else 0.0,
        "decay_end_1_s": float(decay[-1]) if len(decay) else 0.0,
        "decay_delta_1_s": float(decay[-1] - decay[0]) if len(decay) else 0.0,
        "decay_slope_1_s_per_ms": slope(decay),
        "amplitude_start": float(amp[0]) if len(amp) else 0.0,
        "amplitude_end": float(amp[-1]) if len(amp) else 0.0,
        "amplitude_delta": float(amp[-1] - amp[0]) if len(amp) else 0.0,
        "amplitude_slope_per_ms": slope(amp),
    }


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    sweep_results = load_sweep_results()
    materials = ["glass", "mug", "metal_bowl", "wood"]
    max_modes = 4

    fig, axes = plt.subplots(len(materials), 3, figsize=(18, 16), sharex=True)
    fig.suptitle("Experiment 10A - Time-Varying Mode Analysis (0-100 ms)", fontsize=16, fontweight="bold")

    summary = {}
    report = []
    report.append("# Experiment 10A: Time-Varying Mode Analysis Report")
    report.append("")
    report.append("This experiment tests whether modal frequencies are stationary over the first 100 ms after onset.")
    report.append("We track the strongest consensus modes with a narrow-band analytic-signal observer and measure f(t), d(t), and A(t).");
    report.append("")

    for row_idx, material in enumerate(materials):
        fs, sig = load_material_signal(material)
        onset_idx = detect_onset(sig)
        modes = sweep_results.get(material, [])
        if not modes:
            summary[material] = []
            continue

        selected_modes = sorted(modes, key=lambda m: (m.get("agreement_count", 0), m.get("amplitude", 0.0)), reverse=True)[:max_modes]
        material_summary = []

        report.append(f"## {material.replace('_', ' ').title()}")
        report.append(f"Onset index: {onset_idx} samples ({onset_idx / fs * 1000.0:.2f} ms)")
        report.append("")
        report.append("| Mode Freq (Hz) | f start | f end | f drift % | d start | d end | A start | A end |")
        report.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

        colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(selected_modes)))

        for mode_idx, (mode, color) in enumerate(zip(selected_modes, colors)):
            center_frequency = float(mode["frequency"])
            track = track_mode_parameters(sig, fs, center_frequency, onset_idx, analysis_ms=100.0, window_ms=12.0, hop_ms=1.0)
            track_summary = summarize_track(track)
            track_summary.update(
                {
                    "consensus_frequency_hz": center_frequency,
                    "agreement_count": int(mode.get("agreement_count", 0)),
                    "agreement_rate": float(mode.get("agreement_rate", 0.0)),
                    "track": track,
                }
            )
            material_summary.append(track_summary)

            report.append(
                f"| {center_frequency:.2f} | {track_summary['frequency_start_hz']:.2f} | {track_summary['frequency_end_hz']:.2f} | {track_summary['frequency_drift_pct']:.2f}% | "
                f"{track_summary['decay_start_1_s']:.2f} | {track_summary['decay_end_1_s']:.2f} | {track_summary['amplitude_start']:.4f} | {track_summary['amplitude_end']:.4f} |"
            )

            print(
                f"{material} mode {center_frequency:.2f} Hz: "
                f"f {track_summary['frequency_start_hz']:.2f}->{track_summary['frequency_end_hz']:.2f} Hz, "
                f"d {track_summary['decay_start_1_s']:.2f}->{track_summary['decay_end_1_s']:.2f} 1/s"
            )

            times = np.asarray(track["times_ms"], dtype=float)
            freq = np.asarray(track["frequency_hz"], dtype=float)
            decay = np.asarray(track["decay_1_s"], dtype=float)
            amp = np.asarray(track["amplitude"], dtype=float)

            ax_f = axes[row_idx, 0]
            ax_d = axes[row_idx, 1]
            ax_a = axes[row_idx, 2]

            label = f"{center_frequency:.0f} Hz"
            ax_f.plot(times, freq, color=color, linewidth=1.5, label=label)
            ax_d.plot(times, decay, color=color, linewidth=1.5, label=label)
            ax_a.plot(times, amp, color=color, linewidth=1.5, label=label)

        summary[material] = material_summary

        for ax, title, ylabel in [
            (axes[row_idx, 0], f"{material.replace('_', ' ').title()} - f(t)", "Instantaneous Frequency (Hz)"),
            (axes[row_idx, 1], f"{material.replace('_', ' ').title()} - d(t)", "Instantaneous Decay (1/s)"),
            (axes[row_idx, 2], f"{material.replace('_', ' ').title()} - A(t)", "Amplitude"),
        ]:
            ax.set_title(title)
            ax.set_ylabel(ylabel)
            ax.set_xlim(0.0, 100.0)
            ax.grid(True, alpha=0.2)
            ax.axvline(0.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
            ax.axvline(100.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)

        axes[row_idx, 0].legend(fontsize=7, loc="best")

    for ax in axes[-1, :]:
        ax.set_xlabel("Time from Onset (ms)")

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    plot_path = results_dir / "10a_time_varying_mode_analysis.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved time-varying mode plot to: {plot_path}")

    report.append("## Scientific Interpretation")
    report.append("")
    report.append("If the fitted frequency, decay, and amplitude trajectories are nearly flat, the mode is stationary over the 0-100 ms observation window.")
    report.append("If the frequency trajectory shifts materially, that is direct evidence of detuning or effective mode motion rather than a fixed modal basis.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **Experiment 10A measures stationarity directly. Any consistent slope in f(t), d(t), or A(t) is evidence that the modal parameters are evolving, not fixed.**")
    report.append("> That result would motivate a dynamic modal synthesizer in the next experiment.")

    report_path = results_dir / "10a_time_varying_mode_analysis_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    json_path = results_dir / "10a_time_varying_mode_analysis.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved time-varying summary to: {json_path}")
    print(f"Saved report to: {report_path}")


if __name__ == "__main__":
    main()