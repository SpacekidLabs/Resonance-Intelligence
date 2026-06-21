from __future__ import annotations

import numpy as np
import scipy.signal as signal
from resonance.modal import Mode, ModeList


class FourierObserver:
    def __init__(self, fs: int = 44_100, nfft: int = 2048, hop_length: int = 512) -> None:
        self.fs = fs
        self.nfft = nfft
        self.hop_length = hop_length

    def extract_modes(self, sig: np.ndarray, max_modes: int = 12, min_distance_hz: float = 30.0) -> ModeList:
        """Extracts modes using STFT peak-picking and log-linear regression decay fitting."""
        # 1. Compute STFT
        f, t, Zxx = signal.stft(
            sig, 
            fs=self.fs, 
            nperseg=self.nfft, 
            noverlap=self.nfft - self.hop_length
        )
        mag = np.abs(Zxx)  # shape (n_freqs, n_frames)

        # 2. Average spectrum over the first 10 frames (approx 100ms) to locate initial peaks
        initial_mag = np.mean(mag[:, :10], axis=1)

        # Ensure minimum bin distance
        bin_resolution = self.fs / self.nfft
        min_dist_bins = max(1, int(min_distance_hz / bin_resolution))

        peaks, _ = signal.find_peaks(
            initial_mag,
            prominence=0.005 * np.max(initial_mag),
            distance=min_dist_bins
        )

        if len(peaks) == 0:
            return ModeList()

        # Sort peaks by initial amplitude
        peak_amps = initial_mag[peaks]
        sorted_indices = np.argsort(peak_amps)[::-1][:max_modes]
        peaks = peaks[sorted_indices]

        modes = ModeList()

        # 3. Fit exponential decay for each peak frequency
        for p in peaks:
            freq_hz = float(f[p])
            env = mag[p, :]  # amplitude envelope at this bin

            # Find where decay starts (peak envelope frame)
            max_idx = np.argmax(env)
            peak_val = env[max_idx]
            if peak_val == 0:
                continue

            # Set threshold to -40dB from peak
            threshold = peak_val * 0.01

            # Identify decay frames
            decay_frames = []
            for frame_idx in range(max_idx, len(env)):
                if env[frame_idx] >= threshold:
                    decay_frames.append(frame_idx)
                else:
                    break

            if len(decay_frames) < 5:
                continue

            t_decay = t[decay_frames] - t[max_idx]
            env_decay = env[decay_frames]

            # Fit log-linear: ln(env) = ln(A0) - d * t
            y = np.log(env_decay + 1e-12)
            slope, intercept = np.polyfit(t_decay, y, 1)

            decay_rate = -slope
            amp_est = np.exp(intercept)

            # Floor decay rate to avoid negative or near-zero rates
            if decay_rate < 0.05:
                decay_rate = 0.05

            modes.add(Mode(
                frequency=freq_hz,
                amplitude=float(amp_est),
                decay_rate=float(decay_rate)
            ))

        modes.sort(by="amplitude")
        return modes


class FilterbankObserver:
    def __init__(self, fs: int = 44_100, nfft: int = 2048) -> None:
        self.fs = fs
        self.nfft = nfft

    def extract_modes(self, sig: np.ndarray, max_modes: int = 12, min_distance_hz: float = 30.0) -> ModeList:
        """Extracts modes by first finding candidate peaks, then designing tuned IIR resonators."""
        # 1. Identify candidate frequencies using an FFT magnitude spectrum
        spec = np.abs(np.fft.rfft(sig))
        freqs = np.fft.rfftfreq(len(sig), d=1/self.fs)

        # Smooth spectrum to find robust peaks
        smoothed = np.convolve(spec, np.ones(5)/5, mode='same')
        min_dist_bins = max(1, int(min_distance_hz / (self.fs / len(sig))))

        peaks, _ = signal.find_peaks(
            smoothed,
            prominence=0.005 * np.max(smoothed),
            distance=min_dist_bins
        )

        if len(peaks) == 0:
            return ModeList()

        peak_amps = smoothed[peaks]
        sorted_indices = np.argsort(peak_amps)[::-1][:max_modes]
        peaks = peaks[sorted_indices]
        candidate_freqs = freqs[peaks]

        # 2. Design bandpass resonators and fit decay curves
        modes = ModeList()
        t = np.arange(len(sig)) / self.fs
        bandwidth = 15.0  # Narrow resonator bandwidth in Hz

        for fc in candidate_freqs:
            if fc <= bandwidth:
                continue

            # Second-order IIR bandpass resonator coefficients
            r = np.exp(-np.pi * bandwidth / self.fs)
            theta = 2.0 * np.pi * fc / self.fs
            a1 = -2.0 * r * np.cos(theta)
            a2 = r**2
            b0 = 1.0 - r
            
            # Filter time-domain signal
            filtered = signal.lfilter([b0], [1.0, a1, a2], sig)

            # Extract Hilbert amplitude envelope
            analytic = signal.hilbert(filtered)
            env = np.abs(analytic)

            # Find decay region
            max_idx = np.argmax(env)
            peak_val = env[max_idx]
            if peak_val == 0:
                continue

            threshold = peak_val * 0.01
            decay_indices = []
            for idx in range(max_idx, len(env)):
                if env[idx] >= threshold:
                    decay_indices.append(idx)
                else:
                    break

            if len(decay_indices) < 200:
                continue

            t_decay = t[decay_indices] - t[max_idx]
            env_decay = env[decay_indices]

            # Fit decay rate
            y = np.log(env_decay + 1e-12)
            slope, intercept = np.polyfit(t_decay, y, 1)

            decay_rate = -slope
            amp_est = np.exp(intercept)

            if decay_rate < 0.05:
                decay_rate = 0.05

            modes.add(Mode(
                frequency=float(fc),
                amplitude=float(amp_est),
                decay_rate=float(decay_rate)
            ))

        modes.sort(by="amplitude")
        return modes


def compare_observers(
    fourier_modes: ModeList, 
    filterbank_modes: ModeList, 
    freq_tol_percent: float = 1.5,
    decay_tol_percent: float = 20.0
) -> dict:
    """Compares Fourier and Filterbank mode lists to measure agreement and flag artifacts."""
    confirmed = []
    fragile = []
    fourier_unmatched = list(fourier_modes.modes)
    filterbank_unmatched = list(filterbank_modes.modes)

    comparison_results = {
        "agreement_rate": 0.0,
        "confirmed": [],
        "fragile": [],
        "fourier_only": [],
        "filterbank_only": []
    }

    # Match modes by frequency proximity
    for f_mode in fourier_modes.modes:
        best_match = None
        min_freq_diff = float('inf')

        for fb_mode in filterbank_unmatched:
            freq_diff = abs(f_mode.frequency - fb_mode.frequency)
            mean_freq = (f_mode.frequency + fb_mode.frequency) / 2.0
            percent_diff = (freq_diff / mean_freq) * 100.0

            if percent_diff <= freq_tol_percent and percent_diff < min_freq_diff:
                min_freq_diff = percent_diff
                best_match = fb_mode

        if best_match is not None:
            # We found a match! Remove from unmatched lists
            fourier_unmatched.remove(f_mode)
            filterbank_unmatched.remove(best_match)

            decay_diff = abs(f_mode.decay_rate - best_match.decay_rate)
            mean_decay = (f_mode.decay_rate + best_match.decay_rate) / 2.0
            decay_percent_diff = (decay_diff / mean_decay) * 100.0 if mean_decay > 0 else 0.0

            match_data = {
                "frequency_fourier": f_mode.frequency,
                "frequency_filterbank": best_match.frequency,
                "frequency_error_percent": min_freq_diff,
                "amplitude_fourier": f_mode.amplitude,
                "amplitude_filterbank": best_match.amplitude,
                "decay_fourier": f_mode.decay_rate,
                "decay_filterbank": best_match.decay_rate,
                "decay_error_percent": decay_percent_diff
            }

            if decay_percent_diff <= decay_tol_percent:
                confirmed.append(match_data)
            else:
                fragile.append(match_data)

    comparison_results["confirmed"] = confirmed
    comparison_results["fragile"] = fragile
    comparison_results["fourier_only"] = [m.to_dict() for m in fourier_unmatched]
    comparison_results["filterbank_only"] = [m.to_dict() for m in filterbank_unmatched]

    total_modes = len(fourier_modes) + len(filterbank_modes)
    if total_modes > 0:
        agreement_rate = (2 * len(confirmed)) / total_modes
        comparison_results["agreement_rate"] = float(agreement_rate)

    return comparison_results
