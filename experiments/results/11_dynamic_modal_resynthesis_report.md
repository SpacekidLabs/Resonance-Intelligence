# Experiment 11: Dynamic Modal Resynthesis Report

This experiment compares a static modal model against a dynamic modal model using the time-varying trajectories measured in Experiment 10A.

## Glass
Onset index: 0 samples (0.00 ms)
Static model RMS ratio: **99.99%**
Static model SNR: **0.00 dB**
Dynamic model RMS ratio: **89.01%**
Dynamic model SNR: **1.01 dB**
Relative improvement: **10.99%**

Verdict: Dynamic modal trajectories improve reconstruction over a static basis.

## Mug
Onset index: 0 samples (0.00 ms)
Static model RMS ratio: **99.85%**
Static model SNR: **0.01 dB**
Dynamic model RMS ratio: **99.96%**
Dynamic model SNR: **0.00 dB**
Relative improvement: **-0.11%**

Verdict: Dynamic trajectories do not yet outperform the static basis for this material.

## Metal Bowl
Onset index: 0 samples (0.00 ms)
Static model RMS ratio: **99.74%**
Static model SNR: **0.02 dB**
Dynamic model RMS ratio: **83.31%**
Dynamic model SNR: **1.59 dB**
Relative improvement: **16.47%**

Verdict: Dynamic modal trajectories improve reconstruction over a static basis.

## Wood
Onset index: 0 samples (0.00 ms)
Static model RMS ratio: **99.12%**
Static model SNR: **0.08 dB**
Dynamic model RMS ratio: **93.99%**
Dynamic model SNR: **0.54 dB**
Relative improvement: **5.18%**

Verdict: Dynamic modal trajectories improve reconstruction over a static basis.

## Scientific Interpretation

If the dynamic model reduces the same residual metrics used in Experiment 09, then the data supports time-varying modal parameters rather than a strictly static basis.
A weaker or mixed result would indicate that excitation separation still dominates the error budget, or that the tracked trajectories need stronger regularization.

### Conclusion
> [!IMPORTANT]
> **Experiment 11 turns measured mode drift into a dynamic synthesizer. If the dynamic model outperforms the static one, the modal system is evolving in time rather than remaining fixed.**