#!/bin/bash

# Phase-B Final: RocksDB 성능 측정 스크립트 (최종 정리 버전)
# Put-Model 검증을 위한 대규모 실험

set -e  # 오류 발생시 스크립트 종료

# 설정
DB_DIR="/rocksdb/data"
WAL_DIR="/rocksdb/wal"
OUTPUT_DIR="phase_b_final_results"
LOG_FILE="phase_b_final.log"
NUM_KEYS=1000000000  # 10억 키
VALUE_SIZE=1024      # 1KB
KEY_SIZE=16          # 16B
THREADS=16

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

# 진행률 업데이트 함수
update_progress() {
    echo "$(date): $1" | tee -a "$OUTPUT_DIR/progress.txt"
    echo "$1"
}

# 로그 파일 초기화
echo "=== Phase-B Final 실험 시작 ===" > "$LOG_FILE"
echo "시작 시간: $(date)" >> "$LOG_FILE"

# 0. 디스크 정리 및 초기화
update_progress "0. 디스크 정리 및 초기화 시작"
echo "디스크 정리 시작: $(date)" >> "$LOG_FILE"

# 기존 마운트 해제
update_progress "  - 기존 마운트 해제 중..."
sudo umount /rocksdb/wal 2>/dev/null || true
sudo umount /rocksdb/data 2>/dev/null || true

# 디스크 초기화
update_progress "  - 디스크 초기화 중..."
sudo blkdiscard -f /dev/nvme1n1p1
sudo blkdiscard -f /dev/nvme1n1p2

# F2FS 포맷
update_progress "  - F2FS 포맷 중..."
sudo mkfs.f2fs /dev/nvme1n1p1
sudo mkfs.f2fs /dev/nvme1n1p2

# 재마운트
update_progress "  - 디스크 재마운트 중..."
sudo mount /dev/nvme1n1p1 /rocksdb/wal
sudo mount /dev/nvme1n1p2 /rocksdb/data

# 권한 설정
update_progress "  - 권한 설정 중..."
sudo chown -R sslab:sslab /rocksdb

# LOG 심볼릭 링크 생성
update_progress "  - LOG 심볼릭 링크 생성 중..."
ln -sf /home/sslab/rocksdb/build/LOG /rocksdb/data/LOG

update_progress "0. 디스크 정리 및 초기화 완료"

# 1. FillRandom 벤치마크
update_progress "1. FillRandom 벤치마크 시작 (10억 키 랜덤 쓰기)"
echo "FillRandom 시작: $(date)" >> "$LOG_FILE"

/home/sslab/rocksdb/build/db_bench \
    --benchmarks=fillrandom,waitforcompaction \
    --db=$DB_DIR \
    --wal_dir=$WAL_DIR \
    --num=$NUM_KEYS \
    --value_size=$VALUE_SIZE \
    --key_size=$KEY_SIZE \
    --threads=$THREADS \
    --compression_type=lz4 \
    --max_background_jobs=4 \
    --max_write_buffer_number=3 \
    --level0_file_num_compaction_trigger=4 \
    --level0_slowdown_writes_trigger=20 \
    --level0_stop_writes_trigger=36 \
    --max_bytes_for_level_base=268435456 \
    --target_file_size_base=67108864 \
    --write_buffer_size=134217728 \
    --max_total_wal_size=1073741824 \
    --statistics \
    --stats_interval_seconds=30 \
    --stats_dump_period_sec=300 \
    >> "$OUTPUT_DIR/fillrandom_results.txt" 2>&1

update_progress "1. FillRandom 완료 (Compaction 대기 포함)"

# 2. ReadRandomWriterandom 벤치마크
update_progress "2. ReadRandomWriterandom 벤치마크 시작 (1시간 장기 실행)"
echo "ReadRandomWriterandom 시작: $(date)" >> "$LOG_FILE"

/home/sslab/rocksdb/build/db_bench \
    --benchmarks=readrandomwriterandom,waitforcompaction \
    --db=$DB_DIR \
    --wal_dir=$WAL_DIR \
    --num=$NUM_KEYS \
    --value_size=$VALUE_SIZE \
    --key_size=$KEY_SIZE \
    --threads=$THREADS \
    --duration=3600 \
    --readwritepercent=50 \
    --compression_type=lz4 \
    --max_background_jobs=4 \
    --max_write_buffer_number=3 \
    --level0_file_num_compaction_trigger=4 \
    --level0_slowdown_writes_trigger=20 \
    --level0_stop_writes_trigger=36 \
    --max_bytes_for_level_base=268435456 \
    --target_file_size_base=67108864 \
    --write_buffer_size=134217728 \
    --max_total_wal_size=1073741824 \
    --statistics \
    --stats_interval_seconds=30 \
    --stats_dump_period_sec=300 \
    >> "$OUTPUT_DIR/readrandomwriterandom_results.txt" 2>&1

update_progress "2. ReadRandomWriterandom 완료 (Compaction 대기 포함)"

# 3. Overwrite 벤치마크
update_progress "3. Overwrite 벤치마크 시작"
echo "Overwrite 시작: $(date)" >> "$LOG_FILE"

/home/sslab/rocksdb/build/db_bench \
    --benchmarks=overwrite,waitforcompaction \
    --db=$DB_DIR \
    --wal_dir=$WAL_DIR \
    --num=$NUM_KEYS \
    --value_size=$VALUE_SIZE \
    --key_size=$KEY_SIZE \
    --threads=$THREADS \
    --compression_type=lz4 \
    --max_background_jobs=4 \
    --max_write_buffer_number=3 \
    --level0_file_num_compaction_trigger=4 \
    --level0_slowdown_writes_trigger=20 \
    --level0_stop_writes_trigger=36 \
    --max_bytes_for_level_base=268435456 \
    --target_file_size_base=67108864 \
    --write_buffer_size=134217728 \
    --max_total_wal_size=1073741824 \
    --statistics \
    --stats_interval_seconds=30 \
    --stats_dump_period_sec=300 \
    >> "$OUTPUT_DIR/overwrite_results.txt" 2>&1

update_progress "3. Overwrite 완료 (Compaction 대기 포함)"

# 4. MixGraph 벤치마크
update_progress "4. MixGraph 벤치마크 시작"
echo "MixGraph 시작: $(date)" >> "$LOG_FILE"

/home/sslab/rocksdb/build/db_bench \
    --benchmarks=mixgraph,waitforcompaction \
    --db=$DB_DIR \
    --wal_dir=$WAL_DIR \
    --num=$NUM_KEYS \
    --value_size=$VALUE_SIZE \
    --key_size=$KEY_SIZE \
    --threads=$THREADS \
    --compression_type=lz4 \
    --max_background_jobs=4 \
    --max_write_buffer_number=3 \
    --level0_file_num_compaction_trigger=4 \
    --level0_slowdown_writes_trigger=20 \
    --level0_stop_writes_trigger=36 \
    --max_bytes_for_level_base=268435456 \
    --target_file_size_base=67108864 \
    --write_buffer_size=134217728 \
    --max_total_wal_size=1073741824 \
    --statistics \
    --stats_interval_seconds=30 \
    --stats_dump_period_sec=300 \
    >> "$OUTPUT_DIR/mixgraph_results.txt" 2>&1

update_progress "4. MixGraph 완료 (Compaction 대기 포함)"

# 5. LOG 파일 분석
update_progress "5. LOG 파일 분석 시작"
echo "LOG 분석 시작: $(date)" >> "$LOG_FILE"

if [ -f "$DB_DIR/LOG" ]; then
    cp "$DB_DIR/LOG" "$OUTPUT_DIR/rocksdb.log"
    
    # 간단한 LOG 분석
    echo "=== LOG 분석 결과 ===" > "$OUTPUT_DIR/log_analysis.txt"
    echo "분석 시간: $(date)" >> "$OUTPUT_DIR/log_analysis.txt"
    echo "" >> "$OUTPUT_DIR/log_analysis.txt"
    
    # Flush 통계
    flush_count=$(grep -c "flush" "$OUTPUT_DIR/rocksdb.log" 2>/dev/null || echo "0")
    echo "Flush 횟수: $flush_count" >> "$OUTPUT_DIR/log_analysis.txt"
    
    # Compaction 통계
    compaction_count=$(grep -c "compaction" "$OUTPUT_DIR/rocksdb.log" 2>/dev/null || echo "0")
    echo "Compaction 횟수: $compaction_count" >> "$OUTPUT_DIR/log_analysis.txt"
    
    # Write Stall 통계
    stall_count=$(grep -c "stall" "$OUTPUT_DIR/rocksdb.log" 2>/dev/null || echo "0")
    echo "Write Stall 횟수: $stall_count" >> "$OUTPUT_DIR/log_analysis.txt"
    
    echo "LOG 분석 완료" >> "$OUTPUT_DIR/log_analysis.txt"
else
    echo "LOG 파일을 찾을 수 없습니다: $DB_DIR/LOG" >> "$OUTPUT_DIR/log_analysis.txt"
fi

update_progress "5. LOG 파일 분석 완료"

# 6. 최종 요약 생성
update_progress "6. 최종 결과 요약 생성"
echo "결과 요약 시작: $(date)" >> "$LOG_FILE"

cat > "$OUTPUT_DIR/final_summary.txt" << EOF
=== Phase-B Final 실험 완료 ===
완료 시간: $(date)
키 개수: 1,000,000,000 (10억)
예상 데이터 크기: 1000 GB
완료된 워크로드: 4개

주요 개선사항:
  ✅ 데이터 크기 10배 증가 (10억 키)
  ✅ 자동 디스크 정리 및 초기화
  ✅ 각 벤치마크 사이 Compaction 대기 시간 추가
  ✅ 백그라운드 작업 수 최적화 (8→4)
  ✅ Compaction 상태 모니터링

생성된 결과 파일들:
EOF

ls -la "$OUTPUT_DIR/" >> "$OUTPUT_DIR/final_summary.txt"

update_progress "6. 최종 결과 요약 완료"

# 7. 완료 알림
echo ""
echo "=== Phase-B Final 실험 완료 ==="
echo "완료 시간: $(date)"
echo "결과 디렉토리: $OUTPUT_DIR"
echo ""
echo "생성된 파일들:"
ls -la "$OUTPUT_DIR/"

echo ""
echo "실험 완료!"
