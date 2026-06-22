# Experiment 13: Dynamic Excitation Modeling Report

This experiment treats the dynamic-model remainder from Experiment 12 as an excitation candidate.
It asks whether that remainder is compact, broadband, and rapidly decaying, and whether it recombines with dynamic resonators in a way that transfers identity.

## Glass
Excitation candidate is the dynamic residual from Experiment 12.
First 10 ms energy: **18.25%**
First 5 ms energy: **9.66%**
Residual decay rate: **7.01 1/s** (half-life 98.87 ms)
Spectral flatness vs dynamic model: **2.876e-08 vs 1.417e-10**
Transient sharpness (crest factor): **2.70**
Early sharpness (peak/mean abs over first 10 ms): **2.25**
Recombination self-error: **0.00%**
Residual-only RMS of dynamic model: **89.01%**

Verdict: Excitation candidate is flatter than the dynamic modal remainder and behaves like a strike impulse.

## Mug
Excitation candidate is the dynamic residual from Experiment 12.
First 10 ms energy: **28.80%**
First 5 ms energy: **14.69%**
Residual decay rate: **14.07 1/s** (half-life 49.27 ms)
Spectral flatness vs dynamic model: **5.451e-08 vs 5.279e-08**
Transient sharpness (crest factor): **4.41**
Early sharpness (peak/mean abs over first 10 ms): **3.22**
Recombination self-error: **0.00%**
Residual-only RMS of dynamic model: **99.96%**

Verdict: Excitation candidate is flatter than the dynamic modal remainder and behaves like a strike impulse.

## Metal Bowl
Excitation candidate is the dynamic residual from Experiment 12.
First 10 ms energy: **11.55%**
First 5 ms energy: **6.28%**
Residual decay rate: **1.27 1/s** (half-life 544.79 ms)
Spectral flatness vs dynamic model: **1.417e-08 vs 1.930e-11**
Transient sharpness (crest factor): **2.56**
Early sharpness (peak/mean abs over first 10 ms): **2.94**
Recombination self-error: **0.00%**
Residual-only RMS of dynamic model: **83.31%**

Verdict: Excitation candidate is flatter than the dynamic modal remainder and behaves like a strike impulse.

## Wood
Excitation candidate is the dynamic residual from Experiment 12.
First 10 ms energy: **62.51%**
First 5 ms energy: **36.46%**
Residual decay rate: **42.03 1/s** (half-life 16.49 ms)
Spectral flatness vs dynamic model: **4.518e-07 vs 5.074e-10**
Transient sharpness (crest factor): **4.80**
Early sharpness (peak/mean abs over first 10 ms): **2.16**
Recombination self-error: **0.00%**
Residual-only RMS of dynamic model: **93.99%**

Verdict: Excitation candidate is short and rapidly disappearing.

## Cross-Swap Analysis

For each source excitation and resonator target, we form a hybrid: excitation_source + resonator_target.
We then ask whether the hybrid is closer to the source identity or the target identity.

Off-diagonal hybrids that are closer to the target resonator: **1/12** (8.33%)

| Excitation Source | Resonator Target | Source RMS | Target RMS | Dominance Score | Best Match |
| :--- | :--- | :---: | :---: | :---: | :--- |
| Glass | Glass | 0.00% | 0.00% | 0.000 | Glass |
| Glass | Mug | 45.64% | 157.36% | -1.117 | Glass |
| Glass | Metal Bowl | 79.69% | 112.30% | -0.326 | Glass |
| Glass | Wood | 48.87% | 192.96% | -1.441 | Glass |
| Mug | Glass | 62.75% | 114.45% | -0.517 | Mug |
| Mug | Mug | 0.00% | 0.00% | 0.000 | Mug |
| Mug | Metal Bowl | 90.08% | 103.28% | -0.132 | Mug |
| Mug | Wood | 24.83% | 166.60% | -1.418 | Mug |
| Metal Bowl | Glass | 67.40% | 132.77% | -0.654 | Metal Bowl |
| Metal Bowl | Mug | 55.41% | 167.89% | -1.125 | Metal Bowl |
| Metal Bowl | Metal Bowl | 0.00% | 0.00% | 0.000 | Metal Bowl |
| Metal Bowl | Wood | 55.90% | 209.46% | -1.536 | Metal Bowl |
| Wood | Glass | 92.82% | 101.59% | -0.088 | Wood |
| Wood | Mug | 34.30% | 120.60% | -0.863 | Wood |
| Wood | Metal Bowl | 125.53% | 93.28% | 0.322 | Metal Bowl |
| Wood | Wood | 0.00% | 0.00% | 0.000 | Wood |

## Scientific Interpretation

The excitation candidate is the dynamic residual after the time-varying modal model has been removed.
If that residual is compact in time and flatter in spectrum than the resonator, it is behaving like a strike excitation rather than another hidden mode set.
The swap matrix tests whether excitation and resonator identities can be recombined and transferred across materials.

### Conclusion
> [!IMPORTANT]
> **Experiment 13 asks whether the dynamic-model remainder can be interpreted as a meaningful excitation signal. If the residual is short, broadband, and the cross-swaps tend to preserve resonator identity, the project has isolated the two key physical components of impact synthesis: strike and object.**