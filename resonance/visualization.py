from __future__ import annotations

from pathlib import Path
import numpy as np

try:
    import matplotlib.pyplot as plt
    import scipy.signal as signal
except ImportError:
    # Will be handled gracefully in main scripts
    pass


def plot_reconstruction_dashboard(
    orig: np.ndarray,
    recon: np.ndarray,
    fs: int,
    title: str,
    save_path: Path | str
) -> None:
    """Generates a premium diagnostic dashboard comparing original vs. resynthesized signals."""
    t = np.arange(len(orig)) / fs

    # Compute error signal
    error = orig - recon
    rms_orig = np.sqrt(np.mean(orig**2))
    rms_error = np.sqrt(np.mean(error**2))
    rms_ratio = rms_error / rms_orig if rms_orig > 0 else 0.0
    snr_db = 20 * np.log10(rms_orig / (rms_error + 1e-12)) if rms_error > 0 else float('inf')

    # Instantaneous squared error smoothed with a 10ms moving average
    win_len = int(0.01 * fs)
    squared_err_smooth = np.convolve(error**2, np.ones(win_len)/win_len, mode='same')
    # Convert to dB relative to peak original power
    ref_power = np.max(orig**2) + 1e-12
    db_err = 10 * np.log10(squared_err_smooth / ref_power + 1e-10)

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle(f"Resynthesis Dashboard - {title}\n(Reconstruction Error RMS Ratio: {rms_ratio:.2%}, SNR: {snr_db:.2f} dB)", fontsize=14, fontweight="bold")

    # Plot 1: Waveforms
    axes[0].plot(t, orig, label="Original", color="#1d3557", alpha=0.8, linewidth=1.0)
    axes[0].plot(t, recon, label="Reconstructed", color="#e63946", alpha=0.7, linewidth=1.0, linestyle="--")
    axes[0].set_title("Waveform Comparison", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Amplitude")
    axes[0].set_xlabel("Time (s)")
    axes[0].grid(True, alpha=0.15)
    axes[0].legend(loc="upper right")

    # Plot 2: Spectrograms Comparison
    # We display the spectrogram of original and reconstructed stacked or side-by-side. 
    # Since we have 3 subplots vertically, let's plot the spectrogram of the original 
    # and the error energy together, or compute a dual spectrogram plot.
    # To keep the layout clean, let's plot the original spectrogram in axes[1]
    # and overlay reconstructed peak frequencies as vertical dashes or markers.
    f, t_spec, Sxx = signal.spectrogram(orig, fs=fs, nperseg=1024, noverlap=512)
    Sxx_db = 10 * np.log10(Sxx + 1e-10)
    im = axes[1].pcolormesh(t_spec, f, Sxx_db, shading='gouraud', cmap='magma')
    axes[1].set_title("Original Spectrogram", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Frequency (Hz)")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylim(0, 8000)  # Focus on the audible modal region
    fig.colorbar(im, ax=axes[1], label="Power (dB)")

    # Plot 3: Time-varying Error Power (dB)
    axes[2].plot(t, db_err, label="Smoothed Error Power", color="#e07a5f", linewidth=1.5)
    axes[2].axhline(-20, color='red', linestyle=':', label="-20 dB (High Error)", alpha=0.5)
    axes[2].axhline(-40, color='green', linestyle=':', label="-40 dB (Low Error)", alpha=0.5)
    axes[2].set_title("Time-Varying Reconstruction Error Power", fontsize=11, fontweight="bold")
    axes[2].set_ylabel("Error Power (dB)")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylim(-100, 10)
    axes[2].grid(True, alpha=0.15)
    axes[2].legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
