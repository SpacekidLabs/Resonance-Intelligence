"""
Resonance Intelligence - Experiment 14: Excitation-Resonator Entanglement

Question:
How much object information is encoded inside the excitation itself?

This script compares a simple leave-one-out nearest-centroid classifier built from
excitation-only features against the same classifier built from resonator-only
features. If excitation-only accuracy is above chance, the excitation retains
object identity and helps explain the failed swaps from Experiment 13.

Outputs:
- 14_excitation_resonator_entanglement.json
- 14_excitation_resonator_entanglement_report.md
- 14_excitation_resonator_entanglement.png
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

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit("Install matplotlib to generate plots.") from exc


def load_experiment_13() -> dict:
    path = PROJECT_ROOT / "experiments" / "results" / "13_dynamic_excitation_modeling.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing Experiment 13 results: {path}. Run Experiment 13 first.")
    with open(path, "r") as f:
        return json.load(f)


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


def build_dynamic_design(selected_tracks: list[dict], fs: int, sample_count: int) -> np.ndarray:
    t = np.arange(sample_count) / fs
    t_ms = t * 1000.0
    columns = []
    for record in selected_tracks:
        track = record["track"]
        freq_traj = np.interp(t_ms, np.asarray(track["times_ms"], dtype=float), np.asarray(track["frequency_hz"], dtype=float))
        amp_traj = np.interp(t_ms, np.asarray(track["times_ms"], dtype=float), np.asarray(track["amplitude"], dtype=float))
        amp_traj = np.maximum(0.0, amp_traj)
        amp_traj = amp_traj / (amp_traj[0] + 1e-12)
        phase = 2.0 * np.pi * np.cumsum(freq_traj) / fs
        columns.append(amp_traj * np.sin(phase))
        columns.append(amp_traj * np.cos(phase))
    return np.column_stack(columns)


def reconstruct_excitation_and_resonator(material: str, tracks_by_material: dict, window_ms: float = 100.0) -> tuple[int, np.ndarray, np.ndarray, np.ndarray]:
    fs, sig = load_material_signal(material)
    onset_idx = 0
    sample_count = min(len(sig) - onset_idx, int(window_ms * fs / 1000.0))
    original = sig[onset_idx : onset_idx + sample_count]

    selected_tracks = tracks_by_material.get(material, [])[:4]
    if not selected_tracks:
        raise ValueError(f"No tracks found for {material}")

    design = build_dynamic_design(selected_tracks, fs, sample_count)
    coeffs, _, _, _ = np.linalg.lstsq(design, original, rcond=None)
    resonator = design @ coeffs
    excitation = original - resonator
    return fs, original.astype(np.float32), excitation.astype(np.float32), resonator.astype(np.float32)


def window_features(sig: np.ndarray, fs: int) -> np.ndarray:
    segment = np.asarray(sig, dtype=float)
    n = len(segment)
    if n == 0:
        return np.zeros(8, dtype=float)

    energy = segment**2
    rms = float(np.sqrt(np.mean(energy)))
    peak = float(np.max(np.abs(segment)))
    crest_factor = peak / (rms + 1e-12)
    zcr = float(np.mean(segment[:-1] * segment[1:] < 0.0)) if n > 1 else 0.0
    envelope = np.abs(signal.hilbert(segment)) if n > 3 else np.abs(segment)
    t = np.arange(n) / fs
    slope = float(np.polyfit(t, envelope, 1)[0]) if n > 3 else 0.0

    nperseg = min(256, n)
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


def build_window_dataset(original: np.ndarray, resonator: np.ndarray, excitation: np.ndarray, fs: int, material: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    window_ms = 20.0
    hop_ms = 10.0
    window_samples = int(window_ms * fs / 1000.0)
    hop_samples = int(hop_ms * fs / 1000.0)
    feature_excitation = []
    feature_resonator = []
    labels = []

    for start in range(0, max(1, len(original) - window_samples + 1), hop_samples):
        stop = start + window_samples
        if stop > len(original):
            break
        feature_excitation.append(window_features(excitation[start:stop], fs))
        feature_resonator.append(window_features(resonator[start:stop], fs))
        labels.append(material)

    return np.vstack(feature_excitation), np.vstack(feature_resonator), np.asarray(labels, dtype=object)


def leave_one_sample_out_centroid(features: np.ndarray, labels: np.ndarray, material_names: list[str]) -> tuple[float, dict[str, float], np.ndarray, list[str]]:
    predictions: list[str] = []
    truths: list[str] = []

    for test_idx in range(len(labels)):
        train_mask = np.ones(len(labels), dtype=bool)
        train_mask[test_idx] = False
        train_features = features[train_mask]
        train_labels = labels[train_mask]
        test_feature = features[test_idx]
        test_label = labels[test_idx]

        mean = np.mean(train_features, axis=0)
        std = np.std(train_features, axis=0)
        std[std < 1e-9] = 1.0
        normalized_train = (train_features - mean) / std
        normalized_test = (test_feature - mean) / std

        centroids = {}
        for label in material_names:
            class_samples = normalized_train[train_labels == label]
            centroids[label] = np.mean(class_samples, axis=0)

        distances = {label: float(np.linalg.norm(normalized_test - centroid)) for label, centroid in centroids.items()}
        predictions.append(min(distances, key=distances.get))
        truths.append(test_label)

    overall_accuracy = float(np.mean(np.asarray(predictions) == np.asarray(truths))) if truths else 0.0

    per_material_accuracy: dict[str, float] = {}
    for material in material_names:
        mask = np.asarray(truths) == material
        per_material_accuracy[material] = float(np.mean(np.asarray(predictions)[mask] == np.asarray(truths)[mask])) if np.any(mask) else 0.0

    classes = material_names
    matrix = np.zeros((len(classes), len(classes)), dtype=int)
    index_by_label = {label: idx for idx, label in enumerate(classes)}
    for truth, pred in zip(truths, predictions):
        matrix[index_by_label[truth], index_by_label[pred]] += 1

    return overall_accuracy, per_material_accuracy, matrix, predictions


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    data = load_experiment_13()["materials"]
    materials = ["glass", "mug", "metal_bowl", "wood"]

    tracks_by_material = load_time_varying_tracks()

    excitation_samples = []
    resonator_samples = []
    sample_labels = []
    for material in materials:
        fs, original, excitation, resonator = reconstruct_excitation_and_resonator(material, tracks_by_material)
        excitation_windows, resonator_windows, window_labels = build_window_dataset(original, resonator, excitation, fs, material)
        excitation_samples.append(excitation_windows)
        resonator_samples.append(resonator_windows)
        sample_labels.append(window_labels)

    excitation_features = np.vstack(excitation_samples)
    resonator_features = np.vstack(resonator_samples)
    labels = np.concatenate(sample_labels)

    excitation_accuracy, excitation_per_material, excitation_cm, excitation_predictions = leave_one_sample_out_centroid(excitation_features, labels, materials)
    resonator_accuracy, resonator_per_material, resonator_cm, resonator_predictions = leave_one_sample_out_centroid(resonator_features, labels, materials)

    chance = 1.0 / len(materials)
    summary = {
        "materials": materials,
        "chance_level": chance,
        "excitation_only": {
            "accuracy": excitation_accuracy,
            "predictions": excitation_predictions,
            "per_material_accuracy": excitation_per_material,
            "classes": materials,
            "confusion_matrix": excitation_cm.tolist(),
        },
        "resonator_only": {
            "accuracy": resonator_accuracy,
            "predictions": resonator_predictions,
            "per_material_accuracy": resonator_per_material,
            "classes": materials,
            "confusion_matrix": resonator_cm.tolist(),
        },
        "accuracy_gap": resonator_accuracy - excitation_accuracy,
        "excitation_above_chance": excitation_accuracy > chance,
        "resonator_above_chance": resonator_accuracy > chance,
    }

    report = []
    report.append("# Experiment 14: Excitation-Resonator Entanglement Report")
    report.append("")
    report.append("Question: how much object information is encoded inside the excitation itself?")
    report.append("")
    report.append("Each material contributes multiple 20 ms windows from the first 100 ms so the classifier has enough samples to learn from and test against.")
    report.append("")
    report.append(f"Chance level for 4-way classification: **{chance:.2%}**")
    report.append(f"Excitation-only leave-one-out accuracy: **{excitation_accuracy:.2%}**")
    report.append(f"Resonator-only leave-one-out accuracy: **{resonator_accuracy:.2%}**")
    report.append(f"Accuracy gap (resonator - excitation): **{resonator_accuracy - excitation_accuracy:.2%}**")
    report.append("")
    report.append("## Per-Material Accuracy")
    report.append("")
    report.append("| Material | Excitation Accuracy | Resonator Accuracy |")
    report.append("| :--- | :---: | :---: |")
    for material in materials:
        report.append(f"| {material} | {excitation_per_material[material]:.2%} | {resonator_per_material[material]:.2%} |")
    report.append("")
    report.append("## Per-Sample Predictions")
    report.append("")
    report.append("| Material | Excitation Prediction | Resonator Prediction |")
    report.append("| :--- | :--- | :--- |")
    for idx, material in enumerate(labels.tolist()):
        report.append(f"| {material} | {excitation_predictions[idx]} | {resonator_predictions[idx]} |")
    report.append("")
    report.append("## Interpretation")
    report.append("")
    if excitation_accuracy > chance:
        report.append("Excitation-only features exceed chance, so the excitation retains object identity information.")
    else:
        report.append("Excitation-only features do not exceed chance, so the excitation is not clearly carrying object identity on its own.")
    if resonator_accuracy >= excitation_accuracy:
        report.append("The resonator remains at least as informative as the excitation, which is consistent with the resonator retaining most material identity.")
    else:
        report.append("The excitation outperforms the resonator, which would suggest stronger entanglement than expected.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **If excitation-only classification is above chance, the excitation contains object information. That makes the failed swaps in Experiment 13 unsurprising: the excitation is not universal, it already carries some material signature.**")

    json_path = results_dir / "14_excitation_resonator_entanglement.json"
    report_path = results_dir / "14_excitation_resonator_entanglement_report.md"
    plot_path = results_dir / "14_excitation_resonator_entanglement.png"

    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    with open(report_path, "w") as f:
        f.write("\n".join(report))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    cmap = "Blues"
    for ax, matrix, classes, title in [
        (axes[0], excitation_cm, materials, f"Excitation-only (acc {excitation_accuracy:.0%})"),
        (axes[1], resonator_cm, materials, f"Resonator-only (acc {resonator_accuracy:.0%})"),
    ]:
        image = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=max(1, int(np.max(matrix))))
        ax.set_xticks(range(len(classes)))
        ax.set_yticks(range(len(classes)))
        ax.set_xticklabels(classes, rotation=45, ha="right")
        ax.set_yticklabels(classes)
        ax.set_title(title)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color="black", fontsize=10)
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.8, label="Count")
    fig.suptitle("Experiment 14 - Classification from Excitation vs Resonator Features", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)

    print(f"Saved classification summary to: {json_path}")
    print(f"Saved report to: {report_path}")
    print(f"Saved plot to: {plot_path}")


if __name__ == "__main__":
    main()