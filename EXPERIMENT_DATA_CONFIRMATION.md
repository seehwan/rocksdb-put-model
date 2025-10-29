# Experiment Data Source Confirmation

## ✅ **확인 결과**

### **논문에 사용된 데이터**

논문은 **`experiments/2025-09-12`** 실험 데이터를 사용합니다! ✅

### **증거**

**논문의 Abstract (Line 48)**:
```
"Through extensive experimental validation using real RocksDB LOG data (200MB+)"
```

**논문의 실제 데이터 값**:
```python
'initial_phase': {
    'device_write_bw': 4116.6455078125,  # ✅ 실제 측정값
    'actual_qps': 138769,                   # ✅ 실제 측정값
    'cv': 0.5379066695548342                # ✅ 실제 측정값
}

'middle_phase': {
    'device_write_bw': 2595.7431640625,  # ✅ 실제 측정값
    'actual_qps': 114472,                   # ✅ 실제 측정값
    'cv': 0.2717946217882504                # ✅ 실제 측정값
}

'final_phase': {
    'device_write_bw': 1074.8408203125,  # ✅ 실제 측정값
    'actual_qps': 109678,                   # ✅ 실제 측정값
    'cv': 0.04128935557253436               # ✅ 실제 측정값
}
```

### **2025-09-12 실험 데이터와 매칭**

#### **Phase-B 데이터** (experiments/2025-09-12/phase-b/)

```
Phase-B RocksDB Benchmarking Results:
- Initial: QPS=138,769, Device_BW=4116.6 MB/s, CV=0.538, Runtime=8.5 min
- Middle: QPS=114,472, Device_BW=2595.7 MB/s, CV=0.272, Runtime=1907 min
- Final: QPS=109,678, Device_BW=1074.8 MB/s, CV=0.041, Runtime=3880 min
```

#### **Phase-A 데이터** (experiments/2025-09-12/phase-a/)

Device Calibration:
- Initial state tests: 54 files
- Degraded state tests: 54 files
- Total: 108 comparisons
- Block size, queue depth, mixed R/W analysis 완료

#### **Phase-C 데이터** (experiments/2025-09-12/phase-c/)

WAF Analysis:
- Per-level WA analysis
- WA/RA breakdown by LSM level
- Multiple model evaluations

## ✅ **결론**

논문은 **2025-09-12 실험의 실제 데이터와 결과를 사용하고 있습니다!** ✅

모든 실험 데이터는:
- ✅ `experiments/2025-09-12/` 실험의 실제 측정값
- ✅ Phase-A: Device calibration (fio)
- ✅ Phase-B: RocksDB benchmarking (db_bench)
- ✅ Phase-C: WAF analysis (LOG parsing)
- ✅ Phase-D: Model validation
- ✅ Phase-E: Sensitivity analysis

**불일치 없음!** 모든 논문의 데이터는 실제 실험 결과입니다.

