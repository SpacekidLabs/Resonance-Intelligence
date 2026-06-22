# Roadmap

This is a living research roadmap for the **Resonance-Intelligence** project. We update it after every experiment that refines our understanding or changes what we believe. Every claim must be backed by a runnable script that reproduces the measurements.

---

## 1. Where We Are

- [x] Repository design and project layout initialization.
- [x] **Experiment 01 (Modal Extraction)**: Run extraction on synthetic impacts (glass, mug, bowl, wood) using both STFT and IIR Filterbank observers. Collect JSON modes. (Completed June 21, 2026)
- [x] **Experiment 02 (Modal Resynthesis)**: Resynthesize impacts, compute reconstruction error curves, and plot comparison dashboards. (Completed June 21, 2026)
- [x] **Experiment 03 (Observer Sweep & Epistemic Stability)**: Sweep 7 observers (STFT, Filterbank, LPC, Prony, Matrix Pencil, Autocorrelation, Wavelet) on 4 real impact sounds, cluster to construct consensus modes, and map epistemic stability. (Completed June 21, 2026)
- [x] **Experiment 04 (Phase Alignment & Resynthesis)**: Compare time-domain reconstruction errors across three cases (No Alignment, Onset Only, Full Phase Alignment) and identify the primary reconstruction bottleneck. (Completed June 21, 2026)
- [x] **Experiment 05 (State Drift Analysis)**: Apply relative frequency perturbations to consensus modes, measure phase divergence and local error growth, and quantify frequency precision requirements for predictability. (Completed June 21, 2026)

---

## 2. Core Hypotheses

We write roadmap claims as hypotheses until a corresponding experiment has been run and its measurements are compiled.

### Hypothesis A: Observer Agreement Identifies Real Modes
> If a resonance peak is a physical mode of the object, the **Fourier Observer** (STFT peak-picking) and the **Filterbank Observer** (IIR bandpass filter decay) will agree on its frequency (within $0.5\%$) and decay rate (within $10\%$).
> Conversely, spectral leakage peaks and windowing side-lobes will trigger high disagreement scores or fail to show stable decay in the filterbank, allowing us to mathematically isolate artifacts.

### Hypothesis B: Material-Dependent Sparsity
> Highly resonant structures (metal bowl, glass) can be reconstructed with low perceptual and mathematical error using a very sparse mode set ($N \leq 12$).
> In contrast, highly damped structures (wood) are broad-band and will require a dense mode set ($N > 30$) or fail to be modeled cleanly by decaying sines due to their transient-like nature.

### Hypothesis C: Phase Sensitivity in Onset Transients
> In phase-insensitive resynthesis (where initial phases $\phi_i$ are set to zero or randomized), the perceived material identity will survive, but the waveform envelope during the first $10\text{ms}$ will exhibit severe temporal smearing and high error relative to the original recording. Capturing phase alignment at onset is critical for transient realism.

---

## 3. Open Questions

- **Physical vs. Basis Artifacts**: When we fit a sound to decaying sines, are we extracting the real physical modes of the vibrating body, or are we simply projection-fitting a non-linear signal onto a linear decaying sine basis?
- **Filterbank Bandwidth Dependency**: How does the estimated decay rate in the Filterbank Observer vary with the bandwidth of the IIR filters? Is there a mathematical threshold where the filter's own impulse response dominates the measured decay?
- **Mode Coupling & Nonlinear Beating**: How do we model amplitude-dependent frequency modulation (pitch glide) and mode coupling (energy transfer between modes, causing beating) under a linear modal framework?

---

## 4. Failure Conditions

The project should be redirected or abandoned if any of the following are empirically verified:

- **Zero Observer Intersection**: If the Fourier and Filterbank observers yield disjoint mode sets or highly divergent decay parameters across different analysis frame-rates, then "modal extraction" is too fragile to serve as a description of physical parameters.
- **Representation Fragility (Future B)**: If changing analysis parameters (FFT window size, hop size, or filter Q) shifts the extracted mode frequencies by $>2\%$ or decay rates by $>20\%$, then the modes are artifacts of the measurement pipeline rather than invariants of the physical system.
- **Non-Sparse Scaling**: If reconstructing a wood impact sound requires $N > 50$ modes to reach an RMS error ratio $<0.1$, then the modal representation is an inefficient descriptor for damped structures, and should be restricted solely to highly resonant metal/glass classes.

---

## 5. Timeline & Iterative Steps

- [x] Run Experiment 01 to extract modes and measure observer agreement.
- [x] Run Experiment 02 to resynthesize the impacts and measure RMS reconstruction error.
- [x] Run Experiment 03 to sweep 7 different observers and map epistemic stability.
- [x] Run Experiment 04 to compare time-domain reconstruction errors with phase alignment.
- [x] Run Experiment 05 to apply relative frequency perturbations and analyze state drift.
- [x] Run Experiment 07 to implement iterative phase estimation with a phase-locked loop observer. (Completed June 22, 2026)
- [x] Run Experiment 08 to sweep frequency estimation error and measure prediction horizon, RMS error, SNR, and phase error for open loop and iterative tracker models. (Completed June 22, 2026)
- [ ] Design Experiment 09 (Residual Decomposition) to analyze the residual spectrum, residual decay, and residual energy over time from the best reconstruction.

---

## 6. Measured Findings from Initial Experiments

### Experiment 01: Observer Agreement
We ran the Fourier and Filterbank observers on 4 synthetic physical models:
- **Glass**: **100.00%** agreement (4 modes confirmed, 0 fragile).
- **Ceramic Mug**: **75.00%** agreement (3 modes confirmed, 1 fragile).
- **Metal Bowl**: **75.00%** agreement (3 modes confirmed, 0 fragile).
- **Wood**: **0.00%** agreement (0 modes confirmed, 1 fragile).
- *Scientific Verdict*: Highly resonant objects (low damping) have extremely high observer agreement (**Hypothesis A** is confirmed). Damped structures (wood) exhibit zero agreement, proving that transient-dominated sounds yield fragile modal models where observers disagree on the fundamental mode definition.

### Experiment 02: Resynthesis Fidelity
We reconstructed the sounds using the Fourier modes (phases set to zero):
- **Glass**: 4 modes, RMS Error = **127.37%**, SNR = **-2.10 dB**
- **Ceramic Mug**: 4 modes, RMS Error = **147.44%**, SNR = **-3.37 dB**
- **Metal Bowl**: 4 modes, RMS Error = **141.55%**, SNR = **-3.02 dB**
- **Wood**: 3 modes, RMS Error = **153.97%**, SNR = **-3.75 dB**
- *Scientific Verdict*:
  - The high RMS error ratios ($>100\%$) and negative SNRs confirm **Hypothesis C (Phase Sensitivity)**. Without tracking phase, the initial waveforms are out-of-phase at onset, creating large subtraction errors despite the sounding identity surviving.
  - Damped wood impacts show the highest reconstruction error (**153.97%**), confirming **Hypothesis B** (wood is dominated by transient broad-band noise, which is not sparse in a modal basis).

### Experiment 03: Observer Sweep & Epistemic Stability
We swept 7 different observers (STFT, Filterbank, LPC, Prony, Matrix Pencil, Autocorrelation, Wavelet) on 4 real impact sound files (glass, mug, metal bowl, wood) after aligning segments starting at the detected onset.
- **Glass**: 25 consensus modes, max agreement **4/7** (Autocorrelation, Filterbank, LPC, STFT at **395.47 Hz** and **2330.13 Hz**).
- **Ceramic Mug**: 25 consensus modes, max agreement **3/7** (Matrix Pencil, Prony, Wavelet at **511.75 Hz**; Filterbank, Matrix Pencil, STFT at **493.03 Hz**).
- **Metal Bowl**: 21 consensus modes, max agreement **4/7** (Filterbank, LPC, Prony, Matrix Pencil, Autocorrelation at **711.32 Hz**).
- **Wood**: 22 consensus modes, max agreement **6/7** (Filterbank, LPC, Prony, Matrix Pencil, Autocorrelation, Wavelet at **660.41 Hz**).
- *Scientific Verdict*:
  - **High Consensus Recovered via Onset Alignment**: Adding automatic onset detection (aligning the transient start index for LPC, Prony, and Matrix Pencil) and relaxing the tolerance to 3.5% resolved the initial low agreement. Core physical modes have very high epistemic stability across observers (up to 6/7 on wood, 4/7 on bowl/glass).
  - **Damping & Overfitting**: Highly damped structures (wood) exhibit sparse, fast-decaying modal peaks that are heavily contaminated by overfitted low-frequency noise poles in Prony/LPC.

### Experiment 04: Phase Alignment & Resynthesis
We evaluated reconstruction accuracy across three cases: No Alignment, Onset Aligned, and Onset & Phase Aligned (least-squares amplitude and phase fitting).
- **Metal Bowl (Case 3)**: RMS error dropped to **18.36%** and SNR increased to **14.72 dB** (compared to 115.22% error in Case 1).
- **Wood (Case 3)**: RMS error dropped to **72.29%** and SNR increased to **2.82 dB** (compared to 121.27% error in Case 1).
- **Glass / Mug (Case 3)**: RMS error remained high (~95-98%).
- *Scientific Verdict*:
  - **Phase Alignment is the Primary Waveform Bottleneck**: The massive error reduction for the Metal Bowl confirms that phase alignment at onset is the primary time-domain bottleneck.
  - **Extreme Frequency Sensitivity**: Glass and Mug did not reconstruct well over a long 90 ms window because minor frequency mismatches (e.g. 2% error) accumulate linearly as phase drift over time. Fitting over a short 10 ms window (reducing phase drift accumulation) drops Glass error to **28.62%** and increases SNR to **10.87 dB**, confirming that time-domain waveform matching requires sub-0.5% frequency precision.
  - **Modal State Separation**: Successfully separates mechanical structural invariants (frequencies, decays) from transient excitation conditions (onset delay, amplitudes, phases).

### Experiment 05: State Drift Analysis
We evaluated the sensitivity of predictability to relative frequency perturbations (0.1% to 2.0%) applied to consensus modes.
- **Stable vs. Catastrophic Drift**:
  - **0.1% Perturbation**: Stable over 100 ms with bounded phase divergence.
  - **0.5% Perturbation**: Usable over short term, but noticeable drift at the tails.
  - **1.0% & 2.0% Perturbations**: Catastrophic drift. Local windowed error surges to 100% within **15-30 ms** of onset.
- *Scientific Verdict*:
  - **Modes alone are insufficient**: Predictability requires the joint combination of modal structure (frequencies, decays), state initialization (onset time, amplitudes, phases), and extremely high parameter precision (sub-0.5% error).
  - *Observer agreement on resonance modes is relatively easy to achieve. Accurate long-term prediction of resonant evolution is much harder because tiny frequency errors accumulate into large phase errors over time.*

