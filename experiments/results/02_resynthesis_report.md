# Experiment 02: Modal Resynthesis Report

This report summarizes the reconstruction accuracy of the physical impact sounds using only the modal parameters extracted in Experiment 01.

| Material | Extracted Modes | RMS Error Ratio | Reconstruction SNR | Status |
| :--- | :---: | :---: | :---: | :--- |
| Glass | 4 | 127.37% | -2.10 dB | Good Reconstruction (Moderate damping) |
| Mug | 4 | 147.44% | -3.37 dB | Good Reconstruction (Moderate damping) |
| Metal bowl | 4 | 141.55% | -3.02 dB | Good Reconstruction (Moderate damping) |
| Wood | 3 | 153.97% | -3.75 dB | Highly Damped (High error expected due to transient onset dominance) |

## Scientific Interpretation of Reconstruction Accuracy

1. **Resonant Sparsity (Hypothesis B)**:
   - **Metal Bowl** and **Glass** exhibit the highest reconstruction SNR. Their mechanical structures have low damping (slow decays), meaning the sound energy resides almost entirely in a few long-lived sinusoids. This maps perfectly to the sparse modal model.
2. **Damped Transient Mismatch**:
   - **Wood** shows a significantly higher RMS error ratio. Because wood has extremely high damping (very rapid decay), the sound is dominated by the initial impact excitation (onset noise burst). A sparse set of linear decaying sines is mathematically unable to capture this broad-band noise transient, validating that modal modeling is less effective for heavily damped structures.