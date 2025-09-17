# RocksDB Put-Rate Model v3 분석 보고서

## 1. 모델 개요
RocksDB Put-Rate Model v3은 Dynamic Compaction-Aware 모델로, Stall dynamics와 Backlog evolution을 고려한 휴리스틱 기반 S_max 계산 모델입니다.

## 2. 분석 결과
- **예측된 S_max (지속 가능한 Put Rate):** `6048.62 ops/sec`
- **Phase-B 실제 평균 QPS:** `120972.36 ops/sec`
- **예측 비율:** `5.00%` (95% under-prediction)

### 상세 분석 결과:
- **Stall Factor:** `1.0000`
- **P_stall:** `0.0000`
- **모델 타입:** `Dynamic Compaction-Aware`
- **휴리스틱 기반:** `True`
- **Under-prediction Error:** `95.0%`

### Phase-B 비교 결과:
- **오류율:** `1900.00%`
- **검증 상태:** `Poor`
- **Under-prediction:** `False`


## 3. 시각화
![v3 Model Analysis](results/v3_model_analysis.png)

