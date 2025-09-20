# Phase-based Model Evaluation: v4, v4.1, v4.2 Comprehensive Analysis

**평가 일시**: 2025-09-20T03:36:39.611860
**평가 모델**: v4_model, v4_1_temporal, v4_2_enhanced
**분석 구간**: initial_phase, middle_phase, final_phase

## 📊 Executive Summary

**전체 최고 모델**: v4_model (81.4%)
**전체 최악 모델**: v4_2_enhanced (30.5%)
**가장 일관된 모델**: v4_model (표준편차: 10.5%)

## 🔍 Phase-by-Phase Evaluation

### Initial Phase
**실제 QPS**: 138,769 ops/sec

| Model | Predicted S_max | Accuracy | Error Rate | Grade | Direction |
|-------|----------------|----------|------------|-------|----------|
| v4.model | 185,000 | 66.7% | 33.3% | Fair | over_prediction |
| v4.1.temporal | 95,000 | 68.5% | 31.5% | Fair | under_prediction |
| v4.2 | 33,132 | 23.9% | 76.1% | Very Poor | under_prediction |

### Middle Phase
**실제 QPS**: 114,472 ops/sec

| Model | Predicted S_max | Accuracy | Error Rate | Grade | Direction |
|-------|----------------|----------|------------|-------|----------|
| v4.model | 125,000 | 90.8% | 9.2% | Excellent | over_prediction |
| v4.1.temporal | 118,000 | 96.9% | 3.1% | Excellent | over_prediction |
| v4.2 | 119,002 | 96.0% | 4.0% | Excellent | over_prediction |

### Final Phase
**실제 QPS**: 109,678 ops/sec

| Model | Predicted S_max | Accuracy | Error Rate | Grade | Direction |
|-------|----------------|----------|------------|-------|----------|
| v4.model | 95,000 | 86.6% | 13.4% | Good | under_prediction |
| v4.1.temporal | 142,000 | 70.5% | 29.5% | Good | over_prediction |
| v4.2 | 250,598 | -28.5% | 128.5% | Very Poor | over_prediction |

## 📈 Model Performance Patterns

### V4.MODEL
**평균 정확도**: 81.4%
**일관성**: high
**최고 성능 구간**: middle_phase (90.8%)
**최악 성능 구간**: initial_phase (66.7%)
**예측 편향**: over_prediction

### V4.1.TEMPORAL
**평균 정확도**: 78.6%
**일관성**: high
**최고 성능 구간**: middle_phase (96.9%)
**최악 성능 구간**: initial_phase (68.5%)
**예측 편향**: over_prediction

### V4.2
**평균 정확도**: 30.5%
**일관성**: low
**최고 성능 구간**: middle_phase (96.0%)
**최악 성능 구간**: final_phase (-28.5%)
**예측 편향**: over_prediction

## 💡 Key Insights

- 전체 최고 성능: v4_model (81.4%)
- Initial Phase 최고: v4_1_temporal (68.5%)
- Middle Phase 최고: v4_1_temporal (96.9%)
- Final Phase 최고: v4_model (86.6%)

## ⚖️ Model Strengths and Weaknesses

### V4.MODEL
**강점**:
- 높은 평균 정확도
- 일관된 성능
- middle_phase에서 우수한 성능 (90.8%)

**약점**:
- over_prediction 편향

### V4.1.TEMPORAL
**강점**:
- 높은 평균 정확도
- 일관된 성능
- middle_phase에서 우수한 성능 (96.9%)

**약점**:
- over_prediction 편향

### V4.2
**강점**:
- middle_phase에서 우수한 성능 (96.0%)

**약점**:
- 낮은 평균 정확도
- 불일관한 성능
- over_prediction 편향
- final_phase에서 낮은 성능 (-28.5%)

## 🎯 Recommendations

- Middle Phase에서 모든 모델이 상대적으로 우수한 성능을 보임
- Initial Phase와 Final Phase에서 모델 개선이 필요
- v4.2 Enhanced 모델의 Level-wise 접근법이 유망함
- 구간별 특성을 고려한 하이브리드 모델 개발 권장

