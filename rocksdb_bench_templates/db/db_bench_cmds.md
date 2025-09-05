# db_bench command cheatsheet (adjust paths and numbers)

# 1) Fill random with leveled options (레벨별 압축 설정 사용)
./db_bench --options_file=options-leveled.ini --benchmarks=fillrandom --num=200000000 --value_size=1024 --key_size=16 --use_existing_db=0 --threads=8 --stats_interval_seconds=5 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 2) Mixed workload (overwrite / readwhilewriting)
./db_bench --options_file=options-leveled.ini --benchmarks=overwrite,readwhilewriting --disable_auto_compactions=0 --num=50000000 --value_size=1024 --threads=8 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 3) Universal compaction baseline
./db_bench --options_file=options-universal.ini --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 4) Throttle ingest (approximate) via threads; or use --writes_per_second if suitable
./db_bench --options_file=options-leveled.ini --benchmarks=fillrandom --num=100000000 --value_size=1024 --threads=4 --db=/rocksdb/data --wal_dir=/rocksdb/wal
