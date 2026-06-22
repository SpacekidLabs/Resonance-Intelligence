# Experiment 09: Residual Decomposition Report

This experiment subtracts the best phase-aligned modal reconstruction from the original signal and examines the leftover energy.

Question: what is the modal model failing to explain?

## Glass
Residual RMS ratio: **99.99%**
Residual SNR: **0.00 dB**
Residual decay rate: **7.06 1/s**
Residual half-life: **98.19 ms**
Spectral flatness: **0.000**
Dominant residual peaks: **2**
Residual category: **Slow detuning or dynamic modes**

| Top Residual Peaks (Hz) | Relative Power |
| :--- | :---: |
| 1561.16 | 1.3664e-04 |
| 2239.45 | 3.0193e-05 |

## Mug
Residual RMS ratio: **95.85%**
Residual SNR: **0.37 dB**
Residual decay rate: **13.00 1/s**
Residual half-life: **53.31 ms**
Spectral flatness: **0.000**
Dominant residual peaks: **2**
Residual category: **Slow detuning or dynamic modes**

| Top Residual Peaks (Hz) | Relative Power |
| :--- | :---: |
| 818.26 | 3.7220e-05 |
| 1335.06 | 8.0655e-06 |

## Metal Bowl
Residual RMS ratio: **98.18%**
Residual SNR: **0.16 dB**
Residual decay rate: **0.00 1/s**
Residual half-life: **inf ms**
Spectral flatness: **0.000**
Dominant residual peaks: **3**
Residual category: **Slow detuning or dynamic modes**

| Top Residual Peaks (Hz) | Relative Power |
| :--- | :---: |
| 441.43 | 5.2727e-04 |
| 646.00 | 1.3405e-04 |
| 936.69 | 4.5482e-05 |

## Wood
Residual RMS ratio: **95.99%**
Residual SNR: **0.36 dB**
Residual decay rate: **43.18 1/s**
Residual half-life: **16.05 ms**
Spectral flatness: **0.000**
Dominant residual peaks: **2**
Residual category: **Mixed residual**

| Top Residual Peaks (Hz) | Relative Power |
| :--- | :---: |
| 183.03 | 4.3741e-06 |
| 398.36 | 1.8624e-07 |

## Scientific Interpretation

The residual is what remains after the best phase-aligned modal reconstruction has done its work. Its spectrum and envelope tell us which parts of the signal are not well explained by static decaying sinusoids.

### Category Key
- Broadband transient: the residual is noise-like and concentrated near onset.
- Structured tonal residue / sidebands: the residual still contains narrow peaks, suggesting missing coupled modes or modulation products.
- Slow detuning or dynamic modes: the residual decays slowly, suggesting the modal basis is not tracking time-varying frequencies well enough.

### Conclusion
> [!IMPORTANT]
> **Residual decomposition shows what the modal basis does not explain: either transient excitation, frequency modulation, or coupled sideband structure.**
> If the residual is broadband and front-loaded, the next model needs an excitation term. If it remains tonal, the next model needs dynamic modes or coupling terms.