# V4.2 Model Evaluation with Phase-B Results

**평가 일시**: 2025-09-19T20:20:08.828775
**모델 버전**: v4.2_enhanced_level_wise_temporal

## Overall Assessment

**평가 등급**: Poor
**평가 설명**: 모델의 정확도가 낮으며 대폭적인 개선 필요
**평균 정확도**: 30.5%

## Phase-by-Phase Evaluation

| Phase | Actual QPS | Predicted S_max | Accuracy | Error Rate | Direction |
|-------|------------|-----------------|----------|------------|----------|
| Initial Phase | 138,769 | 33,132 | 23.9% | 76.1% | under_prediction |
| Middle Phase | 114,472 | 119,002 | 96.0% | 4.0% | over_prediction |
| Final Phase | 109,678 | 250,598 | -28.5% | 128.5% | over_prediction |

## Pattern Analysis

- **정확도 트렌드**: variable
- **과대 예측**: 2개 시기
- **과소 예측**: 1개 시기
- **평균 정확도**: 30.5%
- **정확도 표준편차**: 51.1%
- **정확도 일관성**: low
- **예측 편향**: over_prediction

## Strengths and Weaknesses

### Strengths
- 일부 시기에서 높은 정확도 달성 (90% 이상)
- middle_phase에서 최고 성능 (96.0% 정확도)

### Weaknesses
- 일부 시기에서 낮은 정확도 (50% 미만)
- 과대 예측 경향 (실제보다 높게 예측)
- final_phase에서 개선 필요 (-28.5% 정확도)

## Recommendations

- 모델 파라미터 재조정 필요
- 과대 예측 경향 보정 필요
- 시기별 정확도 일관성 개선 필요

