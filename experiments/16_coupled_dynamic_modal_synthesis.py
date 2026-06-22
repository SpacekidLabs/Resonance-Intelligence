"""
Resonance Intelligence - Experiment 16: Coupled Dynamic Modal Synthesis

Scientific question:
Does explicit coupling explain more error than adding more independent modes?

This script compares two syntheses built from the time-varying tracks in
Experiment 10A:
- Model A: independent dynamic modes
- Model B: coupled dynamic modes using the strong pairs found in Experiment 15

It measures reconstruction RMS error, SNR, residual energy, and residual
classification accuracy on windowed residual features.

Outputs:
- 16_coupled_dynamic_modal_synthesis.json
- 16_coupled_dynamic_modal_synthesis_report.md
- 16_coupled_dynamic_modal_synthesis.png
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from resonance.extraction import detect_onset

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit("Install matplotlib to generate plots.") from exc


def synthesize_material_impact(material: str, duration: float, fs: int = 44_100) -> np.ndarray:
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
    sig[:burst_len] += rng.normal(0.0, 0.1, burst_len) * hann_win

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
        raise FileNotFoundError(f"Missing Experiment 10A results: {path}. Run Experiment 10A first.")
    with open(path, "r") as f:
        return json.load(f)


def load_coupling_pairs() -> dict:
    path = PROJECT_ROOT / "experiments" / "results" / "15_modal_coupling_detection.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing Experiment 15 results: {path}. Run Experiment 15 first.")
    with open(path, "r") as f:
        return json.load(f)


def build_trajectory_bundle(tracks: list[dict], fs: int, duration_ms: float = 100.0) -> tuple[np.ndarray, np.ndarray]:
    sample_count = max(1, int(duration_ms * fs / 1000.0))
    t = np.arange(sample_count) / fs
    t_ms = t * 1000.0
    freqs = []
    amps = []
    for record in tracks:
        track = record["track"]
        freq_traj = np.interp(t_ms, np.asarray(track["times_ms"], dtype=float), np.asarray(track["frequency_hz"], dtype=float))
        amp_traj = np.interp(t_ms, np.asarray(track["times_ms"], dtype=float), np.asarray(track["amplitude"], dtype=float))
        freqs.append(freq_traj)
        amps.append(np.maximum(0.0, amp_traj))
    return np.asarray(freqs, dtype=float).T, np.asarray(amps, dtype=float).T


def coupling_matrix(pair_rows: list[dict], mode_count: int, threshold: float = 0.75) -> np.ndarray:
    matrix = np.zeros((mode_count, mode_count), dtype=float)
    for row in pair_rows:
        score = float(row["coupling_score"])
        if score < threshold:
            continue
        i = int(row["mode_i"])
        j = int(row["mode_j"])
        weight = (score - threshold) / max(1e-12, (1.0 - threshold))
        matrix[i, j] = max(matrix[i, j], weight)
        matrix[j, i] = max(matrix[j, i], weight)
    return matrix


def coupled_trajectories(base_freq: np.ndarray, base_amp: np.ndarray, coupling: np.ndarray, gain_freq: float = 0.08, gain_amp: float = 0.04) -> tuple[np.ndarray, np.ndarray]:
    coupled_freq = base_freq.copy()
    coupled_amp = base_amp.copy()
    for t in range(1, base_freq.shape[0]):
        prev_freq = coupled_freq[t - 1]
        prev_amp = coupled_amp[t - 1]
        freq_pull = coupling @ prev_freq - np.sum(coupling, axis=1) * prev_freq
        amp_pull = coupling @ prev_amp - np.sum(coupling, axis=1) * prev_amp
        coupled_freq[t] = np.maximum(1.0, base_freq[t] + gain_freq * freq_pull)
        coupled_amp[t] = np.maximum(0.0, base_amp[t] + gain_amp * amp_pull)
    return coupled_freq, coupled_amp


def design_from_trajectories(freq_traj: np.ndarray, amp_traj: np.ndarray, fs: int) -> np.ndarray:
    sample_count, mode_count = freq_traj.shape
    columns = []
    for mode_idx in range(mode_count):
        amp = amp_traj[:, mode_idx]
        amp = amp / (amp[0] + 1e-12)
        phase = 2.0 * np.pi * np.cumsum(freq_traj[:, mode_idx]) / fs
        columns.append(amp * np.sin(phase))
        columns.append(amp * np.cos(phase))
    return np.column_stack(columns)


def fit_and_reconstruct(design: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    coeffs, _, _, _ = np.linalg.lstsq(design, target, rcond=None)
    reconstruction = design @ coeffs
    return coeffs, reconstruction.astype(np.float32)


def compute_metrics(original: np.ndarray, reconstruction: np.ndarray) -> tuple[float, float, float]:
    error = original - reconstruction
    rms_original = float(np.sqrt(np.mean(original**2)))
    rms_error = float(np.sqrt(np.mean(error**2)))
    rms_ratio = rms_error / (rms_original + 1e-12)
    snr = 20.0 * np.log10(rms_original / (rms_error + 1e-12))
    residual_energy_fraction = float(np.sum(error**2) / (np.sum(original**2) + 1e-12))
    return rms_ratio, snr, residual_energy_fraction


def window_features(sig: np.ndarray, fs: int) -> np.ndarray:
    segment = np.asarray(sig, dtype=float)
    if len(segment) < 8:
        return np.zeros(8, dtype=float)

    energy = segment**2
    rms = float(np.sqrt(np.mean(energy)))
    crest_factor = float(np.max(np.abs(segment)) / (rms + 1e-12))
    zcr = float(np.mean(segment[:-1] * segment[1:] < 0.0))
    envelope = np.abs(signal.hilbert(segment))
    slope = float(np.polyfit(np.arange(len(segment)) / fs, envelope, 1)[0])
    nperseg = min(256, len(segment))
    freqs, psd = signal.welch(segment, fs=fs, nperseg=max(8, nperseg), noverlap=None)
    psd = np.maximum(psd, 1e-18)
    flatness = float(np.exp(np.mean(np.log(psd))) / np.mean(psd))
    centroid = float(np.sum(freqs * psd) / (np.sum(psd) + 1e-12))
    rolloff_idx = int(np.searchsorted(np.cumsum(psd) / (np.sum(psd) + 1e-12), 0.85))
    rolloff = float(freqs[min(rolloff_idx, len(freqs) - 1)])
    band_bounds = [0.0, 1000.0, 4000.0, fs / 2.0]
    total = float(np.sum(psd) + 1e-12)
    band_energy = []
    for start_hz, stop_hz in zip(band_bounds[:-1], band_bounds[1:]):
        mask = (freqs >= start_hz) & (freqs < stop_hz)
        band_energy.append(float(np.sum(psd[mask]) / total))
    return np.array([rms, crest_factor, zcr, slope, flatness, centroid / 5000.0, rolloff / 5000.0, *band_energy], dtype=float)


def residual_window_dataset(residuals_by_material: dict[str, np.ndarray], fs: int) -> tuple[np.ndarray, np.ndarray]:
    features = []
    labels = []
    window_ms = 20.0
    hop_ms = 10.0
    window_samples = int(window_ms * fs / 1000.0)
    hop_samples = int(hop_ms * fs / 1000.0)
    for material, residual in residuals_by_material.items():
        for start in range(0, max(1, len(residual) - window_samples + 1), hop_samples):
            stop = start + window_samples
            if stop > len(residual):
                break
            features.append(window_features(residual[start:stop], fs))
            labels.append(material)
    return np.vstack(features), np.asarray(labels, dtype=object)


def leave_one_window_out_centroid(features: np.ndarray, labels: np.ndarray, class_names: list[str]) -> tuple[float, dict[str, float], list[str]]:
    predictions: list[str] = []
    truths: list[str] = []
    for idx in range(len(labels)):
        train_mask = np.ones(len(labels), dtype=bool)
        train_mask[idx] = False
        train_features = features[train_mask]
        train_labels = labels[train_mask]
        test_feature = features[idx]
        mean = np.mean(train_features, axis=0)
        std = np.std(train_features, axis=0)
        std[std < 1e-9] = 1.0
        normalized_train = (train_features - mean) / std
        normalized_test = (test_feature - mean) / std
        centroids = {}
        for class_name in class_names:
            class_samples = normalized_train[train_labels == class_name]
            centroids[class_name] = np.mean(class_samples, axis=0)
        distances = {class_name: float(np.linalg.norm(normalized_test - centroid)) for class_name, centroid in centroids.items()}
        predictions.append(min(distances, key=distances.get))
        truths.append(labels[idx])

    accuracy = float(np.mean(np.asarray(predictions) == np.asarray(truths))) if truths else 0.0
    per_class_accuracy = {}
    for class_name in class_names:
        mask = np.asarray(truths) == class_name
        per_class_accuracy[class_name] = float(np.mean(np.asarray(predictions)[mask] == np.asarray(truths)[mask])) if np.any(mask) else 0.0
    return accuracy, per_class_accuracy, predictions


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    tracks_by_material = load_time_varying_tracks()
    coupling_data = load_coupling_pairs()
    materials = ["glass", "mug", "metal_bowl", "wood"]

    summary = {}
    residuals_independent = {}
    residuals_coupled = {}

    for material in materials:
        fs, sig = load_material_signal(material)
        onset_idx = detect_onset(sig)
        window_samples = min(len(sig) - onset_idx, int(0.1 * fs))
        if window_samples <= 0:
            continue

        original = sig[onset_idx : onset_idx + window_samples]
        tracks = tracks_by_material.get(material, [])
        if not tracks:
            continue

        mode_limit = min(4, len(tracks))
        selected_tracks = tracks[:mode_limit]
        base_freq, base_amp = build_trajectory_bundle(selected_tracks, fs, duration_ms=100.0)
        pair_rows = coupling_data["materials"][material]["pairwise_metrics"]
        coupling = coupling_matrix(pair_rows, mode_limit, threshold=0.75)
        coupled_freq, coupled_amp = coupled_trajectories(base_freq, base_amp, coupling)

        independent_design = design_from_trajectories(base_freq, base_amp, fs)
        coupled_design = design_from_trajectories(coupled_freq, coupled_amp, fs)

        _, independent_recon = fit_and_reconstruct(independent_design, original)
        _, coupled_recon = fit_and_reconstruct(coupled_design, original)

        independent_rms, independent_snr, independent_residual_energy = compute_metrics(original, independent_recon)
        coupled_rms, coupled_snr, coupled_residual_energy = compute_metrics(original, coupled_recon)

        residuals_independent[material] = original - independent_recon
        residuals_coupled[material] = original - coupled_recon

        summary[material] = {
            "onset_idx": int(onset_idx),
            "mode_count": int(mode_limit),
            "coupling_threshold": 0.75,
            "strong_pair_count": int(np.count_nonzero(np.triu(coupling > 0, 1))),
            "independent": {
                "rms_ratio": independent_rms,
                "snr_db": independent_snr,
                "residual_energy_fraction": independent_residual_energy,
            },
            "coupled": {
                "rms_ratio": coupled_rms,
                "snr_db": coupled_snr,
                "residual_energy_fraction": coupled_residual_energy,
            },
            "improvement_pct": 100.0 * (independent_rms - coupled_rms) / (independent_rms + 1e-12),
        }

    indep_features, indep_labels = residual_window_dataset(residuals_independent, fs=44_100)
    coupled_features, coupled_labels = residual_window_dataset(residuals_coupled, fs=44_100)

    independent_classification_accuracy, independent_per_class_accuracy, independent_predictions = leave_one_window_out_centroid(indep_features, indep_labels, materials)
    coupled_classification_accuracy, coupled_per_class_accuracy, coupled_predictions = leave_one_window_out_centroid(coupled_features, coupled_labels, materials)

    summary_overall = {
        "materials": materials,
        "independent_residual_classification_accuracy": independent_classification_accuracy,
        "coupled_residual_classification_accuracy": coupled_classification_accuracy,
        "classification_gap": independent_classification_accuracy - coupled_classification_accuracy,
        "independent_per_class_accuracy": independent_per_class_accuracy,
        "coupled_per_class_accuracy": coupled_per_class_accuracy,
        "materials_detail": summary,
    }

    report = []
    report.append("# Experiment 16: Coupled Dynamic Modal Synthesis Report")
    report.append("")
    report.append("This experiment compares independent dynamic modes against explicit coupling between the strong mode pairs from Experiment 15.")
    report.append("")
    report.append("## Overall Classification")
    report.append("")
    report.append(f"Residual classification accuracy, independent model: **{independent_classification_accuracy:.2%}**")
    report.append(f"Residual classification accuracy, coupled model: **{coupled_classification_accuracy:.2%}**")
    report.append(f"Classification gap (independent - coupled): **{independent_classification_accuracy - coupled_classification_accuracy:.2%}**")
    report.append("")
    report.append("## Per-Material Reconstruction")
    report.append("")
    report.append("| Material | Indep RMS | Coupled RMS | Indep SNR | Coupled SNR | Indep Residual Energy | Coupled Residual Energy | Improvement |")
    report.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for material in materials:
        stats = summary[material]
        report.append(
            f"| {material} | {stats['independent']['rms_ratio']:.2%} | {stats['coupled']['rms_ratio']:.2%} | {stats['independent']['snr_db']:.2f} | {stats['coupled']['snr_db']:.2f} | {stats['independent']['residual_energy_fraction']:.2%} | {stats['coupled']['residual_energy_fraction']:.2%} | {stats['improvement_pct']:.2f}% |"
        )
    report.append("")
    report.append("## Per-Class Residual Identification")
    report.append("")
    report.append("| Material | Indep Residual Acc | Coupled Residual Acc |")
    report.append("| :--- | :---: | :---: |")
    for material in materials:
        report.append(f"| {material} | {independent_per_class_accuracy[material]:.2%} | {coupled_per_class_accuracy[material]:.2%} |")
    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append("If the coupled synthesizer lowers RMS error and reduces residual-classification accuracy, explicit interaction is explaining structure that the independent model leaves behind.")
    report.append("If it does not, then the coupling graph is not yet strong enough or the remaining error is due to missing mechanisms beyond pairwise interaction.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **Experiment 16 asks whether pairwise coupling between modes reduces the leftover error more effectively than independent dynamic synthesis. A reduction in residual energy and residual identifiability would support a coupled-resonator synthesis architecture.**")

    json_path = results_dir / "16_coupled_dynamic_modal_synthesis.json"
    report_path = results_dir / "16_coupled_dynamic_modal_synthesis_report.md"
    plot_path = results_dir / "16_coupled_dynamic_modal_synthesis.png"

    with open(json_path, "w") as f:
        json.dump(summary_overall, f, indent=2)

    with open(report_path, "w") as f:
        f.write("\n".join(report))

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    xs = np.arange(len(materials))
    width = 0.35

    axes[0, 0].bar(xs - width / 2, [summary[m]["independent"]["rms_ratio"] for m in materials], width, label="Independent", color="tab:blue")
    axes[0, 0].bar(xs + width / 2, [summary[m]["coupled"]["rms_ratio"] for m in materials], width, label="Coupled", color="tab:orange")
    axes[0, 0].set_title("RMS Error Ratio")
    axes[0, 0].set_xticks(xs)
    axes[0, 0].set_xticklabels([m.replace("_", " ").title() for m in materials])
    axes[0, 0].grid(True, axis="y", alpha=0.2)
    axes[0, 0].legend()

    axes[0, 1].bar(xs - width / 2, [summary[m]["independent"]["snr_db"] for m in materials], width, label="Independent", color="tab:blue")
    axes[0, 1].bar(xs + width / 2, [summary[m]["coupled"]["snr_db"] for m in materials], width, label="Coupled", color="tab:orange")
    axes[0, 1].set_title("SNR (dB)")
    axes[0, 1].set_xticks(xs)
    axes[0, 1].set_xticklabels([m.replace("_", " ").title() for m in materials])
    axes[0, 1].grid(True, axis="y", alpha=0.2)

    axes[1, 0].bar(xs - width / 2, [summary[m]["independent"]["residual_energy_fraction"] for m in materials], width, label="Independent", color="tab:blue")
    axes[1, 0].bar(xs + width / 2, [summary[m]["coupled"]["residual_energy_fraction"] for m in materials], width, label="Coupled", color="tab:orange")
    axes[1, 0].set_title("Residual Energy Fraction")
    axes[1, 0].set_xticks(xs)
    axes[1, 0].set_xticklabels([m.replace("_", " ").title() for m in materials])
    axes[1, 0].grid(True, axis="y", alpha=0.2)

    axes[1, 1].bar(xs - width / 2, [independent_per_class_accuracy[m] for m in materials], width, label="Independent residual", color="tab:blue")
    axes[1, 1].bar(xs + width / 2, [coupled_per_class_accuracy[m] for m in materials], width, label="Coupled residual", color="tab:orange")
    axes[1, 1].set_title("Residual Classification Accuracy")
    axes[1, 1].set_xticks(xs)
    axes[1, 1].set_xticklabels([m.replace("_", " ").title() for m in materials])
    axes[1, 1].set_ylim(0.0, 1.0)
    axes[1, 1].grid(True, axis="y", alpha=0.2)

    fig.suptitle("Experiment 16 - Coupled Dynamic Modal Synthesis", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)

    print(f"Saved coupled synthesis summary to: {json_path}")
    print(f"Saved report to: {report_path}")
    print(f"Saved plot to: {plot_path}")


if __name__ == "__main__":
    main()