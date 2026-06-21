import numpy as np
from resonance.modal import ModeList


def synthesize_modes(modes: ModeList, duration: float, fs: int = 44_100) -> np.ndarray:
    """Resynthesizes a time-domain signal from a set of modal parameters."""
    t = np.arange(int(duration * fs)) / fs
    sig = np.zeros_like(t)
    for m in modes.modes:
        sig += m.amplitude * np.exp(-m.decay_rate * t) * np.sin(2 * np.pi * m.frequency * t + m.phase)
    return sig


def fit_amplitudes_and_phases(
    sig: np.ndarray,
    freqs: list[float],
    decays: list[float],
    fs: int = 44_100,
    fit_window_samples: int = 4000
) -> tuple[np.ndarray, np.ndarray]:
    """Fits amplitudes and phases for a set of frequencies and decay rates to match sig via least squares."""
    from resonance.extraction import detect_onset
    
    onset_idx = detect_onset(sig)
    N_fit = min(fit_window_samples, len(sig) - onset_idx)
    if N_fit <= 0 or len(freqs) == 0:
        return np.array([]), np.array([])
        
    s_seg = sig[onset_idx : onset_idx + N_fit]
    t = np.arange(N_fit) / fs
    
    num_modes = len(freqs)
    H = np.zeros((N_fit, 2 * num_modes))
    for i in range(num_modes):
        f = freqs[i]
        d = decays[i]
        H[:, 2*i] = np.exp(-d * t) * np.sin(2 * np.pi * f * t)
        H[:, 2*i + 1] = np.exp(-d * t) * np.cos(2 * np.pi * f * t)
        
    # Solve least squares H @ c = s_seg
    c, _, _, _ = np.linalg.lstsq(H, s_seg, rcond=None)
    
    amps = np.zeros(num_modes)
    phases = np.zeros(num_modes)
    for i in range(num_modes):
        a = c[2*i]
        b = c[2*i + 1]
        amps[i] = np.sqrt(a**2 + b**2)
        phases[i] = np.arctan2(b, a)
        
    return amps, phases


def synthesize_modes_aligned(
    modes: ModeList,
    duration_samples: int,
    onset_idx: int,
    fs: int = 44_100
) -> np.ndarray:
    """Resynthesizes a signal from modes, starting at onset_idx and prepending silence."""
    if duration_samples <= onset_idx:
        return np.zeros(duration_samples)
        
    t = np.arange(duration_samples - onset_idx) / fs
    sig_ringing = np.zeros_like(t)
    for m in modes.modes:
        sig_ringing += m.amplitude * np.exp(-m.decay_rate * t) * np.sin(2 * np.pi * m.frequency * t + m.phase)
    return np.concatenate([np.zeros(onset_idx), sig_ringing])

