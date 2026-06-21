"""
Resonance Intelligence - Experiment 01: Modal Extraction

This script extracts dominant resonances (frequency, initial amplitude, decay rate)
from recorded impact sounds of four different materials (glass, ceramic mug, metal bowl,
and wood). It runs both the Fourier Observer (STFT-based) and the Filterbank Observer
(IIR bandpass resonator-based) to verify modal parameters and measure observer agreement.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import numpy as np
import scipy.io.wavfile as wavfile

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from resonance.extraction import FourierObserver, FilterbankObserver, compare_observers
from resonance.modal import ModeList

SAMPLE_RATE = 44_100
DURATION = 2.5


def synthesize_material_impact(material: str, duration: float, fs: int = SAMPLE_RATE) -> np.ndarray:
    """Synthesizes a high-fidelity physical model impact sound for reference testing."""
    t = np.arange(int(duration * fs)) / fs
    sig = np.zeros_like(t)
    rng = np.random.default_rng(123)

    # Material-specific modal configurations
    if material == "glass":
        # High frequencies, low damping (medium-long ring)
        freqs = [1560.0, 2240.0, 3110.0, 4480.0]
        amps = [1.0, 0.6, 0.35, 0.15]
        decays = [7.0, 10.0, 14.0, 22.0]
    elif material == "mug":
        # Mid-high frequencies, moderate damping (medium ring)
        freqs = [820.0, 1340.0, 2080.0, 2920.0]
        amps = [0.9, 0.65, 0.4, 0.2]
        decays = [14.0, 20.0, 28.0, 40.0]
    elif material == "metal_bowl":
        # Mid frequencies, extremely low damping (very long ring)
        freqs = [440.0, 650.0, 940.0, 1370.0]
        amps = [1.0, 0.8, 0.55, 0.3]
        decays = [1.5, 2.8, 4.2, 6.5]
    elif material == "wood":
        # Low-mid frequencies, extremely high damping (very brief click)
        freqs = [180.0, 380.0, 620.0, 940.0]
        amps = [1.0, 0.45, 0.25, 0.08]
        decays = [48.0, 65.0, 85.0, 115.0]
    else:
        raise ValueError(f"Unknown material: {material}")

    # Add modal ringing
    for f, a, d in zip(freqs, amps, decays):
        phase = rng.uniform(0, 2 * np.pi)
        sig += a * np.exp(-d * t) * np.sin(2 * np.pi * f * t + phase)

    # Add brief onset noise burst to simulate striker contact
    burst_len = int(0.005 * fs)  # 5ms burst
    hann_win = np.hanning(burst_len * 2)[burst_len:]  # decay half
    noise = rng.normal(0, 0.1, burst_len) * hann_win
    sig[:burst_len] += noise

    # Normalize
    max_val = np.max(np.abs(sig))
    if max_val > 0:
        sig = sig / max_val * 0.9

    return sig


def main() -> None:
    # Setup directories
    test_sounds_dir = PROJECT_ROOT / "experiments" / "test_sounds"
    results_dir = PROJECT_ROOT / "experiments" / "results"
    test_sounds_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    materials = ["glass", "mug", "metal_bowl", "wood"]
    audio_paths = {}

    # Step 1: Ensure test wav files exist
    print("Step 1: Checking for test impact sounds...")
    for mat in materials:
        wav_path = test_sounds_dir / f"{mat}.wav"
        if not wav_path.exists():
            print(f"  Generating synthetic impact sound for '{mat}'...")
            sig = synthesize_material_impact(mat, DURATION, SAMPLE_RATE)
            # Write as 16-bit PCM wav file
            sig_int = (sig * 32767).astype(np.int16)
            wavfile.write(wav_path, SAMPLE_RATE, sig_int)
        audio_paths[mat] = wav_path

    # Step 2: Initialize Observers
    print("\nStep 2: Initializing Observers...")
    fourier_obs = FourierObserver(fs=SAMPLE_RATE)
    filterbank_obs = FilterbankObserver(fs=SAMPLE_RATE)

    all_results = {}

    # Step 3: Run Extraction on each material
    print("\nStep 3: Running Modal Extraction Sweep...")
    for mat in materials:
        print(f"\nAnalyzing sound: '{mat}'")
        fs, sig_int = wavfile.read(audio_paths[mat])
        sig = sig_int.astype(np.float32) / 32767.0
        if len(sig.shape) > 1:
            sig = np.mean(sig, axis=1)

        # Fourier Observer Extraction
        modes_fourier = fourier_obs.extract_modes(sig, max_modes=8)
        print(f"  [Fourier] Extracted {len(modes_fourier)} modes.")

        # Filterbank Observer Extraction
        modes_filterbank = filterbank_obs.extract_modes(sig, max_modes=8)
        print(f"  [Filterbank] Extracted {len(modes_filterbank)} modes.")

        # Compare observers
        comparison = compare_observers(modes_fourier, modes_filterbank)
        agreement = comparison["agreement_rate"]
        print(f"  Observer Agreement: {agreement:.2%} ({len(comparison['confirmed'])} Confirmed, {len(comparison['fragile'])} Fragile)")

        # Save results for JSON export
        all_results[mat] = {
            "fourier_modes": modes_fourier.to_list_of_dicts(),
            "filterbank_modes": modes_filterbank.to_list_of_dicts(),
            "agreement_rate": agreement,
            "confirmed_modes": comparison["confirmed"],
            "fragile_modes": comparison["fragile"],
            "fourier_only": comparison["fourier_only"],
            "filterbank_only": comparison["filterbank_only"]
        }

    # Step 4: Export to JSON
    json_path = results_dir / "01_modes.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nStep 4: Exported modal extraction results to: {json_path}")


if __name__ == "__main__":
    main()
