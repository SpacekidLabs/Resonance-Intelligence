# Experiment 10B: Excitation / Resonator Separation Report

This experiment treats the signal as a short excitation convolved with a resonator impulse response.
We estimate an effective excitation by regularized deconvolution and then re-convolve it to check whether the original sound can be recovered.

## Glass
Onset index: 0 samples (0.00 ms)
Modal reconstruction RMS ratio: **99.99%**
Modal reconstruction SNR: **0.00 dB**
Resynthesized-from-excitation RMS ratio: **139.81%**
Resynthesized-from-excitation SNR: **-2.91 dB**
Excitation energy in first 5 ms: **16.88%**
Excitation t90: **352.02 ms**
Excitation spectral flatness: **0.014**
Excitation crest factor: **22.32**

Verdict: The excitation remains entangled with the resonator tail; a richer excitation model is needed.

## Mug
Onset index: 0 samples (0.00 ms)
Modal reconstruction RMS ratio: **95.85%**
Modal reconstruction SNR: **0.37 dB**
Resynthesized-from-excitation RMS ratio: **39.80%**
Resynthesized-from-excitation SNR: **8.00 dB**
Excitation energy in first 5 ms: **31.26%**
Excitation t90: **43.40 ms**
Excitation spectral flatness: **0.087**
Excitation crest factor: **47.37**

Verdict: The excitation remains entangled with the resonator tail; a richer excitation model is needed.

## Metal Bowl
Onset index: 0 samples (0.00 ms)
Modal reconstruction RMS ratio: **98.18%**
Modal reconstruction SNR: **0.16 dB**
Resynthesized-from-excitation RMS ratio: **16.86%**
Resynthesized-from-excitation SNR: **15.46 dB**
Excitation energy in first 5 ms: **71.04%**
Excitation t90: **218.37 ms**
Excitation spectral flatness: **0.284**
Excitation crest factor: **81.48**

Verdict: The excitation remains entangled with the resonator tail; a richer excitation model is needed.

## Wood
Onset index: 0 samples (0.00 ms)
Modal reconstruction RMS ratio: **95.99%**
Modal reconstruction SNR: **0.36 dB**
Resynthesized-from-excitation RMS ratio: **135.00%**
Resynthesized-from-excitation SNR: **-2.61 dB**
Excitation energy in first 5 ms: **99.30%**
Excitation t90: **2.40 ms**
Excitation spectral flatness: **0.467**
Excitation crest factor: **95.19**

Verdict: Short, broadband strike excitation is separable from resonator response.

## Scientific Interpretation

If the deconvolved excitation is short and broadband, the strike is separable from the resonator response.
If the excitation remains long or tonal, the modal basis is still absorbing dynamics that should belong to the excitation model or to time-varying resonator behavior.

### Conclusion
> [!IMPORTANT]
> **Excitation / resonator separation becomes convincing only when the recovered force-like signal is compact in time and broad in spectrum, while the re-convolution reproduces the original waveform with low error.**
> If that holds, then the next step is dynamic modal resynthesis with separate excitation and resonator terms.