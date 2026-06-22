# Experiment 16: Coupled Dynamic Modal Synthesis Report

This experiment compares independent dynamic modes against explicit coupling between the strong mode pairs from Experiment 15.

## Overall Classification

Residual classification accuracy, independent model: **97.22%**
Residual classification accuracy, coupled model: **97.22%**
Classification gap (independent - coupled): **0.00%**

## Per-Material Reconstruction

| Material | Indep RMS | Coupled RMS | Indep SNR | Coupled SNR | Indep Residual Energy | Coupled Residual Energy | Improvement |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| glass | 89.01% | 89.01% | 1.01 | 1.01 | 79.22% | 79.22% | 0.00% |
| mug | 99.96% | 99.96% | 0.00 | 0.00 | 99.92% | 99.92% | -0.00% |
| metal_bowl | 83.31% | 83.31% | 1.59 | 1.59 | 69.41% | 69.41% | 0.00% |
| wood | 93.99% | 95.88% | 0.54 | 0.37 | 88.34% | 91.93% | -2.01% |

## Per-Class Residual Identification

| Material | Indep Residual Acc | Coupled Residual Acc |
| :--- | :---: | :---: |
| glass | 100.00% | 100.00% |
| mug | 100.00% | 100.00% |
| metal_bowl | 100.00% | 100.00% |
| wood | 88.89% | 88.89% |

## Interpretation

If the coupled synthesizer lowers RMS error and reduces residual-classification accuracy, explicit interaction is explaining structure that the independent model leaves behind.
If it does not, then the coupling graph is not yet strong enough or the remaining error is due to missing mechanisms beyond pairwise interaction.

### Conclusion
> [!IMPORTANT]
> **Experiment 16 asks whether pairwise coupling between modes reduces the leftover error more effectively than independent dynamic synthesis. A reduction in residual energy and residual identifiability would support a coupled-resonator synthesis architecture.**