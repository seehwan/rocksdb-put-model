# Phase-D: v4 Model Validation (2025-09-08)

## 목적
Phase-A, B, C에서 수집한 실제 데이터를 바탕으로 v4 모델의 정확성을 검증합니다.

## 검증 방법
- **Device Envelope Modeling**: Phase-A fio 데이터 활용
- **Closed Ledger Accounting**: Phase-C WA 데이터 활용
- **실제 성능 비교**: Phase-B 측정값과 예측값 비교

## 검증 절차

### 1. v4 모델 파라미터 설정
```python
# Phase-A 결과 반영
B_w = phase_a_results['write_bandwidth_mib_s']
B_r = phase_a_results['read_bandwidth_mib_s']
B_eff = phase_a_results['mixed_bandwidth_mib_s']

# Phase-C 결과 반영
WA = phase_c_results['log_wa']
CR = phase_c_results['compression_ratio']
```

### 2. v4 모델 실행
```python
# v4 시뮬레이터 실행
from model.v4_simulator import V4Simulator

simulator = V4Simulator(
    device_bandwidths={'write': B_w, 'read': B_r, 'mixed': B_eff},
    write_amplification=WA,
    compression_ratio=CR
)

predicted_s_max = simulator.predict_s_max()
```

### 3. 정확도 계산
```python
# Phase-B 실제 측정값과 비교
actual_s_max = phase_b_results['put_rate_mib_s']
error_percent = abs(predicted_s_max - actual_s_max) / actual_s_max * 100
```

## 검증 기준

### 1. 정확도 등급
- **Excellent**: < 10% 오류
- **Good**: 10-20% 오류
- **Fair**: 20-50% 오류
- **Poor**: > 50% 오류

### 2. 목표 성능
- **v4 모델**: < 10% 오류율 달성
- **개선도**: v1 대비 90% 이상 개선

## 검증 항목

### 1. 기본 예측 정확도
- **S_max 예측**: 실제 put rate와 비교
- **병목 지점**: 예측된 병목과 실제 병목 비교
- **레벨별 I/O**: 각 레벨의 I/O 분배 예측

### 2. 파라미터 민감도
- **WA 영향**: Write Amplification 변화에 대한 민감도
- **CR 영향**: Compression Ratio 변화에 대한 민감도
- **대역폭 영향**: 디바이스 대역폭 변화에 대한 민감도

### 3. 동적 특성
- **시간별 변화**: 시간에 따른 성능 변화 예측
- **Stall 모델링**: Write stall 현상 정확도
- **과도기 동역학**: 초기 버스트 구간 예측

## 예상 결과
- **v4 모델 오류율**: < 10%
- **등급**: Excellent
- **개선도**: v1 대비 95% 이상

## 상태
- [ ] Phase-A 데이터 반영
- [ ] Phase-C 데이터 반영
- [ ] v4 모델 실행
- [ ] 정확도 계산
- [ ] 결과 분석 및 보고서 작성
