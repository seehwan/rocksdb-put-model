#!/bin/bash

# Phase-B: RocksDB FillRandom 실험 백그라운드 실행 스크립트
# 목적: FillRandom 워크로드를 백그라운드에서 실행하고 모니터링

set -e

# PID 파일 경로
PID_FILE="phase_b.pid"
LOG_FILE="phase_b_background.log"

echo "=== Phase-B 백그라운드 실행 시작 ===" | tee $LOG_FILE
echo "시작 시간: $(date)" | tee -a $LOG_FILE

# 기존 프로세스 확인
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat $PID_FILE)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️ 기존 Phase-B 프로세스가 실행 중입니다 (PID: $OLD_PID)" | tee -a $LOG_FILE
        echo "기존 프로세스를 종료하시겠습니까? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            kill $OLD_PID
            echo "기존 프로세스를 종료했습니다." | tee -a $LOG_FILE
            sleep 2
        else
            echo "실행을 중단합니다." | tee -a $LOG_FILE
            exit 1
        fi
    else
        echo "기존 PID 파일이 존재하지만 프로세스가 실행되지 않습니다. 정리합니다." | tee -a $LOG_FILE
        rm -f $PID_FILE
    fi
fi

# 백그라운드 실행 함수
run_phase_b_background() {
    echo "=== Phase-B 백그라운드 실행 시작 ===" | tee $LOG_FILE
    echo "PID: $$" | tee -a $LOG_FILE
    
    # 1. 장치 파티셔닝 및 마운트
    echo "" | tee -a $LOG_FILE
    echo "=== 1. 장치 파티셔닝 및 마운트 ===" | tee -a $LOG_FILE

    # 기존 파티션 정리
    echo "기존 파티션 언마운트..." | tee -a $LOG_FILE
    sudo umount /dev/nvme1n1p1 2>/dev/null || true
    sudo umount /dev/nvme1n1p2 2>/dev/null || true
    sudo umount /dev/nvme1n1 2>/dev/null || true
    sleep 2

    # 파티션 테이블 생성
    echo "파티션 테이블 생성..." | tee -a $LOG_FILE
    printf "yes\n" | sudo parted /dev/nvme1n1 mklabel gpt
    sleep 2

    echo "WAL 파티션 생성 (1MB-10GB)..." | tee -a $LOG_FILE
    sudo parted /dev/nvme1n1 mkpart primary 1MB 10GB
    sleep 2

    echo "Data 파티션 생성 (10GB-100%)..." | tee -a $LOG_FILE
    sudo parted /dev/nvme1n1 mkpart primary 10GB 100%
    sleep 2

    # 파일시스템 생성
    echo "WAL 파티션 파일시스템 생성..." | tee -a $LOG_FILE
    sudo mkfs.f2fs /dev/nvme1n1p1
    sleep 2

    echo "Data 파티션 파일시스템 생성..." | tee -a $LOG_FILE
    sudo mkfs.f2fs /dev/nvme1n1p2
    sleep 2

    # 마운트 포인트 생성 및 마운트
    echo "마운트 포인트 생성..." | tee -a $LOG_FILE
    sudo mkdir -p /rocksdb/wal /rocksdb/data

    echo "WAL 파티션 마운트..." | tee -a $LOG_FILE
    sudo mount /dev/nvme1n1p1 /rocksdb/wal

    echo "Data 파티션 마운트..." | tee -a $LOG_FILE
    sudo mount /dev/nvme1n1p2 /rocksdb/data

    echo "권한 설정..." | tee -a $LOG_FILE
    sudo chown -R sslab:sslab /rocksdb

    # LOG 파일 디렉토리 생성 및 링크 설정
    echo "LOG 파일 디렉토리 설정..." | tee -a $LOG_FILE
    mkdir -p /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/logs
    ln -sf /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/logs/LOG /rocksdb/data/LOG

    # 2. RocksDB FillRandom 실행
    echo "" | tee -a $LOG_FILE
    echo "=== 2. RocksDB FillRandom 실행 ===" | tee -a $LOG_FILE

    # RocksDB 디렉토리로 이동
    cd /home/sslab/rocksdb

    # db_bench 실행
    echo "FillRandom 워크로드 시작..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/$LOG_FILE
    echo "시작 시간: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/$LOG_FILE

    ./db_bench \
      --benchmarks=fillrandom \
      --db=/rocksdb/data \
      --wal_dir=/rocksdb/wal \
      --num=1000000000 \
      --value_size=1024 \
      --key_size=16 \
      --threads=32 \
      --stats_interval=1000000 \
      --stats_dump_period_sec=10 \
      --report_file=/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/fillrandom_results.json \
      --report_interval_seconds=10

    echo "FillRandom 완료 시간: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/$LOG_FILE

    # 3. 결과 파일 복사
    echo "" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/$LOG_FILE
    echo "=== 3. 결과 파일 복사 ===" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/$LOG_FILE

    cd /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b

    echo "LOG 파일 확인..." | tee -a $LOG_FILE
    ls -la logs/LOG* 2>/dev/null || echo "LOG 파일이 생성되지 않았습니다" | tee -a $LOG_FILE

    echo "데이터베이스 크기 확인..." | tee -a $LOG_FILE
    du -sh /rocksdb/data | tee -a $LOG_FILE

    echo "완료 시간: $(date)" | tee -a $LOG_FILE
    echo "=== Phase-B 완료 ===" | tee -a $LOG_FILE
    
    # PID 파일 삭제
    rm -f $PID_FILE
}

# 백그라운드에서 실행
echo "Phase-B를 백그라운드에서 실행합니다..." | tee -a $LOG_FILE
run_phase_b_background &
BACKGROUND_PID=$!

# PID 저장
echo $BACKGROUND_PID > $PID_FILE

echo "✅ Phase-B가 백그라운드에서 실행 중입니다!" | tee -a $LOG_FILE
echo "📋 PID: $BACKGROUND_PID" | tee -a $LOG_FILE
echo "📄 로그 파일: $LOG_FILE" | tee -a $LOG_FILE
echo "📄 PID 파일: $PID_FILE" | tee -a $LOG_FILE

echo ""
echo "🔍 모니터링 명령어:"
echo "  로그 확인: tail -f $LOG_FILE"
echo "  프로세스 확인: ps -p $BACKGROUND_PID"
echo "  중단: kill $BACKGROUND_PID"
echo "  상태 확인: ./check_phase_b_status.sh"
