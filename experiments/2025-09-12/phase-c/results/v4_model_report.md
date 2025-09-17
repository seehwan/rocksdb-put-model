# RocksDB Put-Rate Model v4 분석 보고서 (수정된 버전)

## 1. 모델 개요
RocksDB Put-Rate Model v4는 Device Envelope Modeling, Closed Ledger Accounting, Dynamic Simulation Framework를 통합한 최신 모델입니다.
이 수정된 버전은 RocksDB LOG에서 정상적인 컴팩션 통계를 추출하여 사용합니다.

## 2. 분석 결과
### Device Envelope Modeling
- **초기 상태 파일 수:** `0`
- **열화 상태 파일 수:** `0`
- **성능 열화 분석:** `0` 파일

### Closed Ledger Accounting
- **실제 평균 QPS:** `0.00 ops/sec`
- **평균 초기 대역폭:** `0.00 MB/s`
- **평균 열화 대역폭:** `0.00 MB/s`
- **컴팩션 쓰기 대역폭:** `188.70 MB/s`
- **컴팩션 읽기 대역폭:** `35.68 MB/s`
- **Write Amplification:** `2.00`
- **예측 S_max:** `188700.00 ops/sec`

### RocksDB LOG 통계
- **컴팩션 쓰기 대역폭:** `188.70 MB/s`
- **컴팩션 읽기 대역폭:** `35.68 MB/s`
- **Write Amplification:** `2.00`
- **컴팩션 시간:** `5.00초`


## 3. 시각화
![v4 Model Analysis](results/v4_model_analysis.png)

