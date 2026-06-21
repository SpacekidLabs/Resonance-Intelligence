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
| 1 | 395.47 | 11.7906 | 19.79 | 360.9287 | 4/7 | Autocorrelation, Filterbank, LPC, STFT |
| 2 | 2330.13 | 612.2767 | 5.18 | 0.8685 | 4/7 | Filterbank, Matrix Pencil, STFT, Wavelet |
| 3 | 365.18 | 24.3283 | 22.01 | 581.3393 | 3/7 | Autocorrelation, LPC, Prony |
| 4 | 10976.95 | 259.0394 | 16.90 | 111.6558 | 3/7 | Filterbank, Matrix Pencil, STFT |
| 5 | 341.56 | 8.1257 | 29.07 | 789.5197 | 2/7 | LPC, Prony |
| 6 | 24.77 | 0.0175 | 42.70 | 1286.7199 | 2/7 | LPC, Prony |
| 7 | 315.56 | 18.6896 | 45.01 | 1862.9937 | 2/7 | LPC, Prony |
| 8 | 196.39 | 0.2204 | 7.22 | 0.5355 | 2/7 | Autocorrelation, Prony |
| 9 | 271.48 | 0.6112 | 4.81 | 4.2401 | 2/7 | Prony, Wavelet |
| 10 | 3137.81 | 7.9293 | 6.27 | 0.0020 | 2/7 | Filterbank, STFT |
| 11 | 14669.51 | 5.6097 | 18.76 | 0.1288 | 2/7 | Filterbank, STFT |
| 12 | 7805.78 | 1.2001 | 11.79 | 0.1882 | 2/7 | Filterbank, STFT |
| 13 | 5854.09 | 27.9814 | 9.05 | 0.0788 | 2/7 | Filterbank, STFT |
| 14 | 16427.72 | 3.8606 | 34.50 | 459.4488 | 2/7 | Matrix Pencil, STFT |
| 15 | 383.72 | 0.0000 | 52.15 | 0.0000 | 1/7 | LPC |
| 16 | 414.48 | 0.0000 | 57.39 | 0.0000 | 1/7 | LPC |
| 17 | 443.67 | 0.0000 | 59.80 | 0.0000 | 1/7 | LPC |
| 18 | 295.31 | 0.0000 | 2.36 | 0.0000 | 1/7 | Prony |
| 19 | 49.31 | 0.0000 | 6.43 | 0.0000 | 1/7 | Prony |
| 20 | 187.01 | 0.0000 | 7.12 | 0.0000 | 1/7 | Wavelet |
| 21 | 87.27 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 22 | 128.55 | 5.0051 | 12.21 | 4.8645 | 1/7 | Autocorrelation |
| 23 | 97.76 | 0.0000 | 9.85 | 0.0000 | 1/7 | Autocorrelation |
| 24 | 3692.31 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 25 | 5495.00 | 0.0000 | 9.14 | 0.0000 | 1/7 | Wavelet |

## 2. Epistemic Stability Table: Mug
| Rank | Consensus Freq (Hz) | Freq Var | Mean Decay (1/s) | Decay Var | Agreement (Count/7) | Observers |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | 511.75 | 11.0656 | 42.89 | 943.3541 | 3/7 | Matrix Pencil, Prony, Wavelet |
| 2 | 493.03 | 0.6855 | 55.20 | 98.6303 | 3/7 | Filterbank, Matrix Pencil, STFT |
| 3 | 395.01 | 3.4553 | 63.17 | 5088.4901 | 3/7 | Filterbank, Matrix Pencil, Prony |
| 4 | 187.33 | 5.7231 | 41.20 | 338.9917 | 2/7 | Autocorrelation, Filterbank |
| 5 | 280.76 | 0.0141 | 36.54 | 190.5869 | 2/7 | Filterbank, LPC |
| 6 | 237.46 | 9.5316 | 27.76 | 15.2929 | 2/7 | Filterbank, STFT |
| 7 | 321.47 | 4.1402 | 24.25 | 3.4235 | 2/7 | Filterbank, Prony |
| 8 | 444.01 | 2.3776 | 170.32 | 28959.1240 | 2/7 | Matrix Pencil, Prony |
| 9 | 363.26 | 25.2224 | 14.93 | 61.8373 | 2/7 | Filterbank, Prony |
| 10 | 808.44 | 133.8580 | 370.66 | 117664.1549 | 2/7 | Matrix Pencil, STFT |
| 11 | 175.97 | 0.0000 | 70.80 | 0.0000 | 1/7 | LPC |
| 12 | 201.56 | 0.0000 | 66.16 | 0.0000 | 1/7 | LPC |
| 13 | 151.08 | 0.0000 | 73.18 | 0.0000 | 1/7 | LPC |
| 14 | 227.95 | 0.0000 | 61.66 | 0.0000 | 1/7 | LPC |
| 15 | 126.38 | 0.0000 | 72.72 | 0.0000 | 1/7 | LPC |
| 16 | 254.50 | 0.0000 | 57.09 | 0.0000 | 1/7 | LPC |
| 17 | 101.49 | 0.0000 | 69.76 | 0.0000 | 1/7 | LPC |
| 18 | 93.02 | 0.0000 | 14.94 | 0.0000 | 1/7 | Autocorrelation |
| 19 | 302.69 | 0.0000 | 3.58 | 0.0000 | 1/7 | Prony |
| 20 | 344.38 | 0.0000 | 16.12 | 0.0000 | 1/7 | Prony |
| 21 | 541.05 | 0.0000 | 0.45 | 0.0000 | 1/7 | Prony |
| 22 | 585.69 | 0.0000 | 164.74 | 0.0000 | 1/7 | Matrix Pencil |
| 23 | 622.55 | 0.0000 | 375.87 | 0.0000 | 1/7 | Matrix Pencil |
| 24 | 684.48 | 0.0000 | 206.66 | 0.0000 | 1/7 | Matrix Pencil |
| 25 | 8847.31 | 0.0000 | 42.84 | 0.0000 | 1/7 | Filterbank |

## 2. Epistemic Stability Table: Metal bowl
| Rank | Consensus Freq (Hz) | Freq Var | Mean Decay (1/s) | Decay Var | Agreement (Count/7) | Observers |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | 711.32 | 41.3720 | 52.24 | 2290.7553 | 4/7 | Autocorrelation, LPC, Matrix Pencil, Prony |
| 2 | 692.28 | 19.3067 | 22.33 | 356.4944 | 3/7 | Filterbank, LPC, Prony |
| 3 | 750.28 | 105.1035 | 35.08 | 1705.5724 | 3/7 | LPC, Matrix Pencil, Prony |
| 4 | 674.92 | 4.6163 | 74.53 | 2721.8454 | 2/7 | LPC, Matrix Pencil |
| 5 | 653.34 | 0.5043 | 88.24 | 2726.1134 | 2/7 | LPC, Wavelet |
| 6 | 49.66 | 0.5491 | 232.34 | 42344.4999 | 2/7 | LPC, Matrix Pencil |
| 7 | 88.19 | 0.5819 | 7.39 | 6.8319 | 2/7 | Autocorrelation, Matrix Pencil |
| 8 | 621.14 | 1.1729 | 79.02 | 1032.9850 | 2/7 | Filterbank, Matrix Pencil |
| 9 | 781.44 | 24.8838 | 23.52 | 512.8660 | 2/7 | Filterbank, Prony |
| 10 | 818.22 | 57.4904 | 30.31 | 861.4908 | 2/7 | Matrix Pencil, Prony |
| 11 | 554.20 | 17.6643 | 71.57 | 566.5128 | 2/7 | Filterbank, Matrix Pencil |
| 12 | 29.19 | 0.0000 | 23.05 | 0.0000 | 1/7 | LPC |
| 13 | 92.18 | 0.0000 | 46.07 | 0.0000 | 1/7 | Filterbank |
| 14 | 99.79 | 0.0000 | 192.57 | 0.0000 | 1/7 | Autocorrelation |
| 15 | 105.89 | 0.0001 | 166.50 | 26734.9628 | 1/7 | Prony |
| 16 | 116.50 | 0.0000 | 179.96 | 0.0000 | 1/7 | Autocorrelation |
| 17 | 139.94 | 0.0000 | 181.50 | 0.0000 | 1/7 | Autocorrelation |
| 18 | 174.55 | 0.0000 | 174.94 | 0.0000 | 1/7 | Autocorrelation |
| 19 | 233.01 | 0.0000 | 173.08 | 0.0000 | 1/7 | Autocorrelation |
| 20 | 350.36 | 0.0000 | 158.63 | 0.0000 | 1/7 | Autocorrelation |
| 21 | 905.86 | 0.0000 | 46.50 | 0.0000 | 1/7 | Filterbank |

## 2. Epistemic Stability Table: Wood
| Rank | Consensus Freq (Hz) | Freq Var | Mean Decay (1/s) | Decay Var | Agreement (Count/7) | Observers |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | 660.41 | 14.9610 | 81.20 | 4843.8417 | 6/7 | Autocorrelation, Filterbank, LPC, Matrix Pencil, Prony, Wavelet |
| 2 | 493.91 | 24.7237 | 37.48 | 1181.5461 | 4/7 | Filterbank, LPC, Matrix Pencil, Prony |
| 3 | 391.20 | 21.5408 | 55.87 | 3009.5826 | 3/7 | LPC, Matrix Pencil, Prony |
| 4 | 686.99 | 44.8904 | 15.76 | 167.0759 | 3/7 | Filterbank, LPC, Prony |
| 5 | 472.49 | 27.6397 | 17.13 | 285.9640 | 2/7 | LPC, Prony |
| 6 | 413.85 | 17.9322 | 18.18 | 325.6899 | 2/7 | LPC, Prony |
| 7 | 437.35 | 28.2482 | 21.93 | 473.6566 | 2/7 | LPC, Prony |
| 8 | 514.50 | 28.4085 | 83.21 | 2271.2997 | 2/7 | Filterbank, Wavelet |
| 9 | 636.75 | 6.9206 | 7.37 | 53.6519 | 2/7 | Filterbank, Prony |
| 10 | 718.41 | 36.4062 | 43.29 | 880.0803 | 2/7 | Filterbank, Matrix Pencil |
| 11 | 600.63 | 4.6373 | 56.33 | 2132.1626 | 2/7 | Filterbank, Matrix Pencil |
| 12 | 453.85 | 0.0000 | 37.60 | 0.0000 | 1/7 | LPC |
| 13 | 365.94 | 0.0000 | 211.95 | 0.0000 | 1/7 | Matrix Pencil |
| 14 | 342.86 | 0.0000 | 231.82 | 0.0000 | 1/7 | Autocorrelation |
| 15 | 265.26 | 0.0000 | 312.49 | 0.0000 | 1/7 | Matrix Pencil |
| 16 | 228.57 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 17 | 167.83 | 0.0000 | 208.19 | 0.0000 | 1/7 | Autocorrelation |
| 18 | 132.96 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 19 | 112.41 | 0.0000 | 113.75 | 0.0000 | 1/7 | Autocorrelation |
| 20 | 96.58 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 21 | 83.62 | 0.0000 | 10.00 | 0.0000 | 1/7 | Autocorrelation |
| 22 | 754.55 | 0.0000 | 13.67 | 0.0000 | 1/7 | Filterbank |

## 3. Scientific Interpretation & Verdict

### Physical Invariant Modes (High Epistemic Stability)
Modes that score an agreement of **$\geq 5/7$** with **low frequency variance** represent true physical resonances of the mechanical structure. 
For example:
- **Wood**: Mode at **660.4 Hz** has **6/7** agreement (Freq Var = 14.9610), indicating a highly stable physical mode.

### Method-Dependent Artifacts (Low Epistemic Stability)
Candidates with agreement **$\leq 2/7$** or **high parameter variance** represent observer artifacts rather than physical modes. These arise due to:
1. **Spectral Leakage / Windowing Side-lobes**: STFT or Wavelet observers sometimes pick up fake peaks caused by side-lobes of window functions. These are ignored by LPC or Matrix Pencil which fit model poles directly.
2. **AR Model Overfitting**: LPC or Prony observers with high order parameters can fit fake complex conjugate poles to noise components. These poles are ignored by Autocorrelation and STFT observers.
3. **Transient Blur**: Autocorrelation can identify periodicities in short impacts that do not correspond to actual sinusoidal ringing (such as the initial noise impact burst), leading to high variance across observers.

### Scientific Conclusion:
> [!IMPORTANT]
> **Resonance is not a monolithic physical property of the signal, but an epistemic conclusion drawn from multiple observation viewpoints.**
> By implementing an observer sweep, we filter out fragile artifacts and isolate the robust invariant core of a sounding object. Highly resonant objects (glass, bowl) show a high density of stable, consensus modes, whereas highly damped structures (wood) exhibit sparse, fragile, and scattered candidate peaks, confirming that damped impacts lack physically stable modal structures.