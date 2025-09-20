# V5 Adaptive Phase-Specific Model

## 🎯 Model Overview

**V5 Adaptive Model**은 구간별로 가장 중요한 요소들에 집중하는 적응형 RocksDB 성능 예측 모델입니다.

**Model Version**: v5.0_adaptive
**Creation Date**: 2025-09-20T05:01:57.493761
**Design Philosophy**: 구간별 중요 요소에 집중하는 적응형 접근법

## 🏗️ Design Principles

- **Adaptive Strategy**: Phase-specific factor weighting
- **Core Philosophy**: 각 구간에서 가장 중요한 요소들에 집중
- **Complexity Balance**: 필요한 만큼만 복잡하게
- **Trend Awareness**: 실제 성능 감소 트렌드 반영

## 🔍 Phase-Specific Models

### Initial Phase
**Model Type**: Device Performance Focused
**Primary Equation**: `S_max_initial = Device_Write_BW * volatility_adjustment * trend_adjustment`

**Key Factors**:
- **Device Write Bw** (Weight: 0.7)
  - Implementation: Direct measurement integration
  - Formula: `base_performance = device_write_bw * utilization_factor`
- **Volatility Adjustment** (Weight: 0.2)
  - Implementation: CV-based penalty
  - Formula: `volatility_penalty = 1 - (cv * 0.3)`
- **Trend Adjustment** (Weight: 0.1)
  - Implementation: Slope-based adjustment
  - Formula: `trend_factor = 1 + (trend_slope * 0.1)`

**Model Equation**: `S_max = (device_write_bw * 1024 * 1024 / 1040) * (1 - cv * 0.3) * (1 + trend_slope * 0.1)`
**Expected Accuracy**: 70-80%

### Middle Phase
**Model Type**: Degradation + Amplification Focused
**Primary Equation**: `S_max_middle = degraded_device_performance / (wa_penalty * compaction_penalty)`

**Key Factors**:
- **Device Degradation** (Weight: 0.5)
  - Implementation: Phase-A degradation data
  - Formula: `degraded_bw = initial_bw * (1 - degradation_rate)`
- **Wa Penalty** (Weight: 0.3)
  - Implementation: Direct WA impact
  - Formula: `wa_penalty = 1 + (wa - 1) * 0.4`
- **Compaction Intensity** (Weight: 0.2)
  - Implementation: Compaction load factor
  - Formula: `compaction_penalty = 1 + compaction_intensity * 0.2`

**Model Equation**: `S_max = (degraded_write_bw * 1024 * 1024 / 1040) / ((1 + (wa-1)*0.4) * (1 + compaction_intensity*0.2))`
**Expected Accuracy**: 90-95%

### Final Phase
**Model Type**: Amplification + Stability Focused
**Primary Equation**: `S_max_final = base_performance / combined_amplification_penalty * stability_bonus`

**Key Factors**:
- **Combined Amplification** (Weight: 0.6)
  - Implementation: WA + RA combined penalty
  - Formula: `amplification_penalty = (wa + ra) * 0.3`
- **Stability Bonus** (Weight: 0.3)
  - Implementation: Low CV stability bonus
  - Formula: `stability_bonus = 1 + (1 - cv) * 0.2`
- **Level Complexity** (Weight: 0.1)
  - Implementation: Deep level penalty
  - Formula: `level_penalty = 1 + level_depth * 0.05`

**Model Equation**: `S_max = (base_performance / ((wa + ra) * 0.3)) * (1 + (1-cv) * 0.2) / (1 + level_depth * 0.05)`
**Expected Accuracy**: 80-90%

## 📊 Performance Evaluation

### V5 Model Performance
| Phase | Predicted S_max | Actual QPS | Accuracy | Error Rate |
|-------|----------------|------------|----------|------------|
| Initial Phase | 119,874 | 138,769 | 86.4% | 13.6% |
| Middle Phase | 130,620 | 114,472 | 85.9% | 14.1% |
| Final Phase | 208,243 | 109,678 | 10.1% | 89.9% |

### Model Comparison
| Model | Average Accuracy | Ranking |
|-------|------------------|----------|
| v4.model | 81.4% | 1 |
| v4.1.temporal | 78.6% | 2 |
| V5 | 60.8% | 3 |
| v4.2 | 30.5% | 4 |

## 🚀 Key Innovations

- **Adaptive Approach**: 구간별 특화 모델링
- **Factor Prioritization**: 구간별 핵심 요소 집중
- **Empirical Calibration**: 실제 데이터 기반 보정
- **Trend Awareness**: 실제 성능 감소 트렌드 반영

## 🎯 Conclusion

**V5 Adaptive Model**은 평균 60.8% 정확도를 달성하여 전체 4개 모델 중 3위를 기록했습니다.

구간별 적응형 접근법을 통해 각 Phase의 핵심 요소에 집중함으로써 기존 모델들의 한계를 극복하고자 했습니다.
