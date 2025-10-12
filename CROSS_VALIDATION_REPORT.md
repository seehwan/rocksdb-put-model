# RocksDB Put-Rate Model Cross-Validation Analysis
## 다중 실험 데이터를 통한 모델 성능 일관성 검증

**Generated**: 2025-09-20 09:37:13
**Experiments**: ['2025-09-05', '2025-09-08', '2025-09-09', '2025-09-12']
**Models Evaluated**: V4, V4.1, V5

---

## 🎯 Executive Summary

**🏆 Best Performing Model**: V4
- **Average Accuracy**: 90.7%
- **Consistency Score**: 93.4/100
- **Experiments Tested**: 2

## 📊 Model Performance Summary

| Model | Mean Accuracy | Std Dev | Min | Max | Consistency | Experiments |
|-------|---------------|---------|-----|-----|-------------|-------------|
| **V4** | 90.7% | ±6.0% | 84.7% | 96.7% | 93.4/100 | 2 |
| **V4.1** | 73.7% | ±11.1% | 62.6% | 84.8% | 84.9/100 | 2 |
| **V5_FINAL** | 52.1% | ±4.9% | 47.2% | 57.0% | 90.6/100 | 2 |

## 🔍 Experiment-by-Experiment Results

### 📅 2025-09-05 Experiment

| Model | Predicted QPS | Actual QPS | Accuracy | Error |
|-------|---------------|------------|----------|-------|
| **V4** | 182,354 | 188,617 | 96.7% | 3.3% |
| **V4.1** | 217,305 | 188,617 | 84.8% | 15.2% |
| **V5_FINAL** | 89,020 | 188,617 | 47.2% | 52.8% |

### 📅 2025-09-08 Experiment

| Model | Predicted QPS | Actual QPS | Accuracy | Error |
|-------|---------------|------------|----------|-------|
| **V4** | 174,612 | 151,432 | 84.7% | 15.3% |
| **V4.1** | 208,080 | 151,432 | 62.6% | 37.4% |
| **V5_FINAL** | 86,323 | 151,432 | 57.0% | 43.0% |

### 📅 2025-09-09 Experiment

❌ No predictions available for this experiment

### 📅 2025-09-12 Experiment

❌ No predictions available for this experiment

## 📈 Consistency Analysis

### 🎯 Key Findings

1. **Most Consistent Model**: V4 (Consistency Score: 93.4/100)
2. **Performance vs Consistency Trade-off**:
   - V4: 90.7% accuracy, 93.4/100 consistency
   - V4.1: 73.7% accuracy, 84.9/100 consistency
   - V5_FINAL: 52.1% accuracy, 90.6/100 consistency

3. **Cross-Experiment Variability**:
   - V4: 6.6% coefficient of variation
   - V4.1: 15.1% coefficient of variation
   - V5_FINAL: 9.4% coefficient of variation

## 🎯 Recommendations

✅ **V4 모델 사용 권장**: 높은 정확도와 우수한 일관성을 보임

---
*Cross-validation analysis completed at 2025-09-20 09:37:13*
