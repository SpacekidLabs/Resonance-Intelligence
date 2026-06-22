# Experiment 07: Iterative Phase Estimation Report

This experiment tests whether a simple PLL-style observer can track a slowly drifting resonance better than an open-loop fixed-frequency model.

For each material, we use the strongest consensus mode from Experiment 03, synthesize a drifting version of that mode, and compare fixed-frequency reconstruction against iterative phase correction.

## Glass
Consensus mode used: 395.47 Hz, decay 19.79 1/s, amplitude 0.8221
Drift injected: 1.0% linear frequency rise across 200 ms

| Reconstruction | RMS Error Ratio | SNR |
| :--- | :---: | :---: |
| Open Loop | 16.64% | 15.58 dB |
| PLL Tracking | 28.00% | 11.06 dB |

Frequency tracking RMS error: 14.546 Hz (3.678% of nominal)

## Mug
Consensus mode used: 511.75 Hz, decay 42.89 1/s, amplitude 0.3173
Drift injected: 1.0% linear frequency rise across 200 ms

| Reconstruction | RMS Error Ratio | SNR |
| :--- | :---: | :---: |
| Open Loop | 5.16% | 25.75 dB |
| PLL Tracking | 2.35% | 32.59 dB |

Frequency tracking RMS error: 0.846 Hz (0.165% of nominal)

## Metal Bowl
Consensus mode used: 711.32 Hz, decay 52.24 1/s, amplitude 0.7652
Drift injected: 0.5% linear frequency rise across 200 ms

| Reconstruction | RMS Error Ratio | SNR |
| :--- | :---: | :---: |
| Open Loop | 2.38% | 32.47 dB |
| PLL Tracking | 1.15% | 38.76 dB |

Frequency tracking RMS error: 0.591 Hz (0.083% of nominal)

## Wood
Consensus mode used: 660.41 Hz, decay 81.20 1/s, amplitude 0.2633
Drift injected: 0.5% linear frequency rise across 200 ms

| Reconstruction | RMS Error Ratio | SNR |
| :--- | :---: | :---: |
| Open Loop | 2.16% | 33.33 dB |
| PLL Tracking | 2.05% | 33.78 dB |

Frequency tracking RMS error: 0.554 Hz (0.084% of nominal)

## Scientific Interpretation

The open-loop reconstruction uses the nominal frequency and therefore accumulates phase error when the target drifts.
The iterative tracker updates frequency from windowed phase measurements, which reduces the long-horizon residual and keeps the synthesized phase closer to the drifting target.

### Conclusion
> [!IMPORTANT]
> **Iterative phase estimation closes part of the predictability gap identified in Experiment 06, but only when the observer is allowed to update its state from local phase measurements.**
> A fixed modal basis is not enough once the resonance drifts; active feedback is required to keep long-window reconstruction coherent.