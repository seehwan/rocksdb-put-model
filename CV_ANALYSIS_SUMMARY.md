# CV 분석 요약

## 문제 발견

### 실험 데이터의 Phase별 CV
- Initial: CV = 0.356 (phase 전체의 CV)
- Middle: CV = 0.027
- Final: CV = 0.013

### Rolling CV 계산 결과
- 전체 CV 범위: 0.310 ~ 0.869
- 평균 CV: 0.497
- 중간값 CV: 0.485

## 원인

### 두 가지 다른 CV 측정:
1. **Phase-level CV**: 전체 phase 동안의 통합 CV
   - Initial phase: 32.2시간 동안의 CV = 0.356
   - 전체 기간을 통합한 단일 CV 값

2. **Rolling CV**: 슬라이딩 윈도우로 계산한 순간 CV
   - 시간에 따라 변동
   - 짧은 구간(100 샘플)의 volatility

## 해결책

CV 기반 phase 감지를 위해서는 **시간 가중 CV (time-weighted CV)** 필요:
- Phase 전체 기간의 통합 CV 사용
- 또는 장기 윈도우 (1000+ 샘플) 사용

