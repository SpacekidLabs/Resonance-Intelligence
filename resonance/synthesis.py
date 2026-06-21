import numpy as np
from resonance.modal import ModeList


def synthesize_modes(modes: ModeList, duration: float, fs: int = 44_100) -> np.ndarray:
    """Resynthesizes a time-domain signal from a set of modal parameters."""
    t = np.arange(int(duration * fs)) / fs
    sig = np.zeros_like(t)
    for m in modes.modes:
        sig += m.amplitude * np.exp(-m.decay_rate * t) * np.sin(2 * np.pi * m.frequency * t + m.phase)
    return sig
