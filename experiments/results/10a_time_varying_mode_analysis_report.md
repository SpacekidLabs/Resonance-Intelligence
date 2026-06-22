# Experiment 10A: Time-Varying Mode Analysis Report

This experiment tests whether modal frequencies are stationary over the first 100 ms after onset.
We track the strongest consensus modes with a narrow-band analytic-signal observer and measure f(t), d(t), and A(t).

## Glass
Onset index: 0 samples (0.00 ms)

| Mode Freq (Hz) | f start | f end | f drift % | d start | d end | A start | A end |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 395.47 | 396.15 | 387.17 | -2.27% | 324.79 | 4.29 | 0.0127 | 0.0000 |
| 2330.13 | 2240.30 | 2239.94 | -0.02% | 2.98 | 9.75 | 0.2514 | 0.1078 |
| 365.18 | 362.41 | 347.62 | -4.08% | 337.84 | 137.01 | 0.0123 | 0.0000 |
| 10976.95 | 10343.49 | 10934.92 | 5.72% | 753.73 | 0.90 | 0.0030 | 0.0000 |
## Mug
Onset index: 0 samples (0.00 ms)

| Mode Freq (Hz) | f start | f end | f drift % | d start | d end | A start | A end |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 511.75 | 506.03 | 792.09 | 56.53% | 267.56 | 4.80 | 0.0076 | 0.0000 |
| 493.03 | 485.35 | 793.36 | 63.46% | 264.78 | -4.16 | 0.0076 | 0.0000 |
| 395.01 | 390.43 | 413.75 | 5.97% | 259.52 | 3.40 | 0.0086 | 0.0000 |
| 187.33 | 185.76 | 162.24 | -12.66% | 106.06 | 34.44 | 0.0088 | 0.0000 |
## Metal Bowl
Onset index: 0 samples (0.00 ms)

| Mode Freq (Hz) | f start | f end | f drift % | d start | d end | A start | A end |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 711.32 | 655.65 | 649.99 | -0.86% | 0.00 | 2.78 | 0.2330 | 0.2199 |
| 692.28 | 651.87 | 649.97 | -0.29% | 0.25 | 2.78 | 0.2483 | 0.2269 |
| 750.28 | 661.77 | 650.26 | -1.74% | 38.78 | 2.77 | 0.1267 | 0.0799 |
| 674.92 | 649.71 | 649.97 | 0.04% | 0.64 | 2.78 | 0.2556 | 0.2272 |
## Wood
Onset index: 0 samples (0.00 ms)

| Mode Freq (Hz) | f start | f end | f drift % | d start | d end | A start | A end |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 660.41 | 626.42 | 617.75 | -1.38% | 5.40 | 92.19 | 0.0750 | 0.0001 |
| 493.91 | 474.54 | 519.36 | 9.45% | 227.96 | -5.26 | 0.0325 | 0.0000 |
| 391.20 | 381.95 | 378.28 | -0.96% | -5.04 | 65.97 | 0.1354 | 0.0006 |
| 686.99 | 631.00 | 618.48 | -1.98% | 30.64 | 95.37 | 0.0641 | 0.0001 |
## Scientific Interpretation

If the fitted frequency, decay, and amplitude trajectories are nearly flat, the mode is stationary over the 0-100 ms observation window.
If the frequency trajectory shifts materially, that is direct evidence of detuning or effective mode motion rather than a fixed modal basis.

### Conclusion
> [!IMPORTANT]
> **Experiment 10A measures stationarity directly. Any consistent slope in f(t), d(t), or A(t) is evidence that the modal parameters are evolving, not fixed.**
> That result would motivate a dynamic modal synthesizer in the next experiment.