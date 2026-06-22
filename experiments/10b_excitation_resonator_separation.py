"""
Resonance Intelligence - Experiment 10B: Excitation / Resonator Separation

This script treats the sound as an excitation force convolved with a resonator
impulse response. It estimates an effective excitation by regularized deconvolution
against the best phase-aligned modal reconstruction, then checks whether the
resulting excitation is short, broadband, and re-convolves back to the original
signal with low error.

Outputs:
- 10b_excitation_resonator_separation.png
- 10b_excitation_resonator_separation.json
- 10b_excitation_resonator_separation_report.md
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


def build_modal_impulse_response(freqs: list[float], decays: list[float], amps: list[float], fs: int, duration_s: float = 0.12) -> np.ndarray:
    t = np.arange(int(duration_s * fs)) / fs
    h = np.zeros_like(t)
    for frequency, decay_rate, amplitude in zip(freqs, decays, amps):
        h += amplitude * np.exp(-decay_rate * t) * np.sin(2.0 * np.pi * frequency * t)
    max_val = np.max(np.abs(h))
    if max_val > 0:
        h = h / max_val
    return h.astype(np.float32)


def estimate_best_modal_reconstruction(sig: np.ndarray, modes: list[dict], fs: int, max_modes: int = 12) -> tuple[np.ndarray, int, list[float], list[float], list[float]]:
    onset_idx = detect_onset(sig)
    consensus = modes[:max_modes]
    freqs = [m["frequency"] for m in consensus]
    decays = [m["decay_rate"] for m in consensus]
    amplitudes = [m["amplitude"] for m in consensus]

    fitted_amps, fitted_phases = fit_amplitudes_and_phases(sig, freqs, decays, fs, fit_window_samples=4000)
    aligned_modes = ModeList([
        Mode(frequency=f, amplitude=float(a), decay_rate=d, phase=float(p))
        for f, d, a, p in zip(freqs, decays, fitted_amps, fitted_phases)
    ])
    reconstruction = synthesize_modes_aligned(aligned_modes, len(sig), onset_idx, fs)
    return reconstruction, onset_idx, freqs, decays, amplitudes


def deconvolve_excitation(signal_in: np.ndarray, impulse_response: np.ndarray, reg: float = 1e-3) -> np.ndarray:
    n = len(signal_in) + len(impulse_response) - 1
    n_fft = 1 << int(np.ceil(np.log2(max(64, n))))

    s_fft = np.fft.rfft(signal_in, n=n_fft)
    h_fft = np.fft.rfft(impulse_response, n=n_fft)
    denom = np.abs(h_fft) ** 2 + reg
    excitation_fft = s_fft * np.conj(h_fft) / denom
    excitation = np.fft.irfft(excitation_fft, n=n_fft)[: len(signal_in)]
    return excitation.astype(np.float32)


def energy_concentration(sig: np.ndarray, fs: int, window_ms: float = 5.0) -> dict:
    window_samples = max(1, int(window_ms * fs / 1000.0))
    energy = sig**2
    total = float(np.sum(energy) + 1e-12)
    cumulative = np.cumsum(energy) / total
    reach_50 = int(np.searchsorted(cumulative, 0.5))
    reach_90 = int(np.searchsorted(cumulative, 0.9))
    reach_99 = int(np.searchsorted(cumulative, 0.99))

    first_window_energy = float(np.sum(energy[:window_samples]) / total)
    flatness = float(np.exp(np.mean(np.log(np.abs(np.fft.rfft(sig))**2 + 1e-18))) / np.mean(np.abs(np.fft.rfft(sig))**2 + 1e-18))

    return {
        "first_5ms_energy_fraction": first_window_energy,
        "t50_ms": float(reach_50 / fs * 1000.0),
        "t90_ms": float(reach_90 / fs * 1000.0),
        "t99_ms": float(reach_99 / fs * 1000.0),
        "spectral_flatness": flatness,
    }


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

    sweep_results = load_sweep_results()
    materials = ["glass", "mug", "metal_bowl", "wood"]

    fig, axes = plt.subplots(len(materials), 3, figsize=(18, 16), sharex=False)
    fig.suptitle("Experiment 10B - Excitation / Resonator Separation", fontsize=16, fontweight="bold")

    summary = {}
    report = []
    report.append("# Experiment 10B: Excitation / Resonator Separation Report")
    report.append("")
    report.append("This experiment treats the signal as a short excitation convolved with a resonator impulse response.")
    report.append("We estimate an effective excitation by regularized deconvolution and then re-convolve it to check whether the original sound can be recovered.")
    report.append("")

    for row_idx, material in enumerate(materials):
        fs, sig = load_material_signal(material)
        modes = sweep_results.get(material, [])
        if not modes:
            summary[material] = {}
            continue

        reconstruction, onset_idx, freqs, decays, amplitudes = estimate_best_modal_reconstruction(sig, modes, fs)
        residual = sig - reconstruction
        impulse_response = build_modal_impulse_response(freqs, decays, amplitudes, fs, duration_s=0.12)
        excitation = deconvolve_excitation(sig, impulse_response, reg=1e-3)
        resynthesized = signal.fftconvolve(excitation, impulse_response, mode="full")[: len(sig)]

        modal_rms, modal_snr = compute_metrics(sig, reconstruction)
        resynth_rms, resynth_snr = compute_metrics(sig, resynthesized)
        residual_rms, residual_snr = compute_metrics(sig, reconstruction)

        excitation_stats = energy_concentration(excitation, fs)
        excitation_peak = float(np.max(np.abs(excitation)))
        excitation_rms = float(np.sqrt(np.mean(excitation**2)))
        excitation_crest = float(excitation_peak / (excitation_rms + 1e-12))
        excitation_support_90 = excitation_stats["t90_ms"]
        excitation_broadband = excitation_stats["spectral_flatness"]

        summary[material] = {
            "onset_idx": onset_idx,
            "modal_reconstruction_rms_ratio": modal_rms,
            "modal_reconstruction_snr_db": modal_snr,
            "resynthesized_rms_ratio": resynth_rms,
            "resynthesized_snr_db": resynth_snr,
            "residual_rms_ratio": residual_rms,
            "residual_snr_db": residual_snr,
            "excitation_peak": excitation_peak,
            "excitation_rms": excitation_rms,
            "excitation_crest_factor": excitation_crest,
            "excitation_energy_fraction_first_5ms": excitation_stats["first_5ms_energy_fraction"],
            "excitation_t90_ms": excitation_support_90,
            "excitation_t99_ms": excitation_stats["t99_ms"],
            "excitation_spectral_flatness": excitation_broadband,
        }

        report.append(f"## {material.replace('_', ' ').title()}")
        report.append(f"Onset index: {onset_idx} samples ({onset_idx / fs * 1000.0:.2f} ms)")
        report.append(f"Modal reconstruction RMS ratio: **{modal_rms:.2%}**")
        report.append(f"Modal reconstruction SNR: **{modal_snr:.2f} dB**")
        report.append(f"Resynthesized-from-excitation RMS ratio: **{resynth_rms:.2%}**")
        report.append(f"Resynthesized-from-excitation SNR: **{resynth_snr:.2f} dB**")
        report.append(f"Excitation energy in first 5 ms: **{excitation_stats['first_5ms_energy_fraction']:.2%}**")
        report.append(f"Excitation t90: **{excitation_support_90:.2f} ms**")
        report.append(f"Excitation spectral flatness: **{excitation_broadband:.3f}**")
        report.append(f"Excitation crest factor: **{excitation_crest:.2f}**")
        report.append("")

        if excitation_support_90 <= 10.0 and excitation_broadband > 0.15:
            verdict = "Short, broadband strike excitation is separable from resonator response."
        elif excitation_support_90 <= 20.0:
            verdict = "Partial excitation/resonator separation is possible, but the strike is not fully compact." 
        else:
            verdict = "The excitation remains entangled with the resonator tail; a richer excitation model is needed."

        report.append(f"Verdict: {verdict}")
        report.append("")

        print(
            f"{material}: modal RMS={modal_rms:.2%}, resynth RMS={resynth_rms:.2%}, "
            f"t90={excitation_support_90:.2f} ms, flatness={excitation_broadband:.3f}"
        )

        ax_exc = axes[row_idx, 0]
        ax_sig = axes[row_idx, 1]
        ax_res = axes[row_idx, 2]

        plot_samples = min(len(sig), int(0.15 * fs))
        t_plot = np.arange(plot_samples) / fs * 1000.0
        ax_sig.plot(t_plot, sig[:plot_samples], color="black", linewidth=1.1, label="Original")
        ax_sig.plot(t_plot, reconstruction[:plot_samples], color="tab:green", linewidth=1.1, label="Modal Fit")
        ax_sig.plot(t_plot, resynthesized[:plot_samples], color="tab:blue", linewidth=1.0, alpha=0.8, label="Excitation * Resonator")
        ax_sig.axvline(onset_idx / fs * 1000.0, color="gray", linestyle="--", alpha=0.5)
        ax_sig.set_title(f"{material.replace('_', ' ').title()} - Reconstruction")
        ax_sig.set_ylabel("Amplitude")
        ax_sig.grid(True, alpha=0.2)
        ax_sig.legend(fontsize=8, loc="upper right")

        excitation_plot_samples = min(len(excitation), int(0.03 * fs))
        t_exc = np.arange(excitation_plot_samples) / fs * 1000.0
        ax_exc.plot(t_exc, excitation[:excitation_plot_samples], color="tab:red", linewidth=1.2)
        ax_exc.axhline(0.0, color="gray", linewidth=0.8)
        ax_exc.set_title(f"{material.replace('_', ' ').title()} - Estimated Excitation")
        ax_exc.set_ylabel("Amplitude")
        ax_exc.grid(True, alpha=0.2)

        residual_plot_samples = min(len(residual), int(0.15 * fs))
        t_res = np.arange(residual_plot_samples) / fs * 1000.0
        ax_res.plot(t_res, residual[:residual_plot_samples], color="tab:purple", linewidth=1.0)
        ax_res.axhline(0.0, color="gray", linewidth=0.8)
        ax_res.set_title(f"{material.replace('_', ' ').title()} - Modal Residual")
        ax_res.set_ylabel("Amplitude")
        ax_res.grid(True, alpha=0.2)

    for ax in axes[-1, :]:
        ax.set_xlabel("Time (ms)")

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    plot_path = results_dir / "10b_excitation_resonator_separation.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved excitation separation plot to: {plot_path}")

    report.append("## Scientific Interpretation")
    report.append("")
    report.append("If the deconvolved excitation is short and broadband, the strike is separable from the resonator response.")
    report.append("If the excitation remains long or tonal, the modal basis is still absorbing dynamics that should belong to the excitation model or to time-varying resonator behavior.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **Excitation / resonator separation becomes convincing only when the recovered force-like signal is compact in time and broad in spectrum, while the re-convolution reproduces the original waveform with low error.**")
    report.append("> If that holds, then the next step is dynamic modal resynthesis with separate excitation and resonator terms.")

    report_path = results_dir / "10b_excitation_resonator_separation_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    json_path = results_dir / "10b_excitation_resonator_separation.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved separation summary to: {json_path}")
    print(f"Saved report to: {report_path}")


if __name__ == "__main__":
    main()