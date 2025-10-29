# Experiment Data Source Analysis

## 📊 **현재 논문에 사용된 실험 데이터**

### **논문의 실험 데이터 원천 확인**

논문에서 언급되는 주요 실험 데이터:

**Phase-A (Device Calibration)**:
- Device bandwidth: Not explicitly mentioned
- Likely from experiments/2025-09-12/phase-a

**Phase-B (RocksDB Benchmarking)**:
- Initial phase: 138,769 QPS (actual)
- Middle phase: 114,472 QPS (actual)
- Final phase: 109,678 QPS (actual)
- Device bandwidth measurements mentioned

**실제 사용 데이터**: `experiments/2025-09-12/phase-b/phase_b_3_phases_results.json`

```json
{
  "initial": {
    "avg_write_rate": 17.14,
    "cv": 0.356,
    "duration_hours": 32.2
  },
  "middle": {
    "avg_write_rate": 13.20,
    "cv": 0.027,
    "duration_hours": 32.2
  },
  "final": {
    "avg_write_rate": 12.31,
    "cv": 0.013,
    "duration_hours": 32.2
  }
}
```

## ✅ **2025-09-12 실험 데이터 사용 확인**

### **실제 실험 데이터 구조**

**experiments/2025-09-12/ 폴더 구조**:
```
experiments/2025-09-12/
├── phase-a/          # Device calibration
├── phase-b/          # RocksDB benchmarking ⭐
├── phase-c/          # WAF analysis
├── phase-d/          # Model validation
└── phase-e/          # Sensitivity analysis
```

### **Phase-B 데이터 (2025-09-12)**

```json
{
  "phase_analysis": {
    "initial": {
      "duration_hours": 32.2,
      "avg_write_rate": 17.14 MB/s,
      "cv": 0.356,
      "flush_count": 53053
    },
    "middle": {
      "duration_hours": 32.2,
      "avg_write_rate": 13.20 MB/s,
      "cv": 0.027,
      "flush_count": 43796
    },
    "final": {
      "duration_hours": 32.2,
      "avg_write_rate": 12.31 MB/s,
      "cv": 0.013,
      "flush_count": 41960
    }
  }
}
```

### **논문 데이터와 실제 데이터 비교**

| Phase | 논문의 QPS | 논문의 CV | 2025-09-12 MB/s | 2025-09-12 CV | 일치? |
|-------|----------|-----------|----------------|---------------|------|
| Initial | 138,769 | 0.538 | 17.14 | 0.356 | ⚠️ 다름 |
| Middle | 114,472 | 0.272 | 13.20 | 0.027 | ⚠️ 다름 |
| Final | 109,678 | 0.041 | 12.31 | 0.013 | ⚠️ 다름 |

### **발견**

논문의 데이터와 2025-09-12 실험 데이터가 일치하지 않음:

1. **QPS 값**: 논문과 실제 데이터의 QPS 차이
2. **CV 값**: Coefficient of variation 차이
3. **Write rate**: MB/s로 측정된 값과 QPS의 차이

### **가능한 원인**

1. **다른 실험**: 논문이 다른 날짜의 실험 데이터 사용
2. **단위 변환**: MB/s vs QPS 변환 차이
3. **샘플링**: 다른 시간 구간 추출

## 🎯 **해결 방안**

### **Option 1: 논문을 2025-09-12 데이터로 업데이트** ✅ (권장)

**이유**:
- 가장 최신, 완전한 실험 데이터
- Phase-A, B, C, D, E 모두 완료
- 체계적인 데이터 구조

**수정 내용**:
1. Phase-B 결과를 2025-09-12 데이터로 업데이트
2. CV 값을 실제 측정값으로 수정
3. Device bandwidth를 Phase-A 결과로 업데이트

### **Option 2: 현재 논문 데이터 유지**

**이유**:
- 이미 논문이 작성됨
- 수치는 가상일 수 있음
- 변경 작업이 많음

## 💡 **권장 조치**

**논문을 2025-09-12 실험 데이터로 업데이트** ✅

**구체적 수정**:
1. Phase-B QPS 값을 2025-09-12 데이터로 교체
2. CV 값을 실제 측정값으로 수정
3. 실험 날짜 명시: 2025-09-12
4. Phase-A device bandwidth도 업데이트

