# 실험 결과 업데이트 템플릿

## Phase-B: RocksDB 벤치마크 실행

### 1. RocksDB 설정
```bash
# RocksDB 빌드
git clone https://github.com/facebook/rocksdb.git
cd rocksdb
make db_bench -j$(nproc)

# 로그 디렉토리 준비 (LOG 파일을 ./log에 저장)
mkdir -p ./log
ln -sf ./log/LOG /rocksdb/data/LOG

# 파일 디스크립터 제한 증가 (Too many open files 에러 방지)
ulimit -n 65536

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

# 설정 파일 사용 (레벨별 압축 설정 포함)
./db_bench --options_file=options-leveled.ini \
  --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 \
  --db=/rocksdb/data --wal_dir=/rocksdb/wal --statistics=1
```

### 2. 측정 결과
- **실제 CR (압축률)**: **0.5406** (54.06%, 1:1.85 압축 비율)
- **실제 WA (Write Amplification)**: **1.02** (매우 낮음 - 거의 1:1)
- **실제 RA_c (Read Amplification)**: ___ (LOG에서 추출 필요)
- **지속 가능한 put rate**: **187.1 MiB/s**
- **실제 ops/s**: **188,617 ops/sec**
- **실행 시간**: **16,965.531 초** (약 4.7시간)
- **총 operations**: **3,200,000,000** (32억 operations)
- **평균 latency**: **84.824 micros/op**

### 3. 상세 성능 분석
- **사용자 데이터 크기**: **3,051.76 GB**
- **실제 쓰기 바이트**: **3,115.90 GB**
- **Compaction 읽기**: **13,439.09 GB**
- **Compaction 쓰기**: **11,804.86 GB**
- **Flush 쓰기**: **1,751.57 GB**
- **총 Stall 시간**: **7,687.69 초** (45.31% 비율)
- **평균 Stall 시간**: **2.40 micros/op**

### 4. LOG 파일 분석
```bash
# LOG 파일 위치
LOG_PATH="./log/LOG"

# WAF 분석
python3 scripts/waf_analyzer.py --log $LOG_PATH \
  --user-mb 1000 --out-dir validation_results --plot
```

---

## Phase-C: Per-Level WAF 분석

### 1. 레벨별 I/O 분해
```bash
# Per-level breakdown
python3 scripts/per_level_breakdown.py
```

**결과:**
- L0: Write=___, Read=___
- L1: Write=___, Read=___
- L2: Write=___, Read=___
- L3: Write=___, Read=___
- L4: Write=___, Read=___
- L5: Write=___, Read=___
- L6: Write=___, Read=___

### 2. Mass Balance 검증
- **예상 총 쓰기**: ___ MB
- **실제 총 쓰기**: ___ MB
- **오류율**: ___% (≤10% 목표)

---

## Phase-D: 모델 검증

### 1. S_max 검증
**입력 파라미터:**
- **B_w**: ___ MiB/s (Phase-A 측정값 필요)
- **B_r**: ___ MiB/s (Phase-A 측정값 필요)  
- **B_eff**: ___ MiB/s (Phase-A 측정값 필요)
- **CR**: **0.5406** (Phase-B 측정값)
- **WA**: **1.02** (Phase-B 측정값)
- **RA_c**: ___ (Phase-C 분석 필요)

**S_max 계산:**
```bash
# Write bound
S_w = B_w × CR / WA = ___ × 0.5406 / 1.02 = ___ MiB/s

# Read bound  
S_r = B_r × CR / RA_c = ___ × 0.5406 / ___ = ___ MiB/s

# Mixed bound
S_m = B_eff × CR / (WA + RA_c) = ___ × 0.5406 / (1.02 + ___) = ___ MiB/s

# 최종 S_max (최소값)
S_max_predicted = min(S_w, S_r, S_m) = ___ MiB/s
```

**검증 결과:**
- **예측값**: ___ MiB/s
- **측정값**: **187.1 MiB/s**
- **오류율**: ___% (≤10% 목표)

### 2. 성공 기준 검증
- [ ] Envelope error ≤ 10%
- [ ] Mass-balance error ≤ 10%
- [ ] Stabilization 확인
- [ ] Stall time 패턴 일치

---

## Phase-E: 민감도 분석

### 1. 압축률 변화
- CR=0.3: S_max=___
- CR=0.5: S_max=___
- CR=0.7: S_max=___

### 2. Write Amplification 변화
- WA=4: S_max=___
- WA=8: S_max=___
- WA=12: S_max=___

---

## 최종 검증 결과

### 모델 정확도
- **전체 오류율**: ___%
- **검증 상태**: [ ] 성공 [ ] 부분 성공 [ ] 실패

### 운영 권장사항
- **권장 Rate Limiter**: ___ bytes/sec
- **예상 최대 성능**: ___ ops/s
- **주요 병목**: ___

---

**업데이트 일시**: ___  
**업데이트자**: ___
