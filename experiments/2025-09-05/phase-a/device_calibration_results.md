# Phase-A: 디바이스 캘리브레이션 결과

**실험 일시**: 2025-09-05  
**디바이스**: /dev/nvme1n1p1 (NVMe SSD)  
**측정 환경**: GPU-01 서버  

## 📊 측정 결과

### 1. Write 성능 측정

```bash
# 명령어
fio --name=w --filename=/dev/nvme1n1p1 --rw=write --bs=128k --iodepth=32 --numjobs=1 --time_based=1 --runtime=60
```

**결과:**
- **Bandwidth**: 1484 MiB/s (1556 MB/s)
- **IOPS**: 11.9k IOPS
- **Latency**: 평균 41.55μs
- **Utilization**: 15.74%

**추출된 값:**
- `B_w = 1484 MiB/s`

### 2. Read 성능 측정

```bash
# 명령어
fio --name=r --filename=/dev/nvme1n1p1 --rw=read --bs=128k --iodepth=32 --numjobs=1 --time_based=1 --runtime=60
```

**결과:**
- **Bandwidth**: 2368 MiB/s (2483 MB/s)
- **IOPS**: 18.9k IOPS
- **Latency**: 평균 44.43μs
- **Utilization**: 65.84%

**추출된 값:**
- `B_r = 2368 MiB/s`

### 3. Mixed 성능 측정 (50:50)

```bash
# 명령어
fio --name=rw --filename=/dev/nvme1n1p1 --rw=rw --rwmixread=50 --bs=128k --iodepth=32 --numjobs=1 --time_based=1 --runtime=60
```

**결과:**
- **Read Bandwidth**: 1116 MiB/s (1170 MB/s)
- **Write Bandwidth**: 1115 MiB/s (1169 MB/s)
- **Total Bandwidth**: 2231 MiB/s
- **Read IOPS**: 8.9k IOPS
- **Write IOPS**: 8.9k IOPS
- **Utilization**: 36.24%

**추출된 값:**
- `B_eff = 2231 MiB/s` (1116 + 1115)

## 📈 성능 분석

### 디바이스 성능 특성

| 측정 항목 | 순수 성능 | 혼합 성능 | 성능 저하율 |
|-----------|-----------|-----------|-------------|
| **읽기** | 2368 MiB/s | 1116 MiB/s | **-53%** |
| **쓰기** | 1484 MiB/s | 1115 MiB/s | **-25%** |
| **혼합** | - | 2231 MiB/s | - |

### 주요 관찰사항

1. **읽기 우세**: 읽기가 쓰기보다 60% 더 빠름
2. **동시성 간섭**: 혼합 워크로드에서 상당한 성능 저하
3. **안정적 성능**: 모든 테스트에서 일관된 성능 유지

## 🎯 다음 단계

- [x] Write 성능 측정 완료
- [x] Read 성능 측정 완료  
- [x] Mixed 성능 측정 완료
- [x] 성능 분석 완료
- [ ] Phase-B: RocksDB 벤치마크 실행

---

**완료일**: 2025-09-05  
**상태**: ✅ 완료
