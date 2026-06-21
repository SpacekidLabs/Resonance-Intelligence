"""
Resonance Intelligence - Experiment 04: Raw Frequency Estimate Diagnostics
This script performs a 7-observer sweep on the 4 real sounds, prints the raw
mode frequencies extracted by each observer, and performs a relaxed clustering
analysis to inspect whether observers are close but missed by the tight 1.5%
tolerance, or if they fundamentally disagree.
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from resonance.extraction import (
    FourierObserver,
    FilterbankObserver,
    LpcObserver,
    PronyObserver,
    MatrixPencilObserver,
    AutocorrelationObserver,
    WaveletObserver
)

SAMPLE_RATE = 44_100

def run_diagnostic_sweep(sig: np.ndarray, fs: int = 44_100) -> tuple[dict[str, list[float]], list[dict]]:
    observers = {
        "STFT": FourierObserver(fs=fs),
        "Filterbank": FilterbankObserver(fs=fs),
        "LPC": LpcObserver(fs=fs),
        "Prony": PronyObserver(fs=fs),
        "Matrix Pencil": MatrixPencilObserver(fs=fs),
        "Autocorrelation": AutocorrelationObserver(fs=fs),
        "Wavelet": WaveletObserver(fs=fs),
    }

    raw_by_observer = {}
    all_candidates = []

    for name, obs in observers.items():
        try:
            modes = obs.extract_modes(sig, max_modes=12)
            freqs = [float(m.frequency) for m in modes.modes]
            raw_by_observer[name] = freqs
            for m in modes.modes:
                all_candidates.append({
                    "frequency": m.frequency,
                    "amplitude": m.amplitude,
                    "decay_rate": m.decay_rate,
                    "observer": name
                })
        except Exception as e:
            raw_by_observer[name] = []
            print(f"  Observer {name} failed: {e}")

    if not all_candidates:
        return raw_by_observer, []

    # Relaxed clustering with 10.0% frequency tolerance to group potentially related modes
    freqs = np.array([c["frequency"] for c in all_candidates])
    n_c = len(freqs)
    
    if n_c == 1:
        c = all_candidates[0]
        return raw_by_observer, [{
            "mean_frequency": c["frequency"],
            "candidates": [c]
        }]

    dist_matrix = np.zeros((n_c, n_c))
    for i in range(n_c):
        for j in range(n_c):
            mean_f = (freqs[i] + freqs[j]) / 2.0
            dist_matrix[i, j] = (abs(freqs[i] - freqs[j]) / mean_f * 100.0) if mean_f > 0 else 0.0

    condensed_dist = squareform(dist_matrix)
    Z = sch.linkage(condensed_dist, method='complete')
    # Use 10% threshold to see what falls into the same group
    labels = sch.fcluster(Z, t=10.0, criterion='distance')

    clusters = []
    unique_labels = np.unique(labels)
    for label in unique_labels:
        mask = labels == label
        cluster_candidates = [all_candidates[idx] for idx in range(n_c) if mask[idx]]
        mean_freq = float(np.mean([c["frequency"] for c in cluster_candidates]))
        clusters.append({
            "mean_frequency": mean_freq,
            "candidates": cluster_candidates
        })

    # Sort clusters by mean frequency
    clusters.sort(key=lambda x: x["mean_frequency"])
    return raw_by_observer, clusters

def main() -> None:
    test_sounds_dir = PROJECT_ROOT / "experiments" / "test_sounds"
    results_dir = PROJECT_ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    materials = ["glass", "mug", "metal_bowl", "wood"]
    
    report = []
    report.append("# Experiment 04: Raw Frequency Estimate Diagnostics")
    report.append("This report examines the raw frequency estimates of all 7 observers to diagnose whether ")
    report.append("low observer agreement is due to a tight clustering threshold (clustering is wrong) ")
    report.append("or whether the observers fundamentally disagree on the resonance frequencies.")
    report.append("")

    for mat in materials:
        wav_path = test_sounds_dir / f"{mat}.wav"
        if not wav_path.exists():
            print(f"Error: WAV file '{wav_path}' not found.")
            sys.exit(1)
            
        fs, sig_int = wavfile.read(wav_path)
        sig = sig_int.astype(np.float32) / 32767.0
        if len(sig.shape) > 1:
            sig = np.mean(sig, axis=1)
            
        print(f"Analyzing {mat}...")
        raw_by_obs, clusters = run_diagnostic_sweep(sig, fs=fs)
        
        report.append(f"## Material: {mat.replace('_', ' ').title()}")
        report.append("")
        report.append("### 1. Raw Detections by Observer")
        report.append("| Observer | Detected Frequencies (Hz) |")
        report.append("| :--- | :--- |")
        for obs_name in sorted(raw_by_obs.keys()):
            freqs_str = ", ".join([f"{f:.1f}" for f in sorted(raw_by_obs[obs_name])])
            report.append(f"| {obs_name} | {freqs_str if freqs_str else 'None'} |")
        report.append("")
        
        report.append("### 2. Relaxed Cluster Candidates (10% Tolerance)")
        report.append("We grouped raw detections using complete-linkage clustering with a 10% frequency tolerance ")
        report.append("to check for close matches. Below are the grouped candidates:")
        report.append("")
        report.append("| Cluster Mean (Hz) | STFT | Filterbank | LPC | Prony | Matrix Pencil | Autocorrelation | Wavelet |")
        report.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        
        # Display clusters that have candidates from at least 1 observer
        for c in clusters:
            # Map observer name to its closest candidate inside this cluster
            obs_map = {obs: "-" for obs in ["STFT", "Filterbank", "LPC", "Prony", "Matrix Pencil", "Autocorrelation", "Wavelet"]}
            for cand in c["candidates"]:
                obs_name = cand["observer"]
                freq_val = f"{cand['frequency']:.1f} Hz"
                if obs_map[obs_name] == "-":
                    obs_map[obs_name] = freq_val
                else:
                    # Append if multiple candidates from same observer fell in this relaxed cluster
                    obs_map[obs_name] += f"<br>{freq_val}"
            
            row = (
                f"| **{c['mean_frequency']:.1f}** | "
                f"{obs_map['STFT']} | "
                f"{obs_map['Filterbank']} | "
                f"{obs_map['LPC']} | "
                f"{obs_map['Prony']} | "
                f"{obs_map['Matrix Pencil']} | "
                f"{obs_map['Autocorrelation']} | "
                f"{obs_map['Wavelet']} |"
            )
            report.append(row)
        report.append("")
        report.append("---")
        report.append("")

    report_path = results_dir / "04_raw_frequency_diagnostics.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))
        
    print(f"Saved diagnostic report to: {report_path}")

if __name__ == "__main__":
    main()
