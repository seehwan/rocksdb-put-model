# db_bench command cheatsheet (adjust paths and numbers)

# 1) Fill random with leveled options
./db_bench --benchmarks=fillrandom --num=200000000 --value_size=1024   --key_size=16 --use_existing_db=0 --threads=8 --compression_type=snappy   --stats_interval_seconds=5 --db=/data/rocksdb --options_file=options-leveled.ini

# 2) Mixed workload (overwrite / readwhilewriting)
./db_bench --benchmarks=overwrite,readwhilewriting --disable_auto_compactions=0   --num=50000000 --value_size=1024 --threads=8   --db=/data/rocksdb --options_file=options-leveled.ini

# 3) Universal compaction baseline
./db_bench --benchmarks=fillrandom --num=200000000 --value_size=1024   --threads=8 --db=/data/rocksdb --options_file=options-universal.ini

# 4) Throttle ingest (approximate) via threads; or use --writes_per_second if suitable
./db_bench --benchmarks=fillrandom --num=100000000 --value_size=1024   --threads=4 --db=/data/rocksdb --options_file=options-leveled.ini
