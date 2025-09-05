# db_bench command cheatsheet (RocksDB 10.7.0+ 호환)

# RocksDB 10.7.0+ 호환 옵션 파일 생성
cat > options-leveled.ini << 'EOF'
[DBOptions]
db_path=/rocksdb/data
wal_dir=/rocksdb/wal
max_open_files=2048
keep_log_file_num=3
statistics=true
report_bg_io_stats=true
stats_dump_period_sec=60
bytes_per_sync=1048576
wal_bytes_per_sync=1048576
use_direct_reads=true
use_direct_io_for_flush_and_compaction=true
compaction_readahead_size=0
rate_limiter_bytes_per_sec=0

[CFOptions "default"]
compaction_style=kCompactionStyleLevel
compaction_pri=kMinOverlappingRatio
num_levels=7
level_compaction_dynamic_level_bytes=false
max_bytes_for_level_multiplier=10
target_file_size_base=268435456
target_file_size_multiplier=1
max_bytes_for_level_base=2684354560
compression=kSnappy
bottommost_compression=kZSTD
write_buffer_size=268435456
max_write_buffer_number=3
min_write_buffer_number_to_merge=1
enable_pipelined_write=true
allow_concurrent_memtable_write=true
max_background_jobs=12
max_subcompactions=4
level0_file_num_compaction_trigger=4
level0_slowdown_writes_trigger=20
level0_stop_writes_trigger=36
EOF

# 1) Fill random with leveled options (레벨별 압축 설정 사용)
./db_bench --options_file=options-leveled.ini --benchmarks=fillrandom --num=200000000 --value_size=1024 --key_size=16 --use_existing_db=0 --threads=8 --stats_interval_seconds=5 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 2) Mixed workload (overwrite / readwhilewriting)
./db_bench --options_file=options-leveled.ini --benchmarks=overwrite,readwhilewriting --disable_auto_compactions=0 --num=50000000 --value_size=1024 --threads=8 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 3) Universal compaction baseline
./db_bench --options_file=options-universal.ini --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 4) Throttle ingest (approximate) via threads; or use --writes_per_second if suitable
./db_bench --options_file=options-leveled.ini --benchmarks=fillrandom --num=100000000 --value_size=1024 --threads=4 --db=/rocksdb/data --wal_dir=/rocksdb/wal
