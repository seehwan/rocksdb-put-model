# Model Evaluation with LOG-based Phase Segmentation

## Analysis Time
2025-09-19 11:46:15

## Overview
This report evaluates the v4.2 model using LOG-based phase segmentation results.
The evaluation compares model predictions with actual LOG-based performance characteristics.

## Evaluation Results

### Initial Phase

**LOG-based Characteristics:**
- Average Performance: 17.1 MB/s
- Stability: low
- Performance Level: medium
- CV: 0.356
- Duration: 32.2 hours

**Model Predictions:**
- S_max: 1209794.6 ops/sec
- Adjusted Write BW: 1199.9 MB/s
- Degradation Factor: 0.000
- Stability Factor: 0.200

**Evaluation Scores:**
- Overall Score: -26.910
- Performance Accuracy: -68.009
- Stability Match: 0.980
- Characteristics Evaluation: 0.000

---

### Middle Phase

**LOG-based Characteristics:**
- Average Performance: 13.2 MB/s
- Stability: high
- Performance Level: low
- CV: 0.027
- Duration: 32.2 hours

**Model Predictions:**
- S_max: 767261.6 ops/sec
- Adjusted Write BW: 761.0 MB/s
- Degradation Factor: 0.000
- Stability Factor: 0.500

**Evaluation Scores:**
- Overall Score: -22.107
- Performance Accuracy: -55.672
- Stability Match: 0.540
- Characteristics Evaluation: 0.000

---

### Final Phase

**LOG-based Characteristics:**
- Average Performance: 12.3 MB/s
- Stability: high
- Performance Level: low
- CV: 0.013
- Duration: 32.2 hours

**Model Predictions:**
- S_max: 185014.7 ops/sec
- Adjusted Write BW: 183.5 MB/s
- Degradation Factor: 0.000
- Stability Factor: 0.800

**Evaluation Scores:**
- Overall Score: -4.964
- Performance Accuracy: -12.905
- Stability Match: 0.660
- Characteristics Evaluation: 0.000

---

## Overall Evaluation Summary

**Average Overall Score: -17.994**

### Score Interpretation:
- **0.8-1.0**: Excellent match
- **0.6-0.8**: Good match
- **0.4-0.6**: Moderate match
- **0.0-0.4**: Poor match

### Key Findings:
- **Initial Phase**: Poor (-26.910)
- **Middle Phase**: Poor (-22.107)
- **Final Phase**: Poor (-4.964)

## Analysis Time
2025-09-19 11:46:15

