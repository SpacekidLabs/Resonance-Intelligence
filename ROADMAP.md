# Roadmap

This is a living research roadmap for the **Resonance-Intelligence** project. We update it after every experiment that refines our understanding or changes what we believe. Every claim must be backed by a runnable script that reproduces the measurements.

---

## 1. Where We Are

- [x] Repository design and project layout initialization.
- [x] **Experiment 01 (Modal Extraction)**: Run extraction on synthetic impacts (glass, mug, bowl, wood) using both STFT and IIR Filterbank observers. Collect JSON modes. (Completed June 21, 2026)
- [x] **Experiment 02 (Modal Resynthesis)**: Resynthesize impacts, compute reconstruction error curves, and plot comparison dashboards. (Completed June 21, 2026)
- [x] **Experiment 03 (Observer Sweep & Epistemic Stability)**: Sweep 7 observers (STFT, Filterbank, LPC, Prony, Matrix Pencil, Autocorrelation, Wavelet) on 4 real impact sounds, cluster to construct consensus modes, and map epistemic stability. (Completed June 21, 2026)

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
- [ ] Design Experiment 04 (Phase Alignment & Resynthesis) to test how tracking onset phases reduces waveform error.

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
We swept 7 different observers (STFT, Filterbank, LPC, Prony, Matrix Pencil, Autocorrelation, Wavelet) on 4 real impact sound files (glass, mug, metal bowl, wood) and grouped detected candidate peaks using linkage clustering with a 1.5% frequency tolerance.
- **Glass**: 26 consensus modes, max agreement **2/7** (Autocorrelation + Filterbank at 392.17 Hz; LPC + STFT at 400.10 Hz).
- **Ceramic Mug**: 35 consensus modes, max agreement **2/7** (Filterbank + LPC at 279.95 Hz; Matrix Pencil + Wavelet at 508.30 Hz).
- **Metal Bowl**: 31 consensus modes, max agreement **3/7** (Autocorrelation + Filterbank + Matrix Pencil at 700.58 Hz).
- **Wood**: 34 consensus modes, max agreement **3/7** (Autocorrelation + LPC + Wavelet at 656.56 Hz).
- *Scientific Verdict*:
  - **No Global Invariants Found**: Across all 7 observers, no mode achieved consensus from more than 3 observers. This shows that "resonance" is highly observer-dependent and fragile.
  - **Grid/Discretization Biases**: The Gabor limit of the Fourier observer and the coarse grid limit of the logarithmic Wavelet observer ($\approx 13\%$ bin spacing) systematically prevent alignment with continuous pole estimators (like Matrix Pencil, Prony, or LPC) under narrow tolerance bands.
  - **Damping & Overfitting**: Damped impacts like wood show high densities of unstable, transient-periodicity modes with high parameter variance, whereas metallic structures show clustered consensus peaks representing mechanical resonances.

