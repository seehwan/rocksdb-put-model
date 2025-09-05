# Phase-B: RocksDB 벤치마크 실행

**실험 일시**: ___  
**RocksDB 버전**: ___  
**벤치마크 설정**: ___  

## 🚀 RocksDB 설정 및 실행

### 1. RocksDB 빌드
```bash
# RocksDB 소스 다운로드 및 빌드
git clone https://github.com/facebook/rocksdb.git
cd rocksdb
make db_bench -j$(nproc)

# 빌드 확인
ls -la db_bench
```

### 2. 벤치마크 실행
```bash
# 로그 디렉토리 준비 (심볼릭 링크 사용)
mkdir -p ./log
ln -sf /rocksdb/data/LOG ./log/LOG

# 기본 벤치마크
./db_bench --options_file=rocksdb_bench_templates/db/options-leveled.ini \
  --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 \
  --db=/rocksdb/data --wal_dir=/rocksdb/wal --statistics=1

# 더 긴 실행 (정확한 측정을 위해)
./db_bench --options_file=rocksdb_bench_templates/db/options-leveled.ini \
  --benchmarks=fillrandom --num=1000000000 --value_size=1024 --threads=16 \
  --db=/rocksdb/data --wal_dir=/rocksdb/wal --statistics=1 --stats_dump_period_sec=60
```

### 3. 로그 파일 확인
```bash
# LOG 파일 위치 확인
ls -la ./log/LOG*

# 통계 정보 확인
grep "Compaction Stats" ./log/LOG
```

## 📊 측정 결과

### 벤치마크 성능
- **지속 가능한 put rate**: ___ MiB/s
- **실제 ops/s**: ___
- **실행 시간**: ___ 초
- **총 데이터 크기**: ___ GB

### RocksDB 통계
- **Compaction Stats 발견**: ___ 개
- **WAL 크기**: ___ MB
- **SST 파일 수**: ___ 개
- **Memtable flush 횟수**: ___ 회

## 🔍 LOG 파일 분석

### 압축률 (CR) 측정
```bash
# LOG에서 압축률 추정
python3 scripts/analyze_compression_ratio.py --log ./log/LOG
```

**결과:**
- **실제 CR**: ___
- **측정 방법**: ___

### Write Amplification (WA) 측정
```bash
# LOG에서 WA 추정
python3 scripts/analyze_write_amplification.py --log ./log/LOG
```

**결과:**
- **실제 WA**: ___
- **측정 방법**: ___

### Read Amplification (RA_c) 측정
```bash
# LOG에서 RA_c 추정
python3 scripts/analyze_read_amplification.py --log ./log/LOG
```

**결과:**
- **실제 RA_c**: ___
- **측정 방법**: ___

## 📈 성능 분석

### 예상 vs 실제 성능 비교
- **예상 S_max**: ___ MiB/s (Phase-A 결과 기반)
- **실제 지속 성능**: ___ MiB/s
- **성능 차이**: ___%

### 병목 분석
- **주요 병목**: [ ] Write [ ] Read [ ] Mixed [ ] CPU [ ] 기타
- **Stall 발생**: [ ] 예 [ ] 아니오
- **Slowdown 발생**: [ ] 예 [ ] 아니오

## 🎯 다음 단계

- [ ] LOG 파일 분석 완료
- [ ] CR, WA, RA_c 측정 완료
- [ ] 성능 분석 완료
- [ ] Phase-C: Per-Level WAF 분석

---

**완료일**: ___  
**상태**: [ ] 진행중 [ ] 완료
