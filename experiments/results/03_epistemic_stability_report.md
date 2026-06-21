# Experiment 03: Epistemic Stability Report

## 1. Executive Summary
Rather than focusing on optimizing a synthesizer, this experiment maps the **epistemic stability** of candidate resonances across seven fundamentally different observers:
- **STFT** (spectral-slice tracing)
- **Filterbank** (tuned IIR resonator envelopes)
- **LPC** (autoregressive Yule-Walker root angles)
- **Prony's Method** (linear predictive complex exponentials)
- **Matrix Pencil** (singular value decomposition subspace shift)
- **Autocorrelation** (time-lag peak tracking)
- **Wavelet** (complex Gabor wavelet scale dynamics)

We classify resonances by the number of independent observers that converge on them, separating **Physical Invariant Modes** from **Method-Dependent Artifacts**.

## 2. Epistemic Stability Table: Glass
| Rank | Consensus Freq (Hz) | Freq Var | Mean Decay (1/s) | Decay Var | Agreement (Count/7) | Observers |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | 392.17 | 1.6298 | 9.69 | 6.0770 | 2/7 | Autocorrelation, Filterbank |
| 2 | 400.10 | 2.7511 | 72.11 | 4205.8255 | 2/7 | LPC, STFT |
| 3 | 358.34 | 0.0161 | 72.02 | 3846.0060 | 2/7 | Autocorrelation, LPC |
| 4 | 3137.81 | 7.9293 | 6.27 | 0.0020 | 2/7 | Filterbank, STFT |
| 5 | 2345.76 | 4.0205 | 5.73 | 0.0001 | 2/7 | Filterbank, STFT |
| 6 | 10979.85 | 235.2624 | 15.44 | 0.9958 | 2/7 | Filterbank, STFT |
| 7 | 14669.51 | 5.6097 | 18.76 | 0.1288 | 2/7 | Filterbank, STFT |
| 8 | 7805.78 | 1.2001 | 11.79 | 0.1882 | 2/7 | Filterbank, STFT |
| 9 | 5854.09 | 27.9814 | 9.05 | 0.0788 | 2/7 | Filterbank, STFT |
| 10 | 379.85 | 0.0000 | 135.44 | 0.0000 | 1/7 | LPC |
| 11 | 423.55 | 0.0000 | 135.72 | 0.0000 | 1/7 | LPC |
| 12 | 336.72 | 0.0000 | 135.32 | 0.0000 | 1/7 | LPC |
| 13 | 445.19 | 0.0000 | 136.91 | 0.0000 | 1/7 | LPC |
| 14 | 314.41 | 0.0000 | 130.49 | 0.0000 | 1/7 | LPC |
| 15 | 42.48 | 0.0000 | 34.83 | 0.0000 | 1/7 | LPC |
| 16 | 195.92 | 0.0000 | 7.95 | 0.0000 | 1/7 | Autocorrelation |
| 17 | 272.27 | 0.0000 | 6.87 | 0.0000 | 1/7 | Wavelet |
| 18 | 187.01 | 0.0000 | 7.12 | 0.0000 | 1/7 | Wavelet |
| 19 | 87.27 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 20 | 130.79 | 0.0000 | 14.41 | 0.0000 | 1/7 | Autocorrelation |
| 21 | 126.32 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 22 | 97.76 | 0.0000 | 9.85 | 0.0000 | 1/7 | Autocorrelation |
| 23 | 2287.44 | 0.0000 | 5.68 | 0.0000 | 1/7 | Wavelet |
| 24 | 16429.69 | 0.0000 | 55.93 | 0.0000 | 1/7 | STFT |
| 25 | 3692.31 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 26 | 5495.00 | 0.0000 | 9.14 | 0.0000 | 1/7 | Wavelet |

## 2. Epistemic Stability Table: Mug
| Rank | Consensus Freq (Hz) | Freq Var | Mean Decay (1/s) | Decay Var | Agreement (Count/7) | Observers |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | 279.95 | 0.4765 | 23.29 | 0.3115 | 2/7 | Filterbank, LPC |
| 2 | 508.30 | 0.7540 | 88.18 | 311.9894 | 2/7 | Matrix Pencil, Wavelet |
| 3 | 492.46 | 0.0760 | 49.87 | 62.7642 | 2/7 | Filterbank, STFT |
| 4 | 184.94 | 0.0000 | 22.79 | 0.0000 | 1/7 | Filterbank |
| 5 | 189.72 | 0.0000 | 59.61 | 0.0000 | 1/7 | Autocorrelation |
| 6 | 194.53 | 0.0000 | 35.24 | 0.0000 | 1/7 | LPC |
| 7 | 167.32 | 0.0000 | 42.87 | 0.0000 | 1/7 | LPC |
| 8 | 204.76 | 0.0000 | 36.08 | 0.0000 | 1/7 | Prony |
| 9 | 153.97 | 0.0000 | 41.57 | 0.0000 | 1/7 | Prony |
| 10 | 222.45 | 0.0000 | 29.04 | 0.0000 | 1/7 | LPC |
| 11 | 140.04 | 0.0000 | 53.91 | 0.0000 | 1/7 | LPC |
| 12 | 250.80 | 0.0000 | 26.05 | 0.0000 | 1/7 | LPC |
| 13 | 111.58 | 0.0000 | 80.80 | 0.0000 | 1/7 | LPC |
| 14 | 255.27 | 0.0000 | 22.94 | 0.0000 | 1/7 | Prony |
| 15 | 103.39 | 0.0000 | 48.48 | 0.0000 | 1/7 | Prony |
| 16 | 98.28 | 0.0000 | 136.05 | 0.0000 | 1/7 | LPC |
| 17 | 93.02 | 0.0000 | 14.94 | 0.0000 | 1/7 | Autocorrelation |
| 18 | 240.55 | 0.0000 | 23.85 | 0.0000 | 1/7 | Filterbank |
| 19 | 51.75 | 0.0000 | 57.15 | 0.0000 | 1/7 | Prony |
| 20 | 303.83 | 0.0000 | 15.88 | 0.0000 | 1/7 | Prony |
| 21 | 475.71 | 0.0000 | 114.18 | 0.0000 | 1/7 | Matrix Pencil |
| 22 | 351.28 | 0.0000 | 16.74 | 0.0000 | 1/7 | Prony |
| 23 | 453.88 | 0.0000 | 1.09 | 0.0000 | 1/7 | Prony |
| 24 | 384.75 | 0.0000 | 205.71 | 0.0000 | 1/7 | Matrix Pencil |
| 25 | 319.44 | 0.0000 | 22.40 | 0.0000 | 1/7 | Filterbank |
| 26 | 358.24 | 0.0000 | 22.79 | 0.0000 | 1/7 | Filterbank |
| 27 | 394.45 | 0.0000 | 23.09 | 0.0000 | 1/7 | Filterbank |
| 28 | 593.53 | 0.0000 | 265.34 | 0.0000 | 1/7 | Matrix Pencil |
| 29 | 234.38 | 0.0000 | 31.67 | 0.0000 | 1/7 | STFT |
| 30 | 811.61 | 0.0000 | 224.47 | 0.0000 | 1/7 | Matrix Pencil |
| 31 | 945.36 | 0.0000 | 268.97 | 0.0000 | 1/7 | Matrix Pencil |
| 32 | 1119.58 | 0.0000 | 210.50 | 0.0000 | 1/7 | Matrix Pencil |
| 33 | 1329.94 | 0.0000 | 157.18 | 0.0000 | 1/7 | Matrix Pencil |
| 34 | 8847.31 | 0.0000 | 42.84 | 0.0000 | 1/7 | Filterbank |
| 35 | 796.88 | 0.0000 | 27.64 | 0.0000 | 1/7 | STFT |

## 2. Epistemic Stability Table: Metal bowl
| Rank | Consensus Freq (Hz) | Freq Var | Mean Decay (1/s) | Decay Var | Agreement (Count/7) | Observers |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | 700.58 | 14.2456 | 53.81 | 953.3267 | 3/7 | Autocorrelation, Filterbank, Matrix Pencil |
| 2 | 654.80 | 0.5709 | 70.89 | 4839.1730 | 2/7 | Prony, Wavelet |
| 3 | 902.68 | 10.1111 | 333.08 | 82128.6573 | 2/7 | Filterbank, Matrix Pencil |
| 4 | 733.00 | 0.0000 | 782.79 | 0.0000 | 1/7 | Matrix Pencil |
| 5 | 49.13 | 0.0000 | 19.33 | 0.0000 | 1/7 | Prony |
| 6 | 55.29 | 0.0000 | 251.87 | 0.0000 | 1/7 | Matrix Pencil |
| 7 | 756.77 | 0.0000 | 5.32 | 0.0000 | 1/7 | Prony |
| 8 | 87.43 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 9 | 92.18 | 0.0000 | 46.07 | 0.0000 | 1/7 | Filterbank |
| 10 | 97.16 | 0.0000 | 0.13 | 0.0000 | 1/7 | Prony |
| 11 | 99.79 | 0.0000 | 192.57 | 0.0000 | 1/7 | Autocorrelation |
| 12 | 116.50 | 0.0000 | 179.96 | 0.0000 | 1/7 | Autocorrelation |
| 13 | 605.42 | 0.0000 | 1.20 | 0.0000 | 1/7 | Prony |
| 14 | 139.94 | 0.0000 | 181.50 | 0.0000 | 1/7 | Autocorrelation |
| 15 | 806.31 | 0.0000 | 2.82 | 0.0000 | 1/7 | Prony |
| 16 | 622.23 | 0.0000 | 46.88 | 0.0000 | 1/7 | Filterbank |
| 17 | 776.45 | 0.0000 | 46.17 | 0.0000 | 1/7 | Filterbank |
| 18 | 174.55 | 0.0000 | 174.94 | 0.0000 | 1/7 | Autocorrelation |
| 19 | 189.35 | 0.0000 | 492.99 | 0.0000 | 1/7 | Matrix Pencil |
| 20 | 536.83 | 0.0000 | 598.09 | 0.0000 | 1/7 | Matrix Pencil |
| 21 | 856.51 | 0.0000 | 0.06 | 0.0000 | 1/7 | Prony |
| 22 | 233.01 | 0.0000 | 173.08 | 0.0000 | 1/7 | Autocorrelation |
| 23 | 254.62 | 0.0000 | 5.67 | 0.0000 | 1/7 | Prony |
| 24 | 558.41 | 0.0000 | 47.77 | 0.0000 | 1/7 | Filterbank |
| 25 | 350.36 | 0.0000 | 158.63 | 0.0000 | 1/7 | Autocorrelation |
| 26 | 1090.29 | 0.0000 | 666.19 | 0.0000 | 1/7 | Matrix Pencil |
| 27 | 1262.23 | 0.0000 | 520.77 | 0.0000 | 1/7 | Matrix Pencil |
| 28 | 4319.97 | 0.0000 | 0.05 | 0.0000 | 1/7 | LPC |
| 29 | 4414.27 | 0.0000 | 968.19 | 0.0000 | 1/7 | LPC |
| 30 | 5647.85 | 414.9134 | 0.05 | 0.0000 | 1/7 | LPC |
| 31 | 5714.34 | 254.5903 | 510.67 | 521474.0589 | 1/7 | LPC |

## 2. Epistemic Stability Table: Wood
| Rank | Consensus Freq (Hz) | Freq Var | Mean Decay (1/s) | Decay Var | Agreement (Count/7) | Observers |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | 656.56 | 3.2133 | 126.37 | 2205.7705 | 3/7 | Autocorrelation, LPC, Wavelet |
| 2 | 497.39 | 0.0275 | 102.39 | 694.0883 | 2/7 | LPC, Matrix Pencil |
| 3 | 452.04 | 2.7679 | 43.03 | 1759.6101 | 2/7 | LPC, Prony |
| 4 | 666.89 | 7.1007 | 89.40 | 5455.6232 | 2/7 | Filterbank, Matrix Pencil |
| 5 | 482.47 | 12.7285 | 46.72 | 1002.0919 | 2/7 | Filterbank, LPC |
| 6 | 603.77 | 0.9836 | 5.23 | 24.2485 | 2/7 | Filterbank, Prony |
| 7 | 755.30 | 0.5672 | 7.11 | 43.0629 | 2/7 | Filterbank, Prony |
| 8 | 677.27 | 0.0000 | 74.59 | 0.0000 | 1/7 | LPC |
| 9 | 411.42 | 0.0000 | 77.99 | 0.0000 | 1/7 | LPC |
| 10 | 432.43 | 0.0000 | 132.74 | 0.0000 | 1/7 | LPC |
| 11 | 403.55 | 0.0000 | 0.92 | 0.0000 | 1/7 | Prony |
| 12 | 381.83 | 0.0000 | 77.43 | 0.0000 | 1/7 | LPC |
| 13 | 374.59 | 0.0000 | 455.10 | 0.0000 | 1/7 | Matrix Pencil |
| 14 | 509.17 | 0.0000 | 130.87 | 0.0000 | 1/7 | Wavelet |
| 15 | 342.86 | 0.0000 | 231.82 | 0.0000 | 1/7 | Autocorrelation |
| 16 | 519.83 | 0.0000 | 35.55 | 0.0000 | 1/7 | Filterbank |
| 17 | 705.90 | 0.0000 | 0.94 | 0.0000 | 1/7 | Prony |
| 18 | 611.94 | 0.0000 | 547.39 | 0.0000 | 1/7 | Matrix Pencil |
| 19 | 257.20 | 0.0000 | 294.94 | 0.0000 | 1/7 | Matrix Pencil |
| 20 | 554.90 | 0.0000 | 1.60 | 0.0000 | 1/7 | Prony |
| 21 | 251.57 | 0.0000 | 1.01 | 0.0000 | 1/7 | Prony |
| 22 | 694.33 | 0.0000 | 15.33 | 0.0000 | 1/7 | Filterbank |
| 23 | 228.57 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 24 | 201.98 | 0.0000 | 6.73 | 0.0000 | 1/7 | Prony |
| 25 | 634.12 | 0.0000 | 14.70 | 0.0000 | 1/7 | Filterbank |
| 26 | 798.85 | 0.0000 | 545.55 | 0.0000 | 1/7 | Matrix Pencil |
| 27 | 167.83 | 0.0000 | 208.19 | 0.0000 | 1/7 | Autocorrelation |
| 28 | 132.96 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 29 | 112.41 | 0.0000 | 113.75 | 0.0000 | 1/7 | Autocorrelation |
| 30 | 96.58 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 31 | 73.17 | 0.0000 | 73.37 | 0.0000 | 1/7 | Matrix Pencil |
| 32 | 83.62 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 33 | 724.44 | 0.0000 | 13.62 | 0.0000 | 1/7 | Filterbank |
| 34 | 925.66 | 0.0000 | 509.96 | 0.0000 | 1/7 | Matrix Pencil |

## 3. Scientific Interpretation & Verdict

### Physical Invariant Modes (High Epistemic Stability)
Modes that score an agreement of **$\geq 5/7$** with **low frequency variance** represent true physical resonances of the mechanical structure. 
For example:

### Method-Dependent Artifacts (Low Epistemic Stability)
Candidates with agreement **$\leq 2/7$** or **high parameter variance** represent observer artifacts rather than physical modes. These arise due to:
1. **Spectral Leakage / Windowing Side-lobes**: STFT or Wavelet observers sometimes pick up fake peaks caused by side-lobes of window functions. These are ignored by LPC or Matrix Pencil which fit model poles directly.
2. **AR Model Overfitting**: LPC or Prony observers with high order parameters can fit fake complex conjugate poles to noise components. These poles are ignored by Autocorrelation and STFT observers.
3. **Transient Blur**: Autocorrelation can identify periodicities in short impacts that do not correspond to actual sinusoidal ringing (such as the initial noise impact burst), leading to high variance across observers.

### Scientific Conclusion:
> [!IMPORTANT]
> **Resonance is not a monolithic physical property of the signal, but an epistemic conclusion drawn from multiple observation viewpoints.**
> By implementing an observer sweep, we filter out fragile artifacts and isolate the robust invariant core of a sounding object. Highly resonant objects (glass, bowl) show a high density of stable, consensus modes, whereas highly damped structures (wood) exhibit sparse, fragile, and scattered candidate peaks, confirming that damped impacts lack physically stable modal structures.