"""
Resonance Intelligence - Experiment 12: Dynamic Residual Decomposition

This script analyzes the remainder left by the dynamic modal model from
Experiment 11. It compares the residual of the static modal basis and the
dynamic modal basis, then decomposes the dynamic remainder into:
- residual spectrum and dominant peaks
- residual decay and half-life
- residual energy concentration over time
- band-limited energy fractions

Outputs:
- 12_dynamic_residual_decomposition.png
- 12_dynamic_residual_decomposition.json
- 12_dynamic_residual_decomposition_report.md
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


def build_static_design(freqs: list[float], decays: list[float], fs: int, duration_ms: float = 100.0) -> np.ndarray:
    sample_count = max(1, int(duration_ms * fs / 1000.0))
    t = np.arange(sample_count) / fs
    columns = []
    for frequency, decay_rate in zip(freqs, decays):
        envelope = np.exp(-decay_rate * t)
        columns.append(envelope * np.sin(2.0 * np.pi * frequency * t))
        columns.append(envelope * np.cos(2.0 * np.pi * frequency * t))
    return np.column_stack(columns)


def build_dynamic_design(tracks: list[dict], fs: int, duration_ms: float = 100.0) -> np.ndarray:
    sample_count = max(1, int(duration_ms * fs / 1000.0))
    t = np.arange(sample_count) / fs
    t_ms = t * 1000.0
    columns = []

    for mode_index in range(len(tracks)):
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


def residual_decay(residual: np.ndarray, fs: int, onset_idx: int, fit_ms: float = 80.0) -> tuple[float, float]:
    start = onset_idx
    stop = min(len(residual), onset_idx + int(fit_ms * fs / 1000.0))
    segment = residual[start:stop]
    if len(segment) < 16:
        return 0.0, 0.0

    envelope = np.abs(signal.hilbert(segment))
    t = np.arange(len(envelope)) / fs
    valid = envelope > (np.max(envelope) * 1e-3)
    if np.count_nonzero(valid) < 8:
        valid = np.ones_like(envelope, dtype=bool)

    slope, _ = np.polyfit(t[valid], np.log(envelope[valid] + 1e-12), 1)
    decay_rate = float(max(0.0, -slope))
    half_life_ms = float((np.log(2.0) / (decay_rate + 1e-12)) * 1000.0) if decay_rate > 0 else float("inf")
    return decay_rate, half_life_ms


def residual_spectrum(residual: np.ndarray, fs: int) -> tuple[np.ndarray, np.ndarray, dict, list[dict]]:
    nperseg = min(4096, len(residual)) if len(residual) >= 16 else len(residual)
    freqs, psd = signal.welch(residual, fs=fs, nperseg=nperseg, noverlap=None)
    psd = np.maximum(psd, 1e-18)
    flatness = float(np.exp(np.mean(np.log(psd))) / np.mean(psd))
    centroid = float(np.sum(freqs * psd) / (np.sum(psd) + 1e-12))
    rolloff_idx = int(np.searchsorted(np.cumsum(psd) / (np.sum(psd) + 1e-12), 0.85))
    rolloff_hz = float(freqs[min(rolloff_idx, len(freqs) - 1)])

    smoothed = signal.savgol_filter(psd, 21 if len(psd) > 21 else max(5, len(psd) // 2 * 2 + 1), 3) if len(psd) >= 7 else psd
    prominence = 0.10 * np.max(smoothed)
    peak_indices, _ = signal.find_peaks(smoothed, prominence=prominence)

    peaks = []
    if len(peak_indices) > 0:
        ranked = peak_indices[np.argsort(smoothed[peak_indices])[::-1]][:6]
        for idx in ranked:
            peaks.append({"frequency_hz": float(freqs[idx]), "power": float(psd[idx])})

    band_edges = [1000.0, 4000.0]
    band_bounds = [0.0, band_edges[0], band_edges[1], fs / 2.0]
    band_energy = []
    total = float(np.sum(psd) + 1e-12)
    for start_hz, stop_hz in zip(band_bounds[:-1], band_bounds[1:]):
        mask = (freqs >= start_hz) & (freqs < stop_hz)
        band_energy.append(float(np.sum(psd[mask]) / total))

    return freqs, psd, {
        "spectral_flatness": flatness,
        "spectral_centroid_hz": centroid,
        "spectral_rolloff_85_hz": rolloff_hz,
        "band_energy_fractions": {
            "0_1k": band_energy[0],
            "1k_4k": band_energy[1],
            "4k_plus": band_energy[2],
        },
    }, peaks


def residual_category(flatness: float, decay_rate: float, peak_count: int, energy_5ms: float) -> str:
    if energy_5ms >= 0.50 and decay_rate >= 30.0:
        return "Broadband transient"
    if peak_count >= 4 and flatness < 0.25:
        return "Structured tonal residue / sidebands"
    if decay_rate < 25.0:
        return "Slow detuning or dynamic modes"
    return "Mixed residual"


def compute_metrics(original: np.ndarray, reconstruction: np.ndarray) -> tuple[float, float]:
    error = original - reconstruction
    rms_original = float(np.sqrt(np.mean(original**2)))
    rms_error = float(np.sqrt(np.mean(error**2)))
    rms_ratio = rms_error / (rms_original + 1e-12)
    snr = 20.0 * np.log10(rms_original / (rms_error + 1e-12))
    return rms_ratio, snr


def energy_metrics(residual: np.ndarray, fs: int) -> dict:
    energy = residual**2
    total = float(np.sum(energy) + 1e-12)
    cumulative = np.cumsum(energy) / total
    reach_50 = int(np.searchsorted(cumulative, 0.5))
    reach_90 = int(np.searchsorted(cumulative, 0.9))
    reach_99 = int(np.searchsorted(cumulative, 0.99))
    first_5ms_samples = max(1, int(0.005 * fs))
    first_5ms_energy = float(np.sum(energy[:first_5ms_samples]) / total)

    zero_crossings = np.count_nonzero(np.diff(np.signbit(residual)))
    zcr = float(zero_crossings / max(1, len(residual) - 1))

    return {
        "first_5ms_energy_fraction": first_5ms_energy,
        "t50_ms": float(reach_50 / fs * 1000.0),
        "t90_ms": float(reach_90 / fs * 1000.0),
        "t99_ms": float(reach_99 / fs * 1000.0),
        "zero_crossing_rate": zcr,
    }


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    tracks_by_material = load_time_varying_tracks()
    consensus_by_material = load_consensus_modes()
    materials = ["glass", "mug", "metal_bowl", "wood"]

    fig, axes = plt.subplots(len(materials), 3, figsize=(18, 16))
    fig.suptitle("Experiment 12 - Dynamic Residual Decomposition", fontsize=16, fontweight="bold")

    summary = {}
    report = []
    report.append("# Experiment 12: Dynamic Residual Decomposition Report")
    report.append("")
    report.append("This experiment analyzes the remainder left by the dynamic modal model from Experiment 11.")
    report.append("It asks what the dynamic model still fails to explain after time-varying frequency and amplitude have been introduced.")
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

        residual_static = original - static_model
        residual_dynamic = original - dynamic_model

        static_rms, static_snr = compute_metrics(original, static_model)
        dynamic_rms, dynamic_snr = compute_metrics(original, dynamic_model)
        residual_static_rms = float(np.sqrt(np.mean(residual_static**2)))
        residual_dynamic_rms = float(np.sqrt(np.mean(residual_dynamic**2)))
        residual_improvement_pct = 100.0 * (residual_static_rms - residual_dynamic_rms) / (residual_static_rms + 1e-12)

        static_decay, static_half_life = residual_decay(residual_static, fs, 0)
        dynamic_decay, dynamic_half_life = residual_decay(residual_dynamic, fs, 0)

        static_energy = energy_metrics(residual_static, fs)
        dynamic_energy = energy_metrics(residual_dynamic, fs)

        static_freqs, static_psd, static_spec, static_peaks = residual_spectrum(residual_static, fs)
        dynamic_freqs, dynamic_psd, dynamic_spec, dynamic_peaks = residual_spectrum(residual_dynamic, fs)

        static_category = residual_category(
            static_spec["spectral_flatness"],
            static_decay,
            len(static_peaks),
            static_energy["first_5ms_energy_fraction"],
        )
        dynamic_category = residual_category(
            dynamic_spec["spectral_flatness"],
            dynamic_decay,
            len(dynamic_peaks),
            dynamic_energy["first_5ms_energy_fraction"],
        )

        summary[material] = {
            "onset_idx": onset_idx,
            "window_ms": 100.0,
            "static_rms_ratio": static_rms,
            "static_snr_db": static_snr,
            "dynamic_rms_ratio": dynamic_rms,
            "dynamic_snr_db": dynamic_snr,
            "residual_static_rms": residual_static_rms,
            "residual_dynamic_rms": residual_dynamic_rms,
            "residual_improvement_pct": residual_improvement_pct,
            "static_decay_rate": static_decay,
            "static_half_life_ms": static_half_life,
            "dynamic_decay_rate": dynamic_decay,
            "dynamic_half_life_ms": dynamic_half_life,
            "static_energy": static_energy,
            "dynamic_energy": dynamic_energy,
            "static_spectrum": {
                **static_spec,
                "peaks": static_peaks,
            },
            "dynamic_spectrum": {
                **dynamic_spec,
                "peaks": dynamic_peaks,
            },
            "static_category": static_category,
            "dynamic_category": dynamic_category,
        }

        report.append(f"## {material.replace('_', ' ').title()}")
        report.append(f"Onset index: {onset_idx} samples ({onset_idx / fs * 1000.0:.2f} ms)")
        report.append(f"Static model RMS ratio: **{static_rms:.2%}**")
        report.append(f"Dynamic model RMS ratio: **{dynamic_rms:.2%}**")
        report.append(f"Residual RMS improvement: **{residual_improvement_pct:.2f}%**")
        report.append(f"Static residual decay: **{static_decay:.2f} 1/s** (half-life {static_half_life:.2f} ms)")
        report.append(f"Dynamic residual decay: **{dynamic_decay:.2f} 1/s** (half-life {dynamic_half_life:.2f} ms)")
        report.append(f"Static spectral flatness: **{static_spec['spectral_flatness']:.3f}**")
        report.append(f"Dynamic spectral flatness: **{dynamic_spec['spectral_flatness']:.3f}**")
        report.append(f"Dynamic first-5ms energy: **{dynamic_energy['first_5ms_energy_fraction']:.2%}**")
        report.append(f"Dynamic t90: **{dynamic_energy['t90_ms']:.2f} ms**")
        report.append(f"Dynamic category: **{dynamic_category}**")
        report.append("")

        report.append("| Residual State | RMS Ratio | SNR | Category |")
        report.append("| :--- | :---: | :---: | :--- |")
        report.append(f"| Static | {static_rms:.2%} | {static_snr:.2f} dB | {static_category} |")
        report.append(f"| Dynamic | {dynamic_rms:.2%} | {dynamic_snr:.2f} dB | {dynamic_category} |")
        report.append("")
        report.append("| Dynamic Residual Peaks (Hz) | Relative Power |")
        report.append("| :--- | :---: |")
        if dynamic_peaks:
            for peak in dynamic_peaks[:5]:
                report.append(f"| {peak['frequency_hz']:.2f} | {peak['power']:.4e} |")
        else:
            report.append("| None detected | - |")
        report.append("")

        print(
            f"{material}: static resid={residual_static_rms:.2%}, dynamic resid={residual_dynamic_rms:.2%}, "
            f"category={dynamic_category}"
        )

        ax_wave = axes[row_idx, 0]
        ax_energy = axes[row_idx, 1]
        ax_spec = axes[row_idx, 2]

        plot_samples = min(len(original), int(0.1 * fs))
        t_plot = np.arange(plot_samples) / fs * 1000.0
        ax_wave.plot(t_plot, residual_static[:plot_samples], color="tab:red", linewidth=1.0, alpha=0.8, label="Static residual")
        ax_wave.plot(t_plot, residual_dynamic[:plot_samples], color="tab:green", linewidth=1.1, label="Dynamic residual")
        ax_wave.axhline(0.0, color="gray", linewidth=0.8)
        ax_wave.set_title(f"{material.replace('_', ' ').title()} - Residual Waveforms")
        ax_wave.set_ylabel("Amplitude")
        ax_wave.grid(True, alpha=0.2)
        ax_wave.legend(fontsize=8, loc="upper right")

        ax_energy.plot(static_energy["t90_ms"], 0.9, marker="o", color="tab:red", label="Static t90")
        ax_energy.plot(dynamic_energy["t90_ms"], 0.9, marker="o", color="tab:green", label="Dynamic t90")
        static_times, static_local = local_rms_trace(residual_static, original, fs)
        dynamic_times, dynamic_local = local_rms_trace(residual_dynamic, original, fs)
        ax_energy.plot(static_times, static_local, color="tab:red", linewidth=1.1, alpha=0.8, label="Static local RMS")
        ax_energy.plot(dynamic_times, dynamic_local, color="tab:green", linewidth=1.1, alpha=0.9, label="Dynamic local RMS")
        ax_energy.set_title(f"{material.replace('_', ' ').title()} - Residual Energy")
        ax_energy.set_xlabel("Time from Onset (ms)")
        ax_energy.set_ylabel("Local RMS / Signal RMS")
        ax_energy.grid(True, alpha=0.2)
        ax_energy.legend(fontsize=8, loc="best")

        ax_spec.semilogy(static_freqs, static_psd, color="tab:red", linewidth=1.0, alpha=0.55, label="Static PSD")
        ax_spec.semilogy(dynamic_freqs, dynamic_psd, color="tab:green", linewidth=1.2, label="Dynamic PSD")
        for peak in dynamic_peaks[:4]:
            ax_spec.axvline(peak["frequency_hz"], color="tab:orange", linestyle="--", alpha=0.7)
        ax_spec.set_title(f"{material.replace('_', ' ').title()} - Residual Spectrum")
        ax_spec.set_xlabel("Frequency (Hz)")
        ax_spec.set_ylabel("PSD")
        ax_spec.set_xlim(0.0, min(fs / 2.0, 8000.0))
        ax_spec.grid(True, alpha=0.2)
        ax_spec.legend(fontsize=8, loc="best")

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    plot_path = results_dir / "12_dynamic_residual_decomposition.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved dynamic residual plot to: {plot_path}")

    report.append("## Scientific Interpretation")
    report.append("")
    report.append("The dynamic remainder is the part of the signal that remains unexplained even after the mode trajectories have been allowed to move in time.")
    report.append("Comparing static and dynamic residuals tells us whether the leftover error is mostly due to missing mode drift, uncaptured excitation, or genuinely non-modal structure.")
    report.append("")
    report.append("### Category Key")
    report.append("- Broadband transient: residual energy is front-loaded and spectrally flat.")
    report.append("- Structured tonal residue / sidebands: residual still contains narrow peaks, suggesting coupling or missing modulation products.")
    report.append("- Slow detuning or dynamic modes: residual decays slowly, suggesting the current trajectories still underfit the motion of the modes.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **Experiment 12 measures the remainder of the dynamic model itself. If the dynamic residual is still structured, the next step is not more static fitting, but more expressive dynamics or explicit excitation modeling.**")

    report_path = results_dir / "12_dynamic_residual_decomposition_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    json_path = results_dir / "12_dynamic_residual_decomposition.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved dynamic residual summary to: {json_path}")
    print(f"Saved report to: {report_path}")


if __name__ == "__main__":
    main()