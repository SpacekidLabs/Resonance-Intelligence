# Experiment 14: Excitation-Resonator Entanglement Report

Question: how much object information is encoded inside the excitation itself?

Each material contributes multiple 20 ms windows from the first 100 ms so the classifier has enough samples to learn from and test against.

Chance level for 4-way classification: **25.00%**
Excitation-only leave-one-out accuracy: **97.22%**
Resonator-only leave-one-out accuracy: **86.11%**
Accuracy gap (resonator - excitation): **-11.11%**

## Per-Material Accuracy

| Material | Excitation Accuracy | Resonator Accuracy |
| :--- | :---: | :---: |
| glass | 100.00% | 100.00% |
| mug | 100.00% | 44.44% |
| metal_bowl | 100.00% | 100.00% |
| wood | 88.89% | 100.00% |

## Per-Sample Predictions

| Material | Excitation Prediction | Resonator Prediction |
| :--- | :--- | :--- |
| glass | glass | glass |
| glass | glass | glass |
| glass | glass | glass |
| glass | glass | glass |
| glass | glass | glass |
| glass | glass | glass |
| glass | glass | glass |
| glass | glass | glass |
| glass | glass | glass |
| mug | mug | wood |
| mug | mug | wood |
| mug | mug | wood |
| mug | mug | wood |
| mug | mug | wood |
| mug | mug | mug |
| mug | mug | mug |
| mug | mug | mug |
| mug | mug | mug |
| metal_bowl | metal_bowl | metal_bowl |
| metal_bowl | metal_bowl | metal_bowl |
| metal_bowl | metal_bowl | metal_bowl |
| metal_bowl | metal_bowl | metal_bowl |
| metal_bowl | metal_bowl | metal_bowl |
| metal_bowl | metal_bowl | metal_bowl |
| metal_bowl | metal_bowl | metal_bowl |
| metal_bowl | metal_bowl | metal_bowl |
| metal_bowl | metal_bowl | metal_bowl |
| wood | mug | wood |
| wood | wood | wood |
| wood | wood | wood |
| wood | wood | wood |
| wood | wood | wood |
| wood | wood | wood |
| wood | wood | wood |
| wood | wood | wood |
| wood | wood | wood |

## Interpretation

Excitation-only features exceed chance, so the excitation retains object identity information.
The excitation outperforms the resonator, which would suggest stronger entanglement than expected.

### Conclusion
> [!IMPORTANT]
> **If excitation-only classification is above chance, the excitation contains object information. That makes the failed swaps in Experiment 13 unsurprising: the excitation is not universal, it already carries some material signature.**