"""
Resonance Intelligence - Experiment 13: Dynamic Excitation Modeling

This script treats the dynamic residual from Experiment 12 as an excitation
candidate. It measures whether that residual is short-lived and broadband, then
tests recombination by pairing each material's excitation candidate with its own
dynamic resonator and with swapped resonators from the other materials.

Outputs:
- 13_dynamic_excitation_modeling.png
- 13_dynamic_excitation_modeling.json
- 13_dynamic_excitation_modeling_report.md
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


def load_dynamic_residuals() -> dict:
    path = PROJECT_ROOT / "experiments" / "results" / "12_dynamic_residual_decomposition.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing 12 results: {path}. Run Experiment 12 first.")
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


def build_dynamic_design(tracks: list[dict], fs: int, duration_ms: float = 100.0) -> np.ndarray:
    sample_count = max(1, int(duration_ms * fs / 1000.0))
    t = np.arange(sample_count) / fs
    t_ms = t * 1000.0
    columns = []

    for mode_index in range(len(tracks)):
        track = tracks[mode_index]["track"]
        freq_traj = interp(track["times_ms"], track["frequency_hz"], t_ms)
        amp_traj = np.maximum(0.0, interp(track["times_ms"], track["amplitude"], t_ms))
        amp_norm = amp_traj / (amp_traj[0] + 1e-12)
        phase = 2.0 * np.pi * np.cumsum(freq_traj) / fs
        columns.append(amp_norm * np.sin(phase))
        columns.append(amp_norm * np.cos(phase))

    return np.column_stack(columns)


def solve_modal_fit(design: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    coeffs, _, _, _ = np.linalg.lstsq(design, target, rcond=None)
    reconstruction = design @ coeffs
    return coeffs, reconstruction.astype(np.float32)


def fit_dynamic_models(materials: list[str], fs: int, original_by_material: dict, tracks_by_material: dict) -> dict:
    models = {}
    for material in materials:
        original = original_by_material[material]
        tracks = tracks_by_material.get(material, [])
        if not tracks:
            continue
        mode_limit = min(4, len(tracks))
        selected_tracks = tracks[:mode_limit]
        dynamic_design = build_dynamic_design(selected_tracks, fs, duration_ms=100.0)
        _, dynamic_model = solve_modal_fit(dynamic_design, original)
        residual = original - dynamic_model
        models[material] = {
            "dynamic_model": dynamic_model,
            "residual": residual,
            "tracks": selected_tracks,
            "mode_count": mode_limit,
        }
    return models


def spectrum_features(sig: np.ndarray, fs: int) -> dict:
    nperseg = min(4096, len(sig)) if len(sig) >= 16 else len(sig)
    freqs, psd = signal.welch(sig, fs=fs, nperseg=nperseg, noverlap=None)
    psd = np.maximum(psd, 1e-18)
    flatness = float(np.exp(np.mean(np.log(psd))) / np.mean(psd))
    centroid = float(np.sum(freqs * psd) / (np.sum(psd) + 1e-12))
    rolloff_idx = int(np.searchsorted(np.cumsum(psd) / (np.sum(psd) + 1e-12), 0.85))
    rolloff_hz = float(freqs[min(rolloff_idx, len(freqs) - 1)])

    band_bounds = [0.0, 1000.0, 4000.0, fs / 2.0]
    total = float(np.sum(psd) + 1e-12)
    band_energy = {}
    for start_hz, stop_hz, label in zip(band_bounds[:-1], band_bounds[1:], ["0_1k", "1k_4k", "4k_plus"]):
        mask = (freqs >= start_hz) & (freqs < stop_hz)
        band_energy[label] = float(np.sum(psd[mask]) / total)

    peak_indices, _ = signal.find_peaks(signal.savgol_filter(psd, 21 if len(psd) > 21 else max(5, len(psd) // 2 * 2 + 1), 3) if len(psd) >= 7 else psd,
                                        prominence=0.10 * np.max(psd))
    peaks = []
    if len(peak_indices) > 0:
        ranked = peak_indices[np.argsort(psd[peak_indices])[::-1]][:6]
        for idx in ranked:
            peaks.append({"frequency_hz": float(freqs[idx]), "power": float(psd[idx])})

    return {
        "freqs": freqs,
        "psd": psd,
        "spectral_flatness": flatness,
        "spectral_centroid_hz": centroid,
        "spectral_rolloff_85_hz": rolloff_hz,
        "band_energy_fractions": band_energy,
        "peaks": peaks,
    }


def residual_metrics(sig: np.ndarray, fs: int) -> dict:
    energy = sig**2
    total = float(np.sum(energy) + 1e-12)
    cumulative = np.cumsum(energy) / total
    t50 = float(np.searchsorted(cumulative, 0.5) / fs * 1000.0)
    t90 = float(np.searchsorted(cumulative, 0.9) / fs * 1000.0)
    t99 = float(np.searchsorted(cumulative, 0.99) / fs * 1000.0)
    first_10ms = float(np.sum(energy[: max(1, int(0.01 * fs))]) / total)
    first_5ms = float(np.sum(energy[: max(1, int(0.005 * fs))]) / total)

    envelope = np.abs(signal.hilbert(sig))
    t = np.arange(len(envelope)) / fs
    valid = envelope > (np.max(envelope) * 1e-3)
    if np.count_nonzero(valid) < 8:
        valid = np.ones_like(envelope, dtype=bool)
    slope, _ = np.polyfit(t[valid], np.log(envelope[valid] + 1e-12), 1)
    decay_rate = float(max(0.0, -slope))
    half_life_ms = float((np.log(2.0) / (decay_rate + 1e-12)) * 1000.0) if decay_rate > 0 else float("inf")

    peak_abs = float(np.max(np.abs(sig)))
    rms = float(np.sqrt(np.mean(sig**2)) + 1e-12)
    crest_factor = peak_abs / rms
    early_window = sig[: max(1, int(0.01 * fs))]
    early_mean_abs = float(np.mean(np.abs(early_window)) + 1e-12)
    early_peak = float(np.max(np.abs(early_window)) + 1e-12)

    return {
        "first_5ms_energy_fraction": first_5ms,
        "first_10ms_energy_fraction": first_10ms,
        "t50_ms": t50,
        "t90_ms": t90,
        "t99_ms": t99,
        "decay_rate_1_s": decay_rate,
        "half_life_ms": half_life_ms,
        "crest_factor": crest_factor,
        "early_peak_to_mean_abs": early_peak / early_mean_abs,
    }


def compute_rms_ratio(original: np.ndarray, reconstruction: np.ndarray) -> tuple[float, float]:
    error = original - reconstruction
    rms_original = float(np.sqrt(np.mean(original**2)))
    rms_error = float(np.sqrt(np.mean(error**2)))
    return rms_error / (rms_original + 1e-12), 20.0 * np.log10(rms_original / (rms_error + 1e-12))


def best_match_label(hybrid: np.ndarray, originals: dict[str, np.ndarray]) -> tuple[str, dict[str, float]]:
    scores = {}
    for material, original in originals.items():
        rms_ratio, _ = compute_rms_ratio(original, hybrid)
        scores[material] = rms_ratio
    return min(scores, key=scores.get), scores


def main() -> None:
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    materials = ["glass", "mug", "metal_bowl", "wood"]
    fs = 44_100

    tracks_by_material = load_time_varying_tracks()
    residuals_by_material = load_dynamic_residuals()
    consensus_by_material = load_consensus_modes()

    original_by_material = {}
    for material in materials:
        material_fs, sig = load_material_signal(material)
        fs = material_fs
        onset_idx = detect_onset(sig)
        original_by_material[material] = sig[onset_idx : onset_idx + int(0.1 * fs)]

    dynamic_models = fit_dynamic_models(materials, fs, original_by_material, tracks_by_material)

    fig, axes = plt.subplots(len(materials), 3, figsize=(18, 16))
    fig.suptitle("Experiment 13 - Dynamic Excitation Modeling", fontsize=16, fontweight="bold")

    swap_labels = {"glass": "G", "mug": "M", "metal_bowl": "B", "wood": "W"}
    dominance_matrix = np.zeros((len(materials), len(materials)), dtype=float)
    best_match_matrix = np.empty((len(materials), len(materials)), dtype=object)
    pair_rows = []
    summary = {}
    report = []
    report.append("# Experiment 13: Dynamic Excitation Modeling Report")
    report.append("")
    report.append("This experiment treats the dynamic-model remainder from Experiment 12 as an excitation candidate.")
    report.append("It asks whether that remainder is compact, broadband, and rapidly decaying, and whether it recombines with dynamic resonators in a way that transfers identity.")
    report.append("")

    for row_idx, source in enumerate(materials):
        source_original = original_by_material[source]
        source_model = dynamic_models[source]["dynamic_model"]
        excitation = dynamic_models[source]["residual"]

        excitation_stats = residual_metrics(excitation, fs)
        model_stats = spectrum_features(source_model, fs)
        excitation_spec = spectrum_features(excitation, fs)

        recombined = source_model + excitation
        recombined_rms, recombined_snr = compute_rms_ratio(source_original, recombined)
        residual_rms, residual_snr = compute_rms_ratio(source_original, source_model)

        spectral_flatness_delta = excitation_spec["spectral_flatness"] - model_stats["spectral_flatness"]
        excitation_like = excitation_spec["spectral_flatness"] > model_stats["spectral_flatness"]

        summary[source] = {
            "onset_idx": int(detect_onset(load_material_signal(source)[1])),
            "mode_count": int(dynamic_models[source]["mode_count"]),
            "excitation": excitation_stats,
            "excitation_spectrum": {
                "spectral_flatness": excitation_spec["spectral_flatness"],
                "spectral_centroid_hz": excitation_spec["spectral_centroid_hz"],
                "spectral_rolloff_85_hz": excitation_spec["spectral_rolloff_85_hz"],
                "band_energy_fractions": excitation_spec["band_energy_fractions"],
                "peaks": excitation_spec["peaks"],
            },
            "dynamic_model_spectrum": {
                "spectral_flatness": model_stats["spectral_flatness"],
                "spectral_centroid_hz": model_stats["spectral_centroid_hz"],
                "spectral_rolloff_85_hz": model_stats["spectral_rolloff_85_hz"],
                "band_energy_fractions": model_stats["band_energy_fractions"],
                "peaks": model_stats["peaks"],
            },
            "recombined_rms_ratio": recombined_rms,
            "recombined_snr_db": recombined_snr,
            "dynamic_model_rms_ratio": residual_rms,
            "dynamic_model_snr_db": residual_snr,
            "spectral_flatness_delta": spectral_flatness_delta,
            "excitation_like": excitation_like,
        }

        report.append(f"## {source.replace('_', ' ').title()}")
        report.append(f"Excitation candidate is the dynamic residual from Experiment 12.")
        report.append(f"First 10 ms energy: **{excitation_stats['first_10ms_energy_fraction']:.2%}**")
        report.append(f"First 5 ms energy: **{excitation_stats['first_5ms_energy_fraction']:.2%}**")
        report.append(f"Residual decay rate: **{excitation_stats['decay_rate_1_s']:.2f} 1/s** (half-life {excitation_stats['half_life_ms']:.2f} ms)")
        report.append(f"Spectral flatness vs dynamic model: **{excitation_spec['spectral_flatness']:.3e} vs {model_stats['spectral_flatness']:.3e}**")
        report.append(f"Transient sharpness (crest factor): **{excitation_stats['crest_factor']:.2f}**")
        report.append(f"Early sharpness (peak/mean abs over first 10 ms): **{excitation_stats['early_peak_to_mean_abs']:.2f}**")
        report.append(f"Recombination self-error: **{recombined_rms:.2%}**")
        report.append(f"Residual-only RMS of dynamic model: **{residual_rms:.2%}**")
        report.append("")

        if excitation_stats["first_10ms_energy_fraction"] >= 0.50 and excitation_stats["decay_rate_1_s"] >= 30.0:
            verdict = "Excitation candidate is short and rapidly disappearing."
        elif excitation_spec["spectral_flatness"] > model_stats["spectral_flatness"]:
            verdict = "Excitation candidate is flatter than the dynamic modal remainder and behaves like a strike impulse."
        else:
            verdict = "Excitation candidate still contains tonal structure and is not fully compact."

        report.append(f"Verdict: {verdict}")
        report.append("")

        print(
            f"{source}: 10ms energy={excitation_stats['first_10ms_energy_fraction']:.2%}, "
            f"flatness={excitation_spec['spectral_flatness']:.3e}, sharpness={excitation_stats['crest_factor']:.2f}"
        )

        ax_wave = axes[row_idx, 0]
        ax_energy = axes[row_idx, 1]
        ax_spec = axes[row_idx, 2]

        plot_samples = min(len(source_original), int(0.03 * fs))
        t_plot = np.arange(plot_samples) / fs * 1000.0
        ax_wave.plot(t_plot, excitation[:plot_samples], color="tab:red", linewidth=1.1, label="Excitation candidate")
        ax_wave.plot(t_plot, source_model[:plot_samples], color="tab:green", linewidth=1.0, alpha=0.9, label="Dynamic resonator")
        ax_wave.set_title(f"{source.replace('_', ' ').title()} - Excitation vs Resonator")
        ax_wave.set_ylabel("Amplitude")
        ax_wave.grid(True, alpha=0.2)
        ax_wave.legend(fontsize=8, loc="upper right")

        energy = excitation**2
        cumulative = np.cumsum(energy) / (np.sum(energy) + 1e-12)
        t_energy = np.arange(len(excitation)) / fs * 1000.0
        ax_energy.plot(t_energy, cumulative, color="tab:purple", linewidth=1.2, label="Cumulative energy")
        ax_energy.axvline(10.0, color="gray", linestyle="--", alpha=0.6, label="10 ms")
        ax_energy.set_ylim(0.0, 1.02)
        ax_energy.set_title(f"{source.replace('_', ' ').title()} - Excitation Energy")
        ax_energy.set_xlabel("Time from Onset (ms)")
        ax_energy.set_ylabel("Cumulative Energy")
        ax_energy.grid(True, alpha=0.2)
        ax_energy.legend(fontsize=8, loc="lower right")

        ax_spec.semilogy(excitation_spec["freqs"], excitation_spec["psd"], color="tab:red", linewidth=1.0, label=f"Excitation flatness={excitation_spec['spectral_flatness']:.2e}")
        ax_spec.semilogy(model_stats["freqs"], model_stats["psd"], color="tab:green", linewidth=1.0, alpha=0.9, label=f"Resonator flatness={model_stats['spectral_flatness']:.2e}")
        ax_spec.set_xlim(0.0, min(fs / 2.0, 8000.0))
        ax_spec.set_title(f"{source.replace('_', ' ').title()} - Spectral Comparison")
        ax_spec.set_xlabel("Frequency (Hz)")
        ax_spec.set_ylabel("PSD")
        ax_spec.grid(True, alpha=0.2)
        ax_spec.legend(fontsize=7, loc="best")

    # Cross-swap analysis
    for i, source in enumerate(materials):
        excitation = dynamic_models[source]["residual"]
        for j, target in enumerate(materials):
            hybrid = excitation + dynamic_models[target]["dynamic_model"]
            source_error, _ = compute_rms_ratio(original_by_material[source], hybrid)
            target_error, _ = compute_rms_ratio(original_by_material[target], hybrid)
            dominance = source_error - target_error
            dominance_matrix[i, j] = dominance
            best_label, score_map = best_match_label(hybrid, original_by_material)
            best_match_matrix[i, j] = best_label
            pair_rows.append(
                {
                    "excitation_source": source,
                    "resonator_target": target,
                    "source_rms_ratio": source_error,
                    "target_rms_ratio": target_error,
                    "dominance_score": dominance,
                    "best_match": best_label,
                    "score_map": score_map,
                }
            )

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    plot_path = results_dir / "13_dynamic_excitation_modeling.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()

    heatmap_fig, heatmap_ax = plt.subplots(figsize=(8, 7))
    im = heatmap_ax.imshow(dominance_matrix, cmap="coolwarm", aspect="auto")
    heatmap_ax.set_xticks(range(len(materials)))
    heatmap_ax.set_yticks(range(len(materials)))
    heatmap_ax.set_xticklabels([m.replace("_", " ").title() for m in materials])
    heatmap_ax.set_yticklabels([m.replace("_", " ").title() for m in materials])
    heatmap_ax.set_xlabel("Dynamic Resonator Target")
    heatmap_ax.set_ylabel("Excitation Source")
    heatmap_ax.set_title("Experiment 13 - Swap Dominance (positive = target resonator dominates)")
    for i in range(len(materials)):
        for j in range(len(materials)):
            heatmap_ax.text(j, i, swap_labels.get(best_match_matrix[i, j], best_match_matrix[i, j][0].upper()), ha="center", va="center", color="black", fontsize=10, fontweight="bold")
    heatmap_fig.colorbar(im, ax=heatmap_ax, label="RMS(source) - RMS(target)")
    heatmap_path = results_dir / "13_dynamic_excitation_modeling_swap_heatmap.png"
    heatmap_fig.tight_layout()
    heatmap_fig.savefig(heatmap_path, dpi=150)
    plt.close(heatmap_fig)

    off_diagonal = [row for row in pair_rows if row["excitation_source"] != row["resonator_target"]]
    target_dominant_count = sum(1 for row in off_diagonal if row["dominance_score"] > 0.0)
    total_off_diagonal = max(1, len(off_diagonal))
    target_dominance_rate = target_dominant_count / total_off_diagonal

    report.append("## Cross-Swap Analysis")
    report.append("")
    report.append("For each source excitation and resonator target, we form a hybrid: excitation_source + resonator_target.")
    report.append("We then ask whether the hybrid is closer to the source identity or the target identity.")
    report.append("")
    report.append(f"Off-diagonal hybrids that are closer to the target resonator: **{target_dominant_count}/{total_off_diagonal}** ({target_dominance_rate:.2%})")
    report.append("")
    report.append("| Excitation Source | Resonator Target | Source RMS | Target RMS | Dominance Score | Best Match |")
    report.append("| :--- | :--- | :---: | :---: | :---: | :--- |")
    for row in pair_rows:
        report.append(
            f"| {row['excitation_source'].replace('_', ' ').title()} | {row['resonator_target'].replace('_', ' ').title()} | {row['source_rms_ratio']:.2%} | {row['target_rms_ratio']:.2%} | {row['dominance_score']:.3f} | {row['best_match'].replace('_', ' ').title()} |"
        )
    report.append("")
    report.append("## Scientific Interpretation")
    report.append("")
    report.append("The excitation candidate is the dynamic residual after the time-varying modal model has been removed.")
    report.append("If that residual is compact in time and flatter in spectrum than the resonator, it is behaving like a strike excitation rather than another hidden mode set.")
    report.append("The swap matrix tests whether excitation and resonator identities can be recombined and transferred across materials.")
    report.append("")
    report.append("### Conclusion")
    report.append("> [!IMPORTANT]")
    report.append("> **Experiment 13 asks whether the dynamic-model remainder can be interpreted as a meaningful excitation signal. If the residual is short, broadband, and the cross-swaps tend to preserve resonator identity, the project has isolated the two key physical components of impact synthesis: strike and object.**")

    report_path = results_dir / "13_dynamic_excitation_modeling_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))

    json_path = results_dir / "13_dynamic_excitation_modeling.json"
    with open(json_path, "w") as f:
        json.dump(
            {
                "materials": summary,
                "pairwise_swaps": pair_rows,
                "target_dominance_rate": target_dominance_rate,
                "target_dominant_count": target_dominant_count,
                "off_diagonal_pairs": total_off_diagonal,
            },
            f,
            indent=2,
        )

    print(f"Saved dynamic excitation plot to: {plot_path}")
    print(f"Saved swap heatmap to: {heatmap_path}")
    print(f"Saved excitation summary to: {json_path}")
    print(f"Saved report to: {report_path}")


if __name__ == "__main__":
    main()