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
# 파일 디스크립터 제한 증가 (Too many open files 에러 방지)
ulimit -n 65536

# 로그 디렉토리 준비 (LOG 파일을 ./log에 저장)
mkdir -p ./log
ln -sf ./log/LOG /rocksdb/data/LOG

# RocksDB 10.7.0+ 호환 옵션 파일 생성
cat > options-leveled.ini << 'EOF'
# RocksDB 10.7+ leveled-compaction options (INI format)
# References:
# - RocksDB Options File format: https://github.com/facebook/rocksdb/wiki/RocksDB-Options-File
# - BlockBasedTable format: https://github.com/facebook/rocksdb/wiki/rocksdb-blockbasedtable-format
# Notes:
# * Keep path arguments (e.g., --db, --wal_dir) on the db_bench command line, not inside this file.
# * Avoid pointer-typed or unsupported options in Options File (see wiki).

[Version]
rocksdb_version=10.7.0
options_file_version=1.1

[DBOptions]
# Creation / general
create_if_missing=true
create_missing_column_families=false

# Logging / stats
keep_log_file_num=3
stats_dump_period_sec=60

# IO behavior
bytes_per_sync=1048576              # 1 MiB
wal_bytes_per_sync=1048576          # 1 MiB
use_direct_reads=true
use_direct_io_for_flush_and_compaction=true
compaction_readahead_size=0

# Write threading
enable_pipelined_write=true         # DBOptions::enable_pipelined_write
allow_concurrent_memtable_write=true

# Background work
max_open_files=2048
max_background_jobs=12
max_subcompactions=4

[CFOptions "default"]
# Compaction policy
compaction_style=kCompactionStyleLevel
compaction_pri=kMinOverlappingRatio
num_levels=7
level_compaction_dynamic_level_bytes=false
max_bytes_for_level_multiplier=10.0

# File sizing and level sizing
target_file_size_base=268435456         # 256 MiB
target_file_size_multiplier=1
max_bytes_for_level_base=2684354560     # ~2.5 GiB

# Compression (ensure your build enables these; otherwise switch to kNoCompression)
compression=kSnappyCompression
bottommost_compression=kZSTD

# Memtable / L0
write_buffer_size=268435456             # 256 MiB per memtable
max_write_buffer_number=3
min_write_buffer_number_to_merge=1
level0_file_num_compaction_trigger=4
level0_slowdown_writes_trigger=20
level0_stop_writes_trigger=36

# Table factory (links to TableOptions/BlockBasedTable section below)
table_factory=BlockBasedTable

[TableOptions/BlockBasedTable "default"]
# Modern table format (forward-incompatible with very old RocksDB)
format_version=5

# Common table tuning (safe defaults)
block_size=65536                        # 64 KiB blocks (adjust per workload)
cache_index_and_filter_blocks=true
pin_l0_filter_and_index_blocks_in_cache=true
whole_key_filtering=true
checksum=kCRC32c
filter_policy=rocksdb.BuiltinBloomFilter
EOF

# 기본 벤치마크
./db_bench --options_file=options-leveled.ini \
  --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 \
  --db=/rocksdb/data --wal_dir=/rocksdb/wal --statistics=1

# 더 긴 실행 (정확한 측정을 위해)
./db_bench --options_file=options-leveled.ini \
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
