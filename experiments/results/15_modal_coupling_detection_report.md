# Experiment 15: Modal Coupling Detection Report

This experiment checks whether modal pairs behave like independent oscillators or show coupling, beating, sidebands, or shared envelopes.

Strong-pair rate (coupling score >= 0.45): **100.00%**

## Material Summaries

| Material | Mean Coupling | Mean Amp Corr | Mean Freq Corr | Mean Envelope Coherence |
| :--- | :---: | :---: | :---: | :---: |
| glass | 0.691 | 0.792 | 0.085 | 0.835 |
| mug | 0.846 | 0.993 | 0.152 | 0.999 |
| metal_bowl | 0.749 | 0.761 | 0.300 | 0.898 |
| wood | 0.779 | 0.934 | 0.359 | 0.958 |

## Top Coupled Pairs

| Material | Mode i | Mode j | Amp Corr | Freq Corr | Env Coh | Low-Band Fraction | Beat Align | Coupling |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| mug | 0 | 1 | 1.000 | 0.863 | 1.000 | 1.000 | 0.423 | 0.959 |
| wood | 0 | 3 | 0.998 | 0.828 | 0.998 | 1.000 | 0.000 | 0.947 |
| mug | 1 | 2 | 0.999 | 0.702 | 1.000 | 1.000 | 0.391 | 0.910 |
| metal_bowl | 0 | 1 | 0.977 | 0.739 | 0.969 | 0.999 | 0.000 | 0.906 |
| glass | 0 | 2 | 1.000 | 0.626 | 1.000 | 1.000 | 0.506 | 0.888 |
| mug | 0 | 3 | 0.983 | -0.584 | 0.997 | 0.993 | 0.377 | 0.867 |
| wood | 0 | 2 | 0.985 | 0.592 | 0.928 | 0.995 | 0.384 | 0.857 |
| mug | 1 | 3 | 0.986 | -0.455 | 0.997 | 0.993 | 0.378 | 0.830 |

## Interpretation

High amplitude correlation and high envelope coherence indicate shared envelopes, while high frequency correlation suggests frequency pulling or coordinated drift.
A strong low-band envelope spectrum suggests beat-like modulation rather than independent stationary modes.

### Conclusion
> [!IMPORTANT]
> **If the top pair scores are consistently high and the envelopes share low-frequency modulation, the modes are not independent oscillators. That would support energy exchange or coupling inside the resonator description.**