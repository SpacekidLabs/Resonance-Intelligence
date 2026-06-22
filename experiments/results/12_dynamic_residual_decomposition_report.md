# Experiment 12: Dynamic Residual Decomposition Report

This experiment analyzes the remainder left by the dynamic modal model from Experiment 11.
It asks what the dynamic model still fails to explain after time-varying frequency and amplitude have been introduced.

## Glass
Onset index: 0 samples (0.00 ms)
Static model RMS ratio: **99.99%**
Dynamic model RMS ratio: **89.01%**
Residual RMS improvement: **10.99%**
Static residual decay: **7.05 1/s** (half-life 98.26 ms)
Dynamic residual decay: **7.03 1/s** (half-life 98.53 ms)
Static spectral flatness: **0.000**
Dynamic spectral flatness: **0.000**
Dynamic first-5ms energy: **9.66%**
Dynamic t90: **80.16 ms**
Dynamic category: **Slow detuning or dynamic modes**

| Residual State | RMS Ratio | SNR | Category |
| :--- | :---: | :---: | :--- |
| Static | 99.99% | 0.00 dB | Slow detuning or dynamic modes |
| Dynamic | 89.01% | 1.01 dB | Slow detuning or dynamic modes |

| Dynamic Residual Peaks (Hz) | Relative Power |
| :--- | :---: |
| 1561.16 | 3.3969e-03 |

## Mug
Onset index: 0 samples (0.00 ms)
Static model RMS ratio: **99.85%**
Dynamic model RMS ratio: **99.96%**
Residual RMS improvement: **-0.11%**
Static residual decay: **14.25 1/s** (half-life 48.63 ms)
Dynamic residual decay: **14.27 1/s** (half-life 48.57 ms)
Static spectral flatness: **0.000**
Dynamic spectral flatness: **0.000**
Dynamic first-5ms energy: **14.69%**
Dynamic t90: **62.40 ms**
Dynamic category: **Slow detuning or dynamic modes**

| Residual State | RMS Ratio | SNR | Category |
| :--- | :---: | :---: | :--- |
| Static | 99.85% | 0.01 dB | Slow detuning or dynamic modes |
| Dynamic | 99.96% | 0.00 dB | Slow detuning or dynamic modes |

| Dynamic Residual Peaks (Hz) | Relative Power |
| :--- | :---: |
| 818.26 | 1.4124e-03 |
| 1335.06 | 3.5397e-04 |
| 1098.19 | 2.3761e-12 |

## Metal Bowl
Onset index: 0 samples (0.00 ms)
Static model RMS ratio: **99.74%**
Dynamic model RMS ratio: **83.31%**
Residual RMS improvement: **16.47%**
Static residual decay: **0.14 1/s** (half-life 4988.83 ms)
Dynamic residual decay: **1.13 1/s** (half-life 615.46 ms)
Static spectral flatness: **0.000**
Dynamic spectral flatness: **0.000**
Dynamic first-5ms energy: **6.28%**
Dynamic t90: **87.57 ms**
Dynamic category: **Slow detuning or dynamic modes**

| Residual State | RMS Ratio | SNR | Category |
| :--- | :---: | :---: | :--- |
| Static | 99.74% | 0.02 dB | Slow detuning or dynamic modes |
| Dynamic | 83.31% | 1.59 dB | Slow detuning or dynamic modes |

| Dynamic Residual Peaks (Hz) | Relative Power |
| :--- | :---: |
| 441.43 | 3.5682e-03 |
| 936.69 | 7.6375e-04 |

## Wood
Onset index: 0 samples (0.00 ms)
Static model RMS ratio: **99.12%**
Dynamic model RMS ratio: **93.99%**
Residual RMS improvement: **5.18%**
Static residual decay: **42.63 1/s** (half-life 16.26 ms)
Dynamic residual decay: **43.27 1/s** (half-life 16.02 ms)
Static spectral flatness: **0.000**
Dynamic spectral flatness: **0.000**
Dynamic first-5ms energy: **36.46%**
Dynamic t90: **23.54 ms**
Dynamic category: **Mixed residual**

| Residual State | RMS Ratio | SNR | Category |
| :--- | :---: | :---: | :--- |
| Static | 99.12% | 0.08 dB | Mixed residual |
| Dynamic | 93.99% | 0.54 dB | Mixed residual |

| Dynamic Residual Peaks (Hz) | Relative Power |
| :--- | :---: |
| 183.03 | 2.2482e-04 |

## Scientific Interpretation

The dynamic remainder is the part of the signal that remains unexplained even after the mode trajectories have been allowed to move in time.
Comparing static and dynamic residuals tells us whether the leftover error is mostly due to missing mode drift, uncaptured excitation, or genuinely non-modal structure.

### Category Key
- Broadband transient: residual energy is front-loaded and spectrally flat.
- Structured tonal residue / sidebands: residual still contains narrow peaks, suggesting coupling or missing modulation products.
- Slow detuning or dynamic modes: residual decays slowly, suggesting the current trajectories still underfit the motion of the modes.

### Conclusion
> [!IMPORTANT]
> **Experiment 12 measures the remainder of the dynamic model itself. If the dynamic residual is still structured, the next step is not more static fitting, but more expressive dynamics or explicit excitation modeling.**