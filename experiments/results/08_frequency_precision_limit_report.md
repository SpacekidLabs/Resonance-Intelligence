# Experiment 08: Frequency Precision Limit Report

This experiment asks how much frequency-estimation error each resonant object can tolerate before waveform prediction collapses.

Operational collapse definition: prediction horizon falls below **50 ms** or, equivalently, the local 5 ms RMS error ratio crosses **100%**.

## Glass
Dominant consensus mode: 395.47 Hz, decay 19.79 1/s, amplitude 0.8221
Injected baseline drift: 0.50% over 250 ms

| Frequency Error | Open Loop Horizon | Open Loop RMS | Open Loop SNR | Open Loop Phase Error | Tracker Horizon | Tracker RMS | Tracker SNR | Tracker Phase Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.01% | 246.94 ms | 6.62% | 23.58 dB | 33.72° | 246.94 ms | 13.00% | 17.72 dB | 107.24° |
| 0.05% | 246.94 ms | 4.47% | 27.00 dB | 27.33° | 246.94 ms | 12.72% | 17.91 dB | 106.60° |
| 0.10% | 246.94 ms | 3.07% | 30.26 dB | 19.53° | 246.94 ms | 17.88% | 14.95 dB | 116.31° |
| 0.20% | 246.94 ms | 7.34% | 22.68 dB | 8.07° | 246.94 ms | 22.80% | 12.84 dB | 122.79° |
| 0.50% | 246.94 ms | 26.23% | 11.62 dB | 53.07° | 246.94 ms | 30.80% | 10.23 dB | 130.02° |
| 1.00% | 246.94 ms | 53.08% | 5.50 dB | 116.22° | 246.94 ms | 39.63% | 8.04 dB | 134.60° |
| 2.00% | 2.49 ms | 80.96% | 1.83 dB | 41.54° | 2.49 ms | 52.78% | 5.55 dB | 41.29° |

Open loop collapse threshold: approximately 2.00% frequency error.
Iterative tracker collapse threshold: approximately 2.00% frequency error.

## Mug
Dominant consensus mode: 511.75 Hz, decay 42.89 1/s, amplitude 0.3173
Injected baseline drift: 0.50% over 250 ms

| Frequency Error | Open Loop Horizon | Open Loop RMS | Open Loop SNR | Open Loop Phase Error | Tracker Horizon | Tracker RMS | Tracker SNR | Tracker Phase Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.01% | 246.94 ms | 2.11% | 33.50 dB | 20.26° | 246.94 ms | 1.43% | 36.90 dB | 1.16° |
| 0.05% | 246.94 ms | 1.64% | 35.72 dB | 15.09° | 246.94 ms | 1.46% | 36.70 dB | 1.13° |
| 0.10% | 246.94 ms | 2.61% | 31.66 dB | 8.92° | 246.94 ms | 2.00% | 33.98 dB | 1.14° |
| 0.20% | 246.94 ms | 6.03% | 24.40 dB | 9.43° | 246.94 ms | 3.68% | 28.69 dB | 1.32° |
| 0.50% | 246.94 ms | 17.01% | 15.39 dB | 50.18° | 246.94 ms | 9.38% | 20.56 dB | 2.53° |
| 1.00% | 2.49 ms | 34.13% | 9.34 dB | 25.66° | 2.49 ms | 18.89% | 14.48 dB | 27.70° |
| 2.00% | 2.49 ms | 59.93% | 4.45 dB | 40.49° | 2.49 ms | 36.38% | 8.78 dB | 41.80° |

Open loop collapse threshold: approximately 1.00% frequency error.
Iterative tracker collapse threshold: approximately 1.00% frequency error.

## Metal Bowl
Dominant consensus mode: 711.32 Hz, decay 52.24 1/s, amplitude 0.7652
Injected baseline drift: 0.50% over 250 ms

| Frequency Error | Open Loop Horizon | Open Loop RMS | Open Loop SNR | Open Loop Phase Error | Tracker Horizon | Tracker RMS | Tracker SNR | Tracker Phase Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.01% | 246.94 ms | 1.56% | 36.14 dB | 21.61° | 246.94 ms | 0.79% | 42.10 dB | 1.33° |
| 0.05% | 246.94 ms | 1.10% | 39.16 dB | 15.35° | 246.94 ms | 0.87% | 41.18 dB | 1.23° |
| 0.10% | 246.94 ms | 2.82% | 30.99 dB | 8.19° | 246.94 ms | 1.90% | 34.45 dB | 1.22° |
| 0.20% | 246.94 ms | 7.00% | 23.10 dB | 13.46° | 246.94 ms | 4.25% | 27.43 dB | 1.51° |
| 0.50% | 246.94 ms | 19.54% | 14.18 dB | 61.76° | 246.94 ms | 11.43% | 18.84 dB | 3.42° |
| 1.00% | 2.49 ms | 38.47% | 8.30 dB | 19.51° | 2.49 ms | 23.00% | 12.77 dB | 19.32° |
| 2.00% | 2.49 ms | 65.02% | 3.74 dB | 35.85° | 2.49 ms | 43.05% | 7.32 dB | 35.76° |

Open loop collapse threshold: approximately 1.00% frequency error.
Iterative tracker collapse threshold: approximately 1.00% frequency error.

## Wood
Dominant consensus mode: 660.41 Hz, decay 81.20 1/s, amplitude 0.2633
Injected baseline drift: 0.50% over 250 ms

| Frequency Error | Open Loop Horizon | Open Loop RMS | Open Loop SNR | Open Loop Phase Error | Tracker Horizon | Tracker RMS | Tracker SNR | Tracker Phase Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.01% | 246.94 ms | 1.70% | 35.38 dB | 13.36° | 246.94 ms | 1.65% | 35.65 dB | 2.67° |
| 0.05% | 246.94 ms | 1.77% | 35.02 dB | 9.04° | 246.94 ms | 1.70% | 35.37 dB | 2.62° |
| 0.10% | 246.94 ms | 2.53% | 31.92 dB | 4.01° | 246.94 ms | 2.09% | 33.60 dB | 2.60° |
| 0.20% | 246.94 ms | 4.77% | 26.42 dB | 13.67° | 246.94 ms | 3.37% | 29.44 dB | 2.75° |
| 0.50% | 246.94 ms | 12.22% | 18.26 dB | 43.39° | 246.94 ms | 8.06% | 21.87 dB | 4.14° |
| 1.00% | 246.94 ms | 24.42% | 12.25 dB | 70.19° | 246.94 ms | 16.08% | 15.88 dB | 7.79° |
| 2.00% | 2.49 ms | 45.60% | 6.82 dB | 25.12° | 2.49 ms | 31.23% | 10.11 dB | 24.58° |

Open loop collapse threshold: approximately 2.00% frequency error.
Iterative tracker collapse threshold: approximately 2.00% frequency error.

## Scientific Interpretation

The prediction horizon shrinks as frequency estimation error grows because phase drift accumulates faster than the envelope decays.
The iterative tracker extends the horizon when the frequency error is still inside its capture range, but it cannot fully erase large initial misspecifications once the local phase error becomes too large.

### Conclusion
> [!IMPORTANT]
> **The frequency precision limit is object-dependent: the higher the resonance sensitivity to phase accumulation and envelope mismatch, the sooner the prediction horizon collapses.**
> Use the tracker for moderate errors; use tighter parameter estimation or richer models once the sweep shows horizon collapse inside the early transient window.