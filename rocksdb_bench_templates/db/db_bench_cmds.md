# db_bench command cheatsheet (RocksDB 10.7.0+ 호환)

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

# 1) Fill random with leveled options (레벨별 압축 설정 사용)
./db_bench --options_file=options-leveled.ini --benchmarks=fillrandom --num=200000000 --value_size=1024 --key_size=16 --use_existing_db=0 --threads=8 --stats_interval_seconds=5 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 2) Mixed workload (overwrite / readwhilewriting)
./db_bench --options_file=options-leveled.ini --benchmarks=overwrite,readwhilewriting --disable_auto_compactions=0 --num=50000000 --value_size=1024 --threads=8 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 3) Universal compaction baseline
./db_bench --options_file=options-universal.ini --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 4) Throttle ingest (approximate) via threads; or use --writes_per_second if suitable
./db_bench --options_file=options-leveled.ini --benchmarks=fillrandom --num=100000000 --value_size=1024 --threads=4 --db=/rocksdb/data --wal_dir=/rocksdb/wal
