# Resonance Intelligence

A research laboratory and code repository investigating how natural resonances are extracted, modeled, manipulated, and resynthesized from real-world impact sounds. 

Repository: `git@github.com:SpacekidLabs/Resonance-Intelligence.git`

This project is strictly scientific and focused on mechanical vibration modeling and signal processing analysis. It is **not** a synthesizer plugin project and **not** a machine learning project.

---

## 1. Project Motivation & Research Philosophy

When we strike a physical object (like a glass or a wooden block), it vibrates at its natural resonant frequencies (modes). However, when we analyze these impact sounds using digital signal processing, a critical question emerges:

> Which extracted resonances correspond to real, invariant physical modes of the object, and which are artifacts (spectral leakage, windowing side-lobes, frame-rate dependencies) of a particular analysis method?

To answer this, we treat resonance analysis not as a settled engineering technique, but as a system of observation. We hold ourselves to the following research principles:
- **Experiments First**: Every claim must be backed by a runnable script that reproduces the figures and metrics.
- **Measurements Before Conclusions**: We do not speculate on the physics of an object without empirical measurements of observer agreement.
- **Adversarial Stress Testing**: We actively try to design signal structures (e.g., closely-spaced modes, rapid pitch glides) that fool our extraction algorithms to map their boundaries of validity.
- **Willingness to Invalidate Assumptions**: If the data shows that modal parameters are fragile and change significantly across observation windows, we do not claim to have found "physical modes".

---

## 2. Directory Structure

```text
Resonance-Intelligence/
├── README.md
├── ROADMAP.md
├── requirements.txt
├── resonance/
│   ├── __init__.py
│   ├── extraction.py      # Dual-observer extraction algorithms (Fourier & Filterbank)
│   ├── modal.py           # Dataclasses representing modes and collections
│   ├── synthesis.py       # Re-synthesis engine based on exponential decaying sines
│   └── visualization.py   # Plotting utilities for waveforms, spectrograms, and errors
└── experiments/
    ├── 01_modal_extraction.py
    ├── 02_modal_resynthesis.py
    └── results/           # Extracted parameter JSONs and comparison plots
```

---

## 3. Initial Experiments

### Experiment 01 — Modal Extraction
- **Goal**: Extract dominant resonance parameters (frequency, initial amplitude, decay rate) from physical impact recordings representing four material classes: **glass, ceramic mug, metal bowl, and wooden object**.
- **Observer Agreement Check**: We run two distinct mathematical observers on each sound:
  1. **Fourier Observer**: Employs Short-Time Fourier Transform peak-picking followed by linear regression on the log-magnitude trace to extract exponential decay.
  2. **Filterbank Observer**: Employs a bank of highly selective second-order IIR bandpass resonators tuned to peak frequencies, extracting the envelope decay directly in the time domain.
- **Output**: Generates a unified JSON file `experiments/results/01_modes.json` containing the extracted modal parameters.

### Experiment 02 — Modal Resynthesis
- **Goal**: Reconstruct the four impact signals using only the parameters extracted in Experiment 01.
- **Model**:
  $$x(t) = \sum_{i} A_i e^{-d_i t} \sin(2\pi f_i t + \phi_i)$$
- **Error Evaluation**: Compares the original waveform and spectrogram with the resynthesized counterpart, plotting the time-varying reconstruction error and computing the final RMS ratio error.
- **Output**: Generates comparison plots in `experiments/results/` for visual verification.

---

## 4. Getting Started

### Installation
Clone the repository and install the dependencies:
```bash
git clone git@github.com:SpacekidLabs/Resonance-Intelligence.git
cd Resonance-Intelligence
pip install -r requirements.txt
```

### Running the Lab
To execute the modal extraction sweep:
```bash
python3 experiments/01_modal_extraction.py
```
To run the modal resynthesis and generate comparison plots:
```bash
python3 experiments/02_modal_resynthesis.py
```
All outputs will be saved to the `experiments/results/` directory.
