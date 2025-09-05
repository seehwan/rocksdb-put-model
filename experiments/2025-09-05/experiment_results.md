# RocksDB Put-Rate Model 실험 결과

**실험 일시**: 2025-09-05  
**실험 환경**: GPU-01 서버  
**디바이스**: /dev/nvme1n1p1 (NVMe SSD)  
**실험자**: yooseehwan  

## 📊 Phase-A: 디바이스 캘리브레이션 결과

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

## 🧮 S_max 예측 계산

### 기본 파라미터 (가정값)

```bash
CR = 0.5      # 압축률 (2:1 압축)
WA = 8.0      # Write Amplification (Leveled compaction)
RA_c = 7.0    # Read Amplification (compaction only)
```

### S_max 계산

```bash
# Write bound
S_w = B_w × CR / WA = 1484 × 0.5 / 8.0 = 92.75 MiB/s

# Read bound  
S_r = B_r × CR / RA_c = 2368 × 0.5 / 7.0 = 169.1 MiB/s

# Mixed bound
S_m = B_eff × CR / (WA + RA_c) = 2231 × 0.5 / (8.0 + 7.0) = 74.4 MiB/s

# 최종 S_max (최소값)
S_max = min(S_w, S_r, S_m) = 74.4 MiB/s
```

### 보정된 S_max (실제 운영용)

```bash
# 파일시스템 오버헤드 20% 적용
B_w_effective = 1484 × 0.8 = 1187 MiB/s
B_r_effective = 2368 × 0.8 = 1894 MiB/s
B_eff_effective = 2231 × 0.8 = 1785 MiB/s

# 보정된 S_max 계산
S_w_corrected = 1187 × 0.5 / 8.0 = 74.2 MiB/s
S_r_corrected = 1894 × 0.5 / 7.0 = 135.3 MiB/s
S_m_corrected = 1785 × 0.5 / 15.0 = 59.5 MiB/s

S_max_corrected = min(74.2, 135.3, 59.5) = 59.5 MiB/s

# 안전 마진 20% 적용
S_max_safe = 59.5 × 0.8 = 47.6 MiB/s
```

## 🎯 권장 운영 설정

### RocksDB 설정 권장사항

```bash
# Rate Limiter 설정
rate_limiter_bytes_per_sec = 50000000  # 47.6 MiB/s

# WAL 설정 (별도 디바이스 권장)
wal_dir = /rocksdb/wal

# Compaction 설정
max_background_jobs = 8
max_subcompactions = 4
```

### 예상 성능

- **최대 지속 가능한 put rate**: ~47.6 MiB/s
- **예상 ops/s** (1KB KV): ~48,000 ops/s
- **병목 지점**: Mixed bound (읽기+쓰기 동시성)

## 📋 다음 단계

### Phase-B: RocksDB 벤치마크 실행
- [ ] RocksDB 빌드 및 설정
- [ ] fillrandom 벤치마크 실행
- [ ] 실제 CR, WA 측정

### Phase-C: Per-Level WAF 분석
- [ ] LOG 파일 분석
- [ ] 레벨별 I/O 분해
- [ ] Mass balance 검증

### Phase-D: 모델 검증
- [ ] 예측값 vs 측정값 비교
- [ ] 오차율 계산
- [ ] 성공 기준 검증

## 📝 실험 노트

### 환경 정보
- **OS**: Linux (GPU-01)
- **디바이스**: NVMe SSD (/dev/nvme1n1p1)
- **파일시스템**: 마운트 해제 후 raw device 측정
- **fio 버전**: 3.28

### 주의사항
- Raw device 측정으로 파일시스템 오버헤드 제외
- 실제 운영 시 20% 오버헤드 고려 필요
- Mixed 워크로드에서 상당한 성능 저하 확인

---

**생성일**: 2025-09-05  
**업데이트**: Phase-A 완료
