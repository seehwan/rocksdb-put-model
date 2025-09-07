# RocksDB Put Model 실험 - 2025-09-08

## 실험 개요
RocksDB Put Model v4의 추가 검증 및 성능 분석을 위한 종합 실험입니다.

## 실험 목적
- **v4 모델 추가 검증**: 다양한 조건에서의 모델 정확도 검증
- **성능 최적화**: 모델 파라미터 최적화 방안 탐색
- **장기 안정성**: 지속적인 성능 모니터링 및 분석
- **실용성 검증**: 실제 운영 환경에서의 적용 가능성 평가

## 실험 구조

### Phase-A: Device Calibration
- **목적**: 디바이스 I/O 성능 정확 측정
- **도구**: fio 벤치마크
- **출력**: B_w, B_r, B_eff 값

### Phase-B: Actual Performance Measurement  
- **목적**: 실제 RocksDB 성능 측정
- **도구**: RocksDB db_bench
- **출력**: S_actual, OPS_actual 값

### Phase-C: Write Amplification Analysis
- **목적**: 정확한 WA 값 측정
- **도구**: LOG 파일 분석기
- **출력**: WA_log, WA_statistics 값

### Phase-D: v4 Model Validation
- **목적**: v4 모델 정확도 검증
- **도구**: v4 시뮬레이터
- **출력**: 예측 정확도, 오류율

### Phase-E: Sensitivity Analysis
- **목적**: 파라미터 민감도 분석
- **도구**: 민감도 분석기
- **출력**: 민감도 지수, 상관관계

## 실험 환경
- **서버**: GPU-01
- **디바이스**: /dev/nvme1n1p1
- **OS**: Linux
- **RocksDB**: 최신 안정 버전
- **Python**: 3.10+

## 실험 데이터
- **설정 파일**: `experiment_data.json`
- **로그 파일**: 각 Phase별 로그
- **결과 파일**: 각 Phase별 결과 JSON

## 실행 순서
1. **Phase-A**: 디바이스 캘리브레이션
2. **Phase-B**: 실제 성능 측정
3. **Phase-C**: WA 분석
4. **Phase-D**: v4 모델 검증
5. **Phase-E**: 민감도 분석

## 예상 결과
- **v4 모델 오류율**: < 10%
- **등급**: Excellent
- **개선도**: v1 대비 95% 이상

## 상태
- [ ] Phase-A: Device Calibration
- [ ] Phase-B: Actual Performance Measurement
- [ ] Phase-C: Write Amplification Analysis
- [ ] Phase-D: v4 Model Validation
- [ ] Phase-E: Sensitivity Analysis

## 파일 구조
```
2025-09-08/
├── README.md                    # 이 파일
├── experiment_data.json         # 실험 데이터
├── phase-a/                     # 디바이스 캘리브레이션
│   └── README.md
├── phase-b/                     # 실제 성능 측정
│   └── README.md
├── phase-c/                     # WA 분석
│   └── README.md
├── phase-d/                     # v4 모델 검증
│   └── README.md
└── phase-e/                     # 민감도 분석
    └── README.md
```

## 참고사항
- 이 실험은 2025-09-05 실험의 후속 실험입니다
- v4 모델의 정확성을 추가로 검증합니다
- 다양한 워크로드 패턴에서의 성능을 분석합니다
