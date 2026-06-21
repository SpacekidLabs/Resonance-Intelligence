from __future__ import annotations

import numpy as np
import scipy.signal as signal
import scipy.linalg as linalg
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform
from resonance.modal import Mode, ModeList


def detect_onset(sig: np.ndarray, threshold: float = 0.005) -> int:
    """Helper function to locate the starting sample of the transient/onset."""
    indices = np.where(np.abs(sig) > threshold)[0]
    return int(indices[0]) if len(indices) > 0 else 0


def estimate_amplitude_filterbank(sig: np.ndarray, fc: float, fs: int, bandwidth: float = 15.0) -> float:
    """Helper function to filter the signal at a frequency and measure peak envelope amplitude."""
    if fc <= bandwidth or fc >= fs / 2.0 - bandwidth:
        return 0.0
    # Second-order IIR bandpass resonator filter coefficients
    r = np.exp(-np.pi * bandwidth / fs)
    theta = 2.0 * np.pi * fc / fs
    a1 = -2.0 * r * np.cos(theta)
    a2 = r**2
    b0 = 1.0 - r
    
    filtered = signal.lfilter([b0], [1.0, a1, a2], sig)
    analytic = signal.hilbert(filtered)
    env = np.abs(analytic)
    return float(np.max(env))


class FourierObserver:
    def __init__(self, fs: int = 44_100, nfft: int = 2048, hop_length: int = 512) -> None:
        self.fs = fs
        self.nfft = nfft
        self.hop_length = hop_length

    def extract_modes(self, sig: np.ndarray, max_modes: int = 12, min_distance_hz: float = 30.0) -> ModeList:
        """Extracts modes using STFT peak-picking and log-linear regression decay fitting."""
        f, t, Zxx = signal.stft(
            sig, 
            fs=self.fs, 
            nperseg=self.nfft, 
            noverlap=self.nfft - self.hop_length
        )
        mag = np.abs(Zxx)  # shape (n_freqs, n_frames)

        # Average spectrum over the first 10 frames to locate initial peaks
        initial_mag = np.mean(mag[:, :min(10, mag.shape[1])], axis=1)

        bin_resolution = self.fs / self.nfft
        min_dist_bins = max(1, int(min_distance_hz / bin_resolution))

        peaks, _ = signal.find_peaks(
            initial_mag,
            prominence=0.005 * np.max(initial_mag),
            distance=min_dist_bins
        )

        if len(peaks) == 0:
            return ModeList()

        peak_amps = initial_mag[peaks]
        sorted_indices = np.argsort(peak_amps)[::-1][:max_modes]
        peaks = peaks[sorted_indices]

        modes = ModeList()

        for p in peaks:
            freq_hz = float(f[p])
            env = mag[p, :]

            max_idx = np.argmax(env)
            peak_val = env[max_idx]
            if peak_val == 0:
                continue

            threshold = peak_val * 0.01
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

            y = np.log(env_decay + 1e-12)
            slope, intercept = np.polyfit(t_decay, y, 1)

            decay_rate = -slope
            amp_est = np.exp(intercept)

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
        spec = np.abs(np.fft.rfft(sig))
        freqs = np.fft.rfftfreq(len(sig), d=1/self.fs)

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

        modes = ModeList()
        t = np.arange(len(sig)) / self.fs
        bandwidth = 15.0

        for fc in candidate_freqs:
            if fc <= bandwidth:
                continue

            r = np.exp(-np.pi * bandwidth / self.fs)
            theta = 2.0 * np.pi * fc / self.fs
            a1 = -2.0 * r * np.cos(theta)
            a2 = r**2
            b0 = 1.0 - r
            
            filtered = signal.lfilter([b0], [1.0, a1, a2], sig)
            analytic = signal.hilbert(filtered)
            env = np.abs(analytic)

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


class LpcObserver:
    def __init__(self, fs: int = 44_100, order: int = 24) -> None:
        self.fs = fs
        self.order = order

    def extract_modes(self, sig: np.ndarray, max_modes: int = 12) -> ModeList:
        """Extracts resonances by fitting an autoregressive model and solving for polynomial roots."""
        onset_idx = detect_onset(sig)
        N = min(2000, len(sig) - onset_idx)
        if N <= self.order:
            return ModeList()
        s_seg = sig[onset_idx : onset_idx + N]
        
        # Compute autocorrelation
        r = np.correlate(s_seg, s_seg, mode='full')[len(s_seg)-1:]
        
        # Solve Yule-Walker equations using Toeplitz solver
        a = linalg.solve_toeplitz((r[:-1], r[:-1]), -r[1:])
        
        # Polynomial root-finding
        roots = np.roots(np.r_[1.0, a])
        roots = roots[np.imag(roots) > 0]
        roots = roots[np.abs(roots) < 1.0]

        modes = ModeList()
        for root in roots:
            freq = np.angle(root) * self.fs / (2.0 * np.pi)
            decay = -np.log(np.abs(root)) * self.fs
            if decay < 0.05:
                decay = 0.05

            amp = estimate_amplitude_filterbank(sig, freq, self.fs)
            if amp > 1e-4:
                modes.add(Mode(
                    frequency=float(freq),
                    amplitude=float(amp),
                    decay_rate=float(decay)
                ))

        modes.sort(by="amplitude")
        return modes.limit(max_modes)


class PronyObserver:
    def __init__(self, fs: int = 44_100, order: int = 24) -> None:
        self.fs = fs
        self.order = order

    def extract_modes(self, sig: np.ndarray, max_modes: int = 12) -> ModeList:
        """Extracts resonances by solving the Prony characteristic equation for complex exponentials."""
        onset_idx = detect_onset(sig)
        N = min(2000, len(sig) - onset_idx)
        s_seg = sig[onset_idx : onset_idx + N]
        P = self.order
        
        if N <= P * 2:
            return ModeList()

        X = linalg.hankel(s_seg[:-P], s_seg[P-1:-1])
        X = X[:, ::-1]  # reverse columns
        y = s_seg[P:]
        
        # Solve least squares system
        a, _, _, _ = np.linalg.lstsq(X, -y, rcond=None)
        
        roots = np.roots(np.r_[1.0, a])
        roots = roots[np.imag(roots) > 0]
        roots = roots[np.abs(roots) < 1.0]

        modes = ModeList()
        for root in roots:
            freq = np.angle(root) * self.fs / (2.0 * np.pi)
            decay = -np.log(np.abs(root)) * self.fs
            if decay < 0.05:
                decay = 0.05

            amp = estimate_amplitude_filterbank(sig, freq, self.fs)
            if amp > 1e-4:
                modes.add(Mode(
                    frequency=float(freq),
                    amplitude=float(amp),
                    decay_rate=float(decay)
                ))

        modes.sort(by="amplitude")
        return modes.limit(max_modes)


class MatrixPencilObserver:
    def __init__(self, fs: int = 44_100, num_poles: int = 24) -> None:
        self.fs = fs
        self.num_poles = num_poles

    def extract_modes(self, sig: np.ndarray, max_modes: int = 12) -> ModeList:
        """Extracts resonances by singular value decomposition of the Hankel matrix (subspace method)."""
        onset_idx = detect_onset(sig)
        N = min(2000, len(sig) - onset_idx)
        s_seg = sig[onset_idx : onset_idx + N]
        L = N // 3
        
        if L < self.num_poles:
            return ModeList()

        # Construct Hankel matrix
        Y = linalg.hankel(s_seg[:N-L], s_seg[N-L-1:N-1])
        
        # Singular Value Decomposition
        U, S, Vh = np.linalg.svd(Y, full_matrices=False)
        V = Vh.T
        
        M = min(self.num_poles, L)
        V_truncated = V[:, :M]
        
        # Form shifts
        V0 = V_truncated[:-1, :]
        V1 = V_truncated[1:, :]
        
        # pseudo-inverse shift solver
        Z = linalg.pinv(V0) @ V1
        poles = linalg.eigvals(Z)
        
        poles = poles[np.imag(poles) > 0]
        poles = poles[np.abs(poles) < 1.0]

        modes = ModeList()
        for pole in poles:
            freq = np.angle(pole) * self.fs / (2.0 * np.pi)
            decay = -np.log(np.abs(pole)) * self.fs
            if decay < 0.05:
                decay = 0.05

            amp = estimate_amplitude_filterbank(sig, freq, self.fs)
            if amp > 1e-4:
                modes.add(Mode(
                    frequency=float(freq),
                    amplitude=float(amp),
                    decay_rate=float(decay)
                ))

        modes.sort(by="amplitude")
        return modes.limit(max_modes)


class AutocorrelationObserver:
    def __init__(self, fs: int = 44_100, min_freq: float = 80.0, max_freq: float = 4000.0) -> None:
        self.fs = fs
        self.min_freq = min_freq
        self.max_freq = max_freq

    def extract_modes(self, sig: np.ndarray, max_modes: int = 12) -> ModeList:
        """Extracts resonances by picking peaks and measuring decay trends in the signal's autocorrelation."""
        N = len(sig)
        r = np.correlate(sig, sig, mode='full')[N-1:]
        r = r / (r[0] + 1e-12)
        
        max_lag = int(self.fs / self.min_freq)
        min_lag = int(self.fs / self.max_freq)
        min_lag = max(1, min_lag)
        max_lag = min(len(r) - 2, max_lag)
        
        peaks, _ = signal.find_peaks(
            r[min_lag:max_lag],
            prominence=0.01 * np.max(r[min_lag:max_lag]),
            distance=10
        )
        peaks = peaks + min_lag
        
        if len(peaks) == 0:
            return ModeList()

        peak_vals = r[peaks]
        sorted_indices = np.argsort(peak_vals)[::-1][:max_modes]
        peaks = peaks[sorted_indices]

        modes = ModeList()
        for lag in peaks:
            freq = self.fs / lag
            
            # Fit exponential decay to correlation peaks
            lags_decay = []
            vals_decay = []
            for k in range(1, 10):
                idx = k * lag
                if idx < len(r) and r[idx] > 0.01:
                    lags_decay.append(idx / self.fs)
                    vals_decay.append(r[idx])
                else:
                    break
                    
            if len(vals_decay) >= 3:
                y = np.log(vals_decay)
                slope, _ = np.polyfit(lags_decay, y, 1)
                decay = -slope
            else:
                decay = 10.0
                
            if decay < 0.05:
                decay = 0.05

            amp = estimate_amplitude_filterbank(sig, freq, self.fs)
            if amp > 1e-4:
                modes.add(Mode(
                    frequency=float(freq),
                    amplitude=float(amp),
                    decay_rate=float(decay)
                ))

        modes.sort(by="amplitude")
        return modes


class WaveletObserver:
    def __init__(self, fs: int = 44_100) -> None:
        self.fs = fs

    def extract_modes(self, sig: np.ndarray, max_modes: int = 12, min_distance_hz: float = 30.0) -> ModeList:
        """Extracts resonances by tracking envelope dynamics across a bank of complex Gabor wavelets."""
        fc_candidates = np.logspace(np.log10(100.0), np.log10(8000.0), 36)
        
        envelopes = []
        for fc in fc_candidates:
            sigma_t = 8.0 / (2.0 * np.pi * fc)
            t_filt = np.arange(-4.0 * sigma_t, 4.0 * sigma_t, 1.0 / self.fs)
            filt = np.exp(2j * np.pi * fc * t_filt) * np.exp(-t_filt**2 / (2.0 * sigma_t**2))
            filt = filt / (np.linalg.norm(filt) + 1e-12)
            
            filtered = signal.convolve(sig, filt, mode='same')
            hop = 256
            n_frames = len(sig) // hop
            env = np.zeros(n_frames)
            for f_idx in range(n_frames):
                start = f_idx * hop
                stop = start + 512
                if stop < len(filtered):
                    env[f_idx] = np.mean(np.abs(filtered[start:stop]))
            envelopes.append(env)
            
        envelopes = np.array(envelopes)  # shape (36, n_frames)
        initial_mag = np.mean(envelopes[:, :min(5, envelopes.shape[1])], axis=1)
        
        peaks, _ = signal.find_peaks(initial_mag, prominence=0.01 * np.max(initial_mag))
        if len(peaks) == 0:
            return ModeList()

        peak_amps = initial_mag[peaks]
        sorted_indices = np.argsort(peak_amps)[::-1][:max_modes]
        peaks = peaks[sorted_indices]
        
        modes = ModeList()
        t_frames = (np.arange(envelopes.shape[1]) * 256) / self.fs
        
        for p in peaks:
            freq = fc_candidates[p]
            env = envelopes[p, :]
            
            max_idx = np.argmax(env)
            peak_val = env[max_idx]
            if peak_val == 0:
                continue
                
            threshold = peak_val * 0.01
            decay_frames = []
            for frame_idx in range(max_idx, len(env)):
                if env[frame_idx] >= threshold:
                    decay_frames.append(frame_idx)
                else:
                    break
                    
            if len(decay_frames) >= 5:
                t_decay = t_frames[decay_frames] - t_frames[max_idx]
                y = np.log(env[decay_frames] + 1e-12)
                slope, _ = np.polyfit(t_decay, y, 1)
                decay = -slope
            else:
                decay = 10.0
                
            if decay < 0.05:
                decay = 0.05

            amp = estimate_amplitude_filterbank(sig, freq, self.fs)
            if amp > 1e-4:
                modes.add(Mode(
                    frequency=float(freq),
                    amplitude=float(amp),
                    decay_rate=float(decay)
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


def run_observer_sweep(
    sig: np.ndarray,
    fs: int = 44_100,
    max_modes: int = 8,
    freq_tol_percent: float = 3.5
) -> list[dict]:
    """Sweeps the signal across 7 observers, groups candidate peaks into consensus modes, and evaluates epistemic stability."""
    observers = {
        "STFT": FourierObserver(fs=fs),
        "Filterbank": FilterbankObserver(fs=fs),
        "LPC": LpcObserver(fs=fs),
        "Autocorrelation": AutocorrelationObserver(fs=fs),
        "Prony": PronyObserver(fs=fs),
        "Matrix Pencil": MatrixPencilObserver(fs=fs),
        "Wavelet": WaveletObserver(fs=fs),
    }

    raw_candidates = []
    for name, obs in observers.items():
        try:
            modes = obs.extract_modes(sig, max_modes=max_modes)
            for m in modes.modes:
                raw_candidates.append({
                    "frequency": m.frequency,
                    "amplitude": m.amplitude,
                    "decay_rate": m.decay_rate,
                    "observer": name
                })
        except Exception as e:
            # Gracefully handle numerical instabilities in AR/subspace solvers
            pass

    if not raw_candidates:
        return []

    # Cluster frequencies using 1D Linkage
    freqs = np.array([c["frequency"] for c in raw_candidates])
    n_c = len(freqs)
    
    if n_c == 1:
        # Trivial single candidate case
        c = raw_candidates[0]
        return [{
            "frequency": c["frequency"],
            "frequency_variance": 0.0,
            "decay_rate": c["decay_rate"],
            "decay_variance": 0.0,
            "amplitude": c["amplitude"],
            "observers": [c["observer"]],
            "agreement_count": 1,
            "agreement_rate": float(1.0 / len(observers))
        }]

    dist_matrix = np.zeros((n_c, n_c))
    for i in range(n_c):
        for j in range(n_c):
            mean_f = (freqs[i] + freqs[j]) / 2.0
            dist_matrix[i, j] = (abs(freqs[i] - freqs[j]) / mean_f * 100.0) if mean_f > 0 else 0.0

    condensed_dist = squareform(dist_matrix)
    Z = sch.linkage(condensed_dist, method='complete')
    labels = sch.fcluster(Z, t=freq_tol_percent, criterion='distance')

    consensus_modes = []
    unique_labels = np.unique(labels)
    for label in unique_labels:
        mask = labels == label
        cluster_candidates = [raw_candidates[idx] for idx in range(n_c) if mask[idx]]

        c_freqs = [c["frequency"] for c in cluster_candidates]
        c_decays = [c["decay_rate"] for c in cluster_candidates]
        c_amps = [c["amplitude"] for c in cluster_candidates]
        c_observers = list(set(c["observer"] for c in cluster_candidates))

        mean_freq = float(np.mean(c_freqs))
        var_freq = float(np.var(c_freqs)) if len(c_freqs) > 1 else 0.0

        mean_decay = float(np.mean(c_decays))
        var_decay = float(np.var(c_decays)) if len(c_decays) > 1 else 0.0

        mean_amp = float(np.mean(c_amps))

        consensus_modes.append({
            "frequency": mean_freq,
            "frequency_variance": var_freq,
            "decay_rate": mean_decay,
            "decay_variance": var_decay,
            "amplitude": mean_amp,
            "observers": c_observers,
            "agreement_count": len(c_observers),
            "agreement_rate": float(len(c_observers) / len(observers))
        })

    # Sort consensus modes by agreement count, then by average amplitude
    consensus_modes.sort(key=lambda x: (x["agreement_count"], x["amplitude"]), reverse=True)
    return consensus_modes
