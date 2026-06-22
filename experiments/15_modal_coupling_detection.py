"""
Resonance Intelligence - Experiment 15: Modal Coupling Detection

Question:
Are the modes independent oscillators, or is energy moving between them?

This script analyzes the time-varying trajectories from Experiment 10A to measure
pairwise coupling between modal envelopes and frequencies. It looks for:
- beat-like envelope modulation
- envelope coherence
- amplitude correlations
- frequency correlations

Outputs:
- 15_modal_coupling_detection.json
- 15_modal_coupling_detection_report.md
- 15_modal_coupling_detection.png
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import scipy.signal as signal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit("Install matplotlib to generate plots.") from exc


def load_tracks() -> dict:
    path = PROJECT_ROOT / "experiments" / "results" / "10a_time_varying_mode_analysis.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing Experiment 10A results: {path}. Run Experiment 10A first.")
    with open(path, "r") as f:
        return json.load(f)


def interpolate_track(track: dict, sample_rate_hz: float = 1000.0, duration_ms: float = 100.0) -> dict:
    sample_count = max(2, int(duration_ms * sample_rate_hz / 1000.0))
    t_ms = np.linspace(0.0, duration_ms, sample_count, endpoint=False)
    times_ms = np.asarray(track["times_ms"], dtype=float)
    freq = np.interp(t_ms, times_ms, np.asarray(track["frequency_hz"], dtype=float))
    amp = np.interp(t_ms, times_ms, np.asarray(track["amplitude"], dtype=float))
    decay = np.interp(t_ms, times_ms, np.asarray(track["decay_1_s"], dtype=float))
    return {"times_ms": t_ms, "frequency_hz": freq, "amplitude": amp, "decay_1_s": decay}


def correlation(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) == 0 or len(b) == 0:
        return 0.0
    a0 = a - np.mean(a)
    b0 = b - np.mean(b)
    denom = float(np.linalg.norm(a0) * np.linalg.norm(b0) + 1e-12)
    return float(np.dot(a0, b0) / denom)


def coherence_score(a: np.ndarray, b: np.ndarray, fs: float) -> float:
    nperseg = min(64, len(a))
    if nperseg < 8:
        return 0.0
    _, coh = signal.coherence(a, b, fs=fs, nperseg=nperseg)
    if len(coh) == 0:
        return 0.0
    return float(np.mean(coh[: min(len(coh), 8)]))


def reconstruct_mode_component(track: dict, fs: int = 44_100, duration_ms: float = 100.0) -> tuple[np.ndarray, np.ndarray]:
    sample_count = max(1, int(duration_ms * fs / 1000.0))
    t = np.arange(sample_count) / fs
    t_ms = t * 1000.0
    freq = np.interp(t_ms, track["times_ms"], track["frequency_hz"])
    amp = np.interp(t_ms, track["times_ms"], track["amplitude"])
    amp = np.maximum(0.0, amp)
    amp = amp / (amp[0] + 1e-12)
    phase = 2.0 * np.pi * np.cumsum(freq) / fs
    component = amp * np.sin(phase)
    return component.astype(np.float32), freq.astype(np.float32)


def envelope_sideband_metrics(pair_sum: np.ndarray, fs: int) -> dict:
    envelope = np.abs(signal.hilbert(pair_sum))
    envelope = envelope - np.mean(envelope)
    envelope_fft = np.fft.rfft(envelope * np.hanning(len(envelope)))
    freqs = np.fft.rfftfreq(len(envelope), d=1.0 / fs)
    power = np.abs(envelope_fft) ** 2
    power_total = float(np.sum(power) + 1e-12)
    low_band_mask = freqs <= 250.0
    low_band_fraction = float(np.sum(power[low_band_mask]) / power_total)
    peak_idx = int(np.argmax(power[1:]) + 1) if len(power) > 1 else 0
    dominant_mod_hz = float(freqs[peak_idx]) if len(freqs) else 0.0
    return {
        "low_band_fraction": low_band_fraction,
        "dominant_modulation_hz": dominant_mod_hz,
        "dominant_modulation_power": float(power[peak_idx]) if len(power) else 0.0,
    }


def beat_alignment(freq_a: np.ndarray, freq_b: np.ndarray, envelope_metrics: dict) -> float:
    mean_sep = float(np.mean(np.abs(freq_a - freq_b)))
    observed = envelope_metrics["dominant_modulation_hz"]
    return float(np.exp(-abs(mean_sep - observed) / max(1.0, mean_sep)))


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    tracks_by_material = load_tracks()
    materials = ["glass", "mug", "metal_bowl", "wood"]

    summary = {}
    rows = []

    for material in materials:
        material_tracks = tracks_by_material.get(material, [])
        interpolated = [interpolate_track(record["track"], sample_rate_hz=1000.0, duration_ms=100.0) for record in material_tracks[:4]]
        components = []
        frequencies = []
        amplitudes = []
        for track in interpolated:
            component, freq = reconstruct_mode_component(track)
            components.append(component)
            frequencies.append(freq)
            amplitudes.append(track["amplitude"])

        pair_rows = []
        n_modes = len(components)
        for i in range(n_modes):
            for j in range(i + 1, n_modes):
                amp_corr = correlation(amplitudes[i], amplitudes[j])
                freq_corr = correlation(frequencies[i], frequencies[j])
                envelope_coh = coherence_score(amplitudes[i], amplitudes[j], fs=1000.0)
                pair_sum = components[i] + components[j]
                envelope_metrics = envelope_sideband_metrics(pair_sum, fs=44_100)
                beat_score = beat_alignment(frequencies[i], frequencies[j], envelope_metrics)
                coupling_score = float(0.4 * abs(amp_corr) + 0.3 * abs(freq_corr) + 0.2 * envelope_coh + 0.1 * envelope_metrics["low_band_fraction"])
                pair_rows.append(
                    {
                        "material": material,
                        "mode_i": i,
                        "mode_j": j,
                        "amplitude_correlation": amp_corr,
                        "frequency_correlation": freq_corr,
                        "envelope_coherence": envelope_coh,
                        "low_band_fraction": envelope_metrics["low_band_fraction"],
                        "dominant_modulation_hz": envelope_metrics["dominant_modulation_hz"],
                        "beat_alignment": beat_score,
                        "coupling_score": coupling_score,
                    }
                )

        ranked = sorted(pair_rows, key=lambda row: row["coupling_score"], reverse=True)
        coupling_mean = float(np.mean([row["coupling_score"] for row in pair_rows])) if pair_rows else 0.0
        frequency_corr_mean = float(np.mean([row["frequency_correlation"] for row in pair_rows])) if pair_rows else 0.0
        amplitude_corr_mean = float(np.mean([row["amplitude_correlation"] for row in pair_rows])) if pair_rows else 0.0
        envelope_coherence_mean = float(np.mean([row["envelope_coherence"] for row in pair_rows])) if pair_rows else 0.0

        summary[material] = {
            "mode_count": n_modes,
            "pairwise_metrics": pair_rows,
            "mean_coupling_score": coupling_mean,
            "mean_frequency_correlation": frequency_corr_mean,
            "mean_amplitude_correlation": amplitude_corr_mean,
            "mean_envelope_coherence": envelope_coherence_mean,
            "top_pair": ranked[0] if ranked else None,
        }

        rows.append({"material": material, "mean_coupling_score": coupling_mean, "mean_frequency_correlation": frequency_corr_mean, "mean_amplitude_correlation": amplitude_corr_mean, "mean_envelope_coherence": envelope_coherence_mean})

    global_pairs = [pair for material in materials for pair in summary[material]["pairwise_metrics"]]
    top_pairs = sorted(global_pairs, key=lambda row: row["coupling_score"], reverse=True)[:8]
    strong_pairs = [row for row in global_pairs if row["coupling_score"] >= 0.45]
    strong_pair_rate = float(len(strong_pairs) / max(1, len(global_pairs)))

    report = []
    report.append("# Experiment 15: Modal Coupling Detection Report")
    report.append("")
    report.append("This experiment checks whether modal pairs behave like independent oscillators or show coupling, beating, sidebands, or shared envelopes.")
    report.append("")
    report.append(f"Strong-pair rate (coupling score >= 0.45): **{strong_pair_rate:.2%}**")
    report.append("")
    report.append("## Material Summaries")
    report.append("")
    report.append("| Material | Mean Coupling | Mean Amp Corr | Mean Freq Corr | Mean Envelope Coherence |")
    report.append("| :--- | :---: | :---: | :---: | :---: |")
    for row in rows:
        report.append(
            f"| {row['material']} | {row['mean_coupling_score']:.3f} | {row['mean_amplitude_correlation']:.3f} | {row['mean_frequency_correlation']:.3f} | {row['mean_envelope_coherence']:.3f} |"
        )
    report.append("")
    report.append("## Top Coupled Pairs")
    report.append("")
    report.append("| Material | Mode i | Mode j | Amp Corr | Freq Corr | Env Coh | Low-Band Fraction | Beat Align | Coupling |")
    report.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for row in top_pairs:
        report.append(
            f"| {row.get('material', '?')} | {row['mode_i']} | {row['mode_j']} | {row['amplitude_correlation']:.3f} | {row['frequency_correlation']:.3f} | {row['envelope_coherence']:.3f} | {row['low_band_fraction']:.3f} | {row['beat_alignment']:.3f} | {row['coupling_score']:.3f} |"
        )
    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append("High amplitude correlation and high envelope coherence indicate shared envelopes, while high frequency correlation suggests frequency pulling or coordinated drift.")
    report.append("A strong low-band envelope spectrum suggests beat-like modulation rather than independent stationary modes.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **If the top pair scores are consistently high and the envelopes share low-frequency modulation, the modes are not independent oscillators. That would support energy exchange or coupling inside the resonator description.**")

    json_path = results_dir / "15_modal_coupling_detection.json"
    report_path = results_dir / "15_modal_coupling_detection_report.md"
    plot_path = results_dir / "15_modal_coupling_detection.png"

    with open(json_path, "w") as f:
        json.dump({"materials": summary, "strong_pair_rate": strong_pair_rate, "top_pairs": top_pairs}, f, indent=2)

    with open(report_path, "w") as f:
        f.write("\n".join(report))

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    materials_order = [row["material"] for row in rows]
    axes[0, 0].bar(materials_order, [row["mean_coupling_score"] for row in rows], color="tab:blue")
    axes[0, 0].set_title("Mean Coupling Score")
    axes[0, 0].set_ylim(0.0, 1.0)
    axes[0, 0].grid(True, axis="y", alpha=0.2)

    axes[0, 1].bar(materials_order, [row["mean_amplitude_correlation"] for row in rows], color="tab:orange")
    axes[0, 1].set_title("Mean Amplitude Correlation")
    axes[0, 1].set_ylim(-1.0, 1.0)
    axes[0, 1].grid(True, axis="y", alpha=0.2)

    axes[1, 0].bar(materials_order, [row["mean_frequency_correlation"] for row in rows], color="tab:green")
    axes[1, 0].set_title("Mean Frequency Correlation")
    axes[1, 0].set_ylim(-1.0, 1.0)
    axes[1, 0].grid(True, axis="y", alpha=0.2)

    axes[1, 1].bar(materials_order, [row["mean_envelope_coherence"] for row in rows], color="tab:red")
    axes[1, 1].set_title("Mean Envelope Coherence")
    axes[1, 1].set_ylim(0.0, 1.0)
    axes[1, 1].grid(True, axis="y", alpha=0.2)

    fig.suptitle("Experiment 15 - Modal Coupling Diagnostics", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)

    print(f"Saved coupling summary to: {json_path}")
    print(f"Saved report to: {report_path}")
    print(f"Saved plot to: {plot_path}")


if __name__ == "__main__":
    main()