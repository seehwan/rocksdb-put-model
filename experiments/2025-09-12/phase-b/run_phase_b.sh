#!/bin/bash

# Phase-B: RocksDB FillRandom 실험 실행 스크립트
# 목적: FillRandom 워크로드 실행 및 LOG 파일 수집

set -e

echo "=== Phase-B: RocksDB FillRandom 실험 시작 ===" | tee phase_b.log
echo "시작 시간: $(date)" | tee -a phase_b.log

# 1. 장치 파티셔닝 및 마운트
echo "" | tee -a phase_b.log
echo "=== 1. 장치 파티셔닝 및 마운트 ===" | tee -a phase_b.log

# 기존 파티션 정리
echo "기존 파티션 언마운트..." | tee -a phase_b.log
sudo umount /dev/nvme1n1p1 2>/dev/null || true
sudo umount /dev/nvme1n1p2 2>/dev/null || true
sudo umount /dev/nvme1n1 2>/dev/null || true
sleep 2

# 파티션 테이블 생성
echo "파티션 테이블 생성..." | tee -a phase_b.log
sudo parted /dev/nvme1n1 mklabel gpt
sleep 2

echo "WAL 파티션 생성 (1MB-10GB)..." | tee -a phase_b.log
sudo parted /dev/nvme1n1 mkpart primary 1MB 10GB
sleep 2

echo "Data 파티션 생성 (10GB-100%)..." | tee -a phase_b.log
sudo parted /dev/nvme1n1 mkpart primary 10GB 100%
sleep 2

# 파일시스템 생성
echo "WAL 파티션 파일시스템 생성..." | tee -a phase_b.log
sudo mkfs.f2fs /dev/nvme1n1p1
sleep 2

echo "Data 파티션 파일시스템 생성..." | tee -a phase_b.log
sudo mkfs.f2fs /dev/nvme1n1p2
sleep 2

# 마운트 포인트 생성 및 마운트
echo "마운트 포인트 생성..." | tee -a phase_b.log
sudo mkdir -p /rocksdb/wal /rocksdb/data

echo "WAL 파티션 마운트..." | tee -a phase_b.log
sudo mount /dev/nvme1n1p1 /rocksdb/wal

echo "Data 파티션 마운트..." | tee -a phase_b.log
sudo mount /dev/nvme1n1p2 /rocksdb/data

echo "권한 설정..." | tee -a phase_b.log
sudo chown -R sslab:sslab /rocksdb

# LOG 파일 디렉토리 생성 및 링크 설정
echo "LOG 파일 디렉토리 설정..." | tee -a phase_b.log
mkdir -p logs
ln -sf /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/logs/LOG /rocksdb/data/LOG

# 2. RocksDB FillRandom 실행
echo "" | tee -a phase_b.log
echo "=== 2. RocksDB FillRandom 실행 ===" | tee -a phase_b.log

# RocksDB 디렉토리로 이동
cd /home/sslab/rocksdb

# db_bench 실행
echo "FillRandom 워크로드 시작..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/phase_b.log
echo "시작 시간: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/phase_b.log

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

echo "FillRandom 완료 시간: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/phase_b.log

# 3. 결과 파일 복사
echo "" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/phase_b.log
echo "=== 3. 결과 파일 복사 ===" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/phase_b.log

cd /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b

echo "LOG 파일 확인..." | tee -a phase_b.log
ls -la logs/LOG* 2>/dev/null || echo "LOG 파일이 생성되지 않았습니다" | tee -a phase_b.log

echo "데이터베이스 크기 확인..." | tee -a phase_b.log
du -sh /rocksdb/data | tee -a phase_b.log

echo "완료 시간: $(date)" | tee -a phase_b.log
echo "=== Phase-B 완료 ===" | tee -a phase_b.log
