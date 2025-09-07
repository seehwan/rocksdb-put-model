# RocksDB Put-Rate Model 실험 디렉토리

이 디렉토리는 RocksDB Put-Rate 모델 검증 실험의 모든 결과를 날짜별로 관리합니다.

## 📁 디렉토리 구조

```
experiments/
├── README.md                    # 이 파일
├── 2025-09-05/                  # 2025년 9월 5일 실험
│   ├── experiment_data.json     # 구조화된 실험 데이터
│   ├── phase-a/                 # 디바이스 캘리브레이션 결과
│   ├── phase-b/                 # RocksDB 벤치마크 결과
│   ├── phase-c/                 # Per-Level WAF 분석 결과
│   ├── phase-d/                 # 모델 검증 결과 (v1, v2.1, v3, v4)
│   └── phase-e/                 # v4 모델 민감도 분석 결과
└── templates/                   # 실험 템플릿들
    ├── device_calibration.md
    ├── rocksdb_benchmark.md
    └── model_validation.md
```

## 🗓️ 실험 일정

| 날짜 | Phase | 상태 | 비고 |
|------|-------|------|------|
| 2025-09-05 | Phase-A | ✅ 완료 | 디바이스 캘리브레이션 |
| 2025-09-05 | Phase-B | ✅ 완료 | RocksDB 벤치마크 |
| 2025-09-05 | Phase-C | ✅ 완료 | Per-Level WAF 분석 |
| 2025-09-05 | Phase-D | ✅ 완료 | 모델 검증 (v4: 5.0% 오류율) |
| 2025-09-05 | Phase-E | ✅ 완료 | v4 모델 민감도 분석 |

## 📋 실험 진행 가이드

### 1. 새로운 실험 시작
```bash
# 오늘 날짜로 디렉토리 생성
mkdir -p experiments/$(date +%Y-%m-%d)

# 템플릿 복사
cp experiments/templates/* experiments/$(date +%Y-%m-%d)/
```

### 2. 실험 결과 저장
각 Phase별로 결과를 해당 디렉토리에 저장:
- `phase-a/`: fio 결과, 성능 측정값
- `phase-b/`: RocksDB LOG, 벤치마크 결과
- `phase-c/`: WAF 분석 결과, 그래프
- `phase-d/`: 모델 검증 결과, 오류율
- `phase-e/`: 민감도 분석 결과

### 3. 실험 완료 후
- `experiment_results.md` 업데이트
- `experiment_data.json` 업데이트
- 최종 결과를 프로젝트 루트에 요약본 생성

## 🔍 실험 결과 조회

### 특정 날짜 실험 결과 보기
```bash
# 2025-09-05 실험 결과
cat experiments/2025-09-05/experiment_results.md

# JSON 데이터 조회
cat experiments/2025-09-05/experiment_data.json | jq '.s_max_calculations'
```

### 모든 실험 결과 비교
```bash
# 각 날짜별 S_max 값 비교
for dir in experiments/*/; do
  echo "=== $(basename $dir) ==="
  cat $dir/experiment_data.json | jq '.s_max_calculations.raw_calculation.S_max'
done
```

## 📊 실험 데이터 형식

### JSON 스키마
```json
{
  "experiment_info": {
    "date": "YYYY-MM-DD",
    "environment": "서버명",
    "device": "디바이스 경로",
    "phase": "현재 Phase"
  },
  "device_calibration": { ... },
  "performance_analysis": { ... },
  "s_max_calculations": { ... },
  "recommendations": { ... }
}
```

### Markdown 보고서 구조
1. 실험 개요
2. Phase별 결과
3. 성능 분석
4. 모델 계산
5. 권장사항
6. 다음 단계

## 🚀 자동화 스크립트

### 실험 결과 자동 업데이트
```bash
# 실험 결과를 JSON으로 자동 업데이트
python3 scripts/update_experiment_data.py --date 2025-09-05 --phase A
```

### 실험 결과 비교
```bash
# 여러 실험 결과 비교
python3 scripts/compare_experiments.py --dates 2025-09-05,2025-09-06
```

---

**생성일**: 2025-09-05  
**마지막 업데이트**: 2025-09-05
