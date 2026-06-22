"""
Resonance Intelligence - Experiment 09: Residual Decomposition

This script computes the residual left behind by the best reconstruction from
Experiment 05 (onset + phase aligned modal resynthesis) and analyzes what the
modal model fails to explain.

Outputs:
- 09_residual_decomposition.png
- 09_residual_decomposition.json
- 09_residual_decomposition_report.md
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
from resonance.modal import Mode, ModeList
from resonance.synthesis import fit_amplitudes_and_phases, synthesize_modes_aligned

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


def load_material_signal(material: str) -> tuple[int, np.ndarray]:
    wav_path = PROJECT_ROOT / "experiments" / "test_sounds" / f"{material}.wav"
    if not wav_path.exists():
        test_sounds_dir = PROJECT_ROOT / "experiments" / "test_sounds"
        test_sounds_dir.mkdir(parents=True, exist_ok=True)
        synthesized = synthesize_material_impact(material, duration=2.5)
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


def reconstruct_best_modal_fit(sig: np.ndarray, modes: list[dict], fs: int, max_modes: int = 12) -> tuple[np.ndarray, int, list[float], list[float]]:
    onset_idx = detect_onset(sig)
    consensus = modes[:max_modes]
    freqs = [m["frequency"] for m in consensus]
    decays = [m["decay_rate"] for m in consensus]

    fitted_amps, fitted_phases = fit_amplitudes_and_phases(sig, freqs, decays, fs, fit_window_samples=4000)
    aligned_modes = ModeList([
        Mode(frequency=f, amplitude=float(a), decay_rate=d, phase=float(p))
        for f, d, a, p in zip(freqs, decays, fitted_amps, fitted_phases)
    ])
    reconstruction = synthesize_modes_aligned(aligned_modes, len(sig), onset_idx, fs)
    return reconstruction, onset_idx, freqs, decays


def local_rms_trace(sig: np.ndarray, fs: int, window_ms: float = 5.0, hop_ms: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    window_samples = max(8, int(window_ms * fs / 1000.0))
    hop_samples = max(1, int(hop_ms * fs / 1000.0))

    centers_ms = []
    rms_values = []
    for start in range(0, len(sig) - window_samples + 1, hop_samples):
        stop = start + window_samples
        window = sig[start:stop]
        rms_values.append(float(np.sqrt(np.mean(window**2))))
        centers_ms.append((start + window_samples / 2.0) / fs * 1000.0)

    return np.asarray(centers_ms, dtype=np.float32), np.asarray(rms_values, dtype=np.float32)


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

    slope, intercept = np.polyfit(t[valid], np.log(envelope[valid] + 1e-12), 1)
    decay_rate = float(max(0.0, -slope))
    half_life_ms = float((np.log(2.0) / (decay_rate + 1e-12)) * 1000.0) if decay_rate > 0 else float("inf")
    return decay_rate, half_life_ms


def residual_spectrum(residual: np.ndarray, fs: int) -> tuple[np.ndarray, np.ndarray, float, list[dict]]:
    freqs, psd = signal.welch(residual, fs=fs, nperseg=min(4096, len(residual)), noverlap=None)
    psd = np.maximum(psd, 1e-18)
    flatness = float(np.exp(np.mean(np.log(psd))) / np.mean(psd))

    smoothed = signal.savgol_filter(psd, 21 if len(psd) > 21 else max(5, len(psd) // 2 * 2 + 1), 3) if len(psd) >= 7 else psd
    prominence = 0.10 * np.max(smoothed)
    peak_indices, _ = signal.find_peaks(smoothed, prominence=prominence)

    peaks = []
    if len(peak_indices) > 0:
        ranked = peak_indices[np.argsort(smoothed[peak_indices])[::-1]][:6]
        for idx in ranked:
            peaks.append({"frequency_hz": float(freqs[idx]), "power": float(psd[idx])})

    return freqs, psd, flatness, peaks


def residual_category(flatness: float, decay_rate: float, peak_count: int) -> str:
    if flatness >= 0.50 and peak_count <= 3:
        return "Broadband transient"
    if peak_count >= 4 and flatness < 0.40:
        return "Structured tonal residue / sidebands"
    if decay_rate < 25.0:
        return "Slow detuning or dynamic modes"
    return "Mixed residual"


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    sweep_results = load_sweep_results()
    materials = ["glass", "mug", "metal_bowl", "wood"]

    fig, axes = plt.subplots(len(materials), 3, figsize=(18, 16))
    fig.suptitle("Experiment 09 - Residual Decomposition", fontsize=16, fontweight="bold")

    summary = {}
    report = []
    report.append("# Experiment 09: Residual Decomposition Report")
    report.append("")
    report.append("This experiment subtracts the best phase-aligned modal reconstruction from the original signal and examines the leftover energy.")
    report.append("")
    report.append("Question: what is the modal model failing to explain?")
    report.append("")

    for row_idx, material in enumerate(materials):
        fs, sig = load_material_signal(material)
        onset_idx = detect_onset(sig)
        modes = sweep_results.get(material, [])
        if not modes:
            summary[material] = {}
            continue

        reconstruction, onset_idx, freqs, decays = reconstruct_best_modal_fit(sig, modes, fs)
        residual = sig - reconstruction

        rms_sig = float(np.sqrt(np.mean(sig**2)))
        rms_residual = float(np.sqrt(np.mean(residual**2)))
        rms_ratio = rms_residual / (rms_sig + 1e-12)
        snr = 20.0 * np.log10(rms_sig / (rms_residual + 1e-12))

        decay_rate, half_life_ms = residual_decay(residual, fs, onset_idx)
        env_centers_ms, env_rms = local_rms_trace(residual[onset_idx:], fs)
        env_norm = env_rms / (np.max(env_rms) + 1e-12)

        spec_freqs, spec_psd, flatness, peaks = residual_spectrum(residual[onset_idx:], fs)
        category = residual_category(flatness, decay_rate, len(peaks))

        summary[material] = {
            "onset_idx": onset_idx,
            "residual_rms_ratio": rms_ratio,
            "residual_snr_db": snr,
            "residual_decay_rate": decay_rate,
            "residual_half_life_ms": half_life_ms,
            "spectral_flatness": flatness,
            "peak_count": len(peaks),
            "peaks": peaks,
            "category": category,
        }

        report.append(f"## {material.replace('_', ' ').title()}")
        report.append(f"Residual RMS ratio: **{rms_ratio:.2%}**")
        report.append(f"Residual SNR: **{snr:.2f} dB**")
        report.append(f"Residual decay rate: **{decay_rate:.2f} 1/s**")
        report.append(f"Residual half-life: **{half_life_ms:.2f} ms**")
        report.append(f"Spectral flatness: **{flatness:.3f}**")
        report.append(f"Dominant residual peaks: **{len(peaks)}**")
        report.append(f"Residual category: **{category}**")
        report.append("")
        report.append("| Top Residual Peaks (Hz) | Relative Power |")
        report.append("| :--- | :---: |")
        if peaks:
            for peak in peaks[:5]:
                report.append(f"| {peak['frequency_hz']:.2f} | {peak['power']:.4e} |")
        else:
            report.append("| None detected | - |")
        report.append("")

        print(f"{material}: residual RMS={rms_ratio:.2%}, category={category}")

        ax_wave = axes[row_idx, 0]
        ax_energy = axes[row_idx, 1]
        ax_spec = axes[row_idx, 2]

        plot_samples = min(len(sig), int(0.15 * fs))
        t_plot = np.arange(plot_samples) / fs * 1000.0
        ax_wave.plot(t_plot, sig[:plot_samples], color="black", linewidth=1.1, label="Original")
        ax_wave.plot(t_plot, reconstruction[:plot_samples], color="tab:green", linewidth=1.1, label="Best Reconstruction")
        ax_wave.plot(t_plot, residual[:plot_samples], color="tab:red", linewidth=1.0, alpha=0.8, label="Residual")
        ax_wave.axvline(onset_idx / fs * 1000.0, color="gray", linestyle="--", alpha=0.5)
        ax_wave.set_title(f"{material.replace('_', ' ').title()} - Time Domain")
        ax_wave.set_xlabel("Time (ms)")
        ax_wave.set_ylabel("Amplitude")
        ax_wave.grid(True, alpha=0.2)
        ax_wave.legend(fontsize=8, loc="upper right")

        ax_energy.plot(env_centers_ms, env_norm, color="tab:purple", linewidth=1.4, label="Residual Energy")
        fit_end_ms = min(env_centers_ms[-1] if len(env_centers_ms) else 0.0, 80.0)
        ax_energy.set_title(f"{material.replace('_', ' ').title()} - Residual Energy")
        ax_energy.set_xlabel("Time from Onset (ms)")
        ax_energy.set_ylabel("Normalized Energy")
        ax_energy.set_ylim(0.0, 1.05)
        ax_energy.grid(True, alpha=0.2)
        ax_energy.legend(fontsize=8, loc="upper right")

        ax_spec.semilogy(spec_freqs, spec_psd, color="tab:blue", linewidth=1.2)
        for peak in peaks[:4]:
            ax_spec.axvline(peak["frequency_hz"], color="tab:orange", linestyle="--", alpha=0.7)
        ax_spec.set_title(f"{material.replace('_', ' ').title()} - Residual Spectrum")
        ax_spec.set_xlabel("Frequency (Hz)")
        ax_spec.set_ylabel("PSD")
        ax_spec.set_xlim(0.0, min(fs / 2.0, 8000.0))
        ax_spec.grid(True, alpha=0.2)

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    plot_path = results_dir / "09_residual_decomposition.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved residual decomposition plot to: {plot_path}")

    report.append("## Scientific Interpretation")
    report.append("")
    report.append("The residual is what remains after the best phase-aligned modal reconstruction has done its work. Its spectrum and envelope tell us which parts of the signal are not well explained by static decaying sinusoids.")
    report.append("")
    report.append("### Category Key")
    report.append("- Broadband transient: the residual is noise-like and concentrated near onset.")
    report.append("- Structured tonal residue / sidebands: the residual still contains narrow peaks, suggesting missing coupled modes or modulation products.")
    report.append("- Slow detuning or dynamic modes: the residual decays slowly, suggesting the modal basis is not tracking time-varying frequencies well enough.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **Residual decomposition shows what the modal basis does not explain: either transient excitation, frequency modulation, or coupled sideband structure.**")
    report.append("> If the residual is broadband and front-loaded, the next model needs an excitation term. If it remains tonal, the next model needs dynamic modes or coupling terms.")

    report_path = results_dir / "09_residual_decomposition_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    json_path = results_dir / "09_residual_decomposition.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved residual summary to: {json_path}")
    print(f"Saved report to: {report_path}")


if __name__ == "__main__":
    main()