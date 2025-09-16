#!/bin/bash
# Phase-A: 열화상태 Device Envelope 그리드 스윕 스크립트
# 실행일: 2025-09-12
# 목적: Phase-B 완료 후 열화된 상태에서의 4D 그리드 스윕 측정

echo "=== Phase-A: 열화상태 Device Envelope 그리드 스윕 시작 ===" | tee phase_a_degraded_grid_sweep.log
echo "시작 시간: $(date)" | tee -a phase_a_degraded_grid_sweep.log
echo "장치: /dev/nvme1n1" | tee -a phase_a_degraded_grid_sweep.log
echo "마운트 포인트: /rocksdb" | tee -a phase_a_degraded_grid_sweep.log
echo "작업 디렉토리: /rocksdb" | tee -a phase_a_degraded_grid_sweep.log
echo "주의: 이 스크립트는 Phase-B 완료 후에 실행해야 합니다!" | tee -a phase_a_degraded_grid_sweep.log
echo "" | tee -a phase_a_degraded_grid_sweep.log

# 작업 디렉토리를 /rocksdb로 변경
cd /rocksdb
echo "작업 디렉토리 변경: $(pwd)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log

# 초기 상태 결과 확인
if [ ! -f "/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/initial_state_results.json" ]; then
    echo "ERROR: 초기 상태 결과 파일이 없습니다!" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    exit 1
fi

echo "초기 상태 결과 파일 확인됨" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log

echo "1. 열화 상태 Block Size 스윕 실행 중..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log

# Block Size Sweep for Random Write
for bs in 4k 8k 16k 32k 64k 128k 256k 512k 1m; do
    echo "  - Random Write ${bs}..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=bs_sweep_randwrite_${bs}_degraded --filename=./bs_sweep_randwrite_${bs}_degraded_test --size=1G --rw=randwrite --bs=${bs} --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=bs_sweep_randwrite_${bs}_degraded.json
done

# Block Size Sweep for Random Read
for bs in 4k 8k 16k 32k 64k 128k 256k 512k 1m; do
    echo "  - Random Read ${bs}..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=bs_sweep_randread_${bs}_degraded --filename=./bs_sweep_randread_${bs}_degraded_test --size=1G --rw=randread --bs=${bs} --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=bs_sweep_randread_${bs}_degraded.json
done

# Block Size Sweep for Sequential Write
for bs in 4k 8k 16k 32k 64k 128k 256k 512k 1m; do
    echo "  - Sequential Write ${bs}..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=bs_sweep_write_${bs}_degraded --filename=./bs_sweep_write_${bs}_degraded_test --size=1G --rw=write --bs=${bs} --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=bs_sweep_write_${bs}_degraded.json
done

# Block Size Sweep for Sequential Read
for bs in 4k 8k 16k 32k 64k 128k 256k 512k 1m; do
    echo "  - Sequential Read ${bs}..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=bs_sweep_read_${bs}_degraded --filename=./bs_sweep_read_${bs}_degraded_test --size=1G --rw=read --bs=${bs} --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=bs_sweep_read_${bs}_degraded.json
done

echo "2. 열화 상태 Queue Depth 스윕 실행 중..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log

# Queue Depth Sweep for Random Write
for qd in 1 2 4 8 16 32 64 128; do
    echo "  - Random Write QD${qd}..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=qd_sweep_randwrite_qd${qd}_degraded --filename=./qd_sweep_randwrite_qd${qd}_degraded_test --size=1G --rw=randwrite --bs=4k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=${qd} --numjobs=1 --output-format=json --output=qd_sweep_randwrite_qd${qd}_degraded.json
done

# Queue Depth Sweep for Sequential Write
for qd in 1 2 4 8 16 32 64 128; do
    echo "  - Sequential Write QD${qd}..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=qd_sweep_write_qd${qd}_degraded --filename=./qd_sweep_write_qd${qd}_degraded_test --size=1G --rw=write --bs=4k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=${qd} --numjobs=1 --output-format=json --output=qd_sweep_write_qd${qd}_degraded.json
done

echo "3. 열화 상태 Parallel Jobs 스윕 실행 중..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log

# Parallel Jobs Sweep for Random Write
for jobs in 1 2 4 8 16 32; do
    echo "  - Random Write Jobs${jobs}..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=concurrent_sweep_randwrite_jobs${jobs}_degraded --filename=./concurrent_sweep_randwrite_jobs${jobs}_degraded_test --size=1G --rw=randwrite --bs=4k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=${jobs} --output-format=json --output=concurrent_sweep_randwrite_jobs${jobs}_degraded.json
done

# Parallel Jobs Sweep for Random Read
for jobs in 1 2 4 8 16 32; do
    echo "  - Random Read Jobs${jobs}..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=concurrent_sweep_randread_jobs${jobs}_degraded --filename=./concurrent_sweep_randread_jobs${jobs}_degraded_test --size=1G --rw=randread --bs=4k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=${jobs} --output-format=json --output=concurrent_sweep_randread_jobs${jobs}_degraded.json
done

echo "4. 열화 상태 Mixed R/W Ratio 스윕 실행 중..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log

# Mixed R/W Ratio Sweep for 4k
for ratio in 0 10 25 50 75 90 100; do
    echo "  - Mixed R/W 4k R${ratio}%..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=mixed_sweep_4k_r${ratio}_degraded --filename=./mixed_sweep_4k_r${ratio}_degraded_test --size=1G --rw=rw --bs=4k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --rwmixread=${ratio} --output-format=json --output=mixed_sweep_4k_r${ratio}_degraded.json
done

# Mixed R/W Ratio Sweep for 16k
for ratio in 0 10 25 50 75 90 100; do
    echo "  - Mixed R/W 16k R${ratio}%..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=mixed_sweep_16k_r${ratio}_degraded --filename=./mixed_sweep_16k_r${ratio}_degraded_test --size=1G --rw=rw --bs=16k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --rwmixread=${ratio} --output-format=json --output=mixed_sweep_16k_r${ratio}_degraded.json
done

# Mixed R/W Ratio Sweep for 64k
for ratio in 0 10 25 50 75 90 100; do
    echo "  - Mixed R/W 64k R${ratio}%..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=mixed_sweep_64k_r${ratio}_degraded --filename=./mixed_sweep_64k_r${ratio}_degraded_test --size=1G --rw=rw --bs=64k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --rwmixread=${ratio} --output-format=json --output=mixed_sweep_64k_r${ratio}_degraded.json
done

# Mixed R/W Ratio Sweep for 128k
for ratio in 0 10 25 50 75 90 100; do
    echo "  - Mixed R/W 128k R${ratio}%..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
    fio --name=mixed_sweep_128k_r${ratio}_degraded --filename=./mixed_sweep_128k_r${ratio}_degraded_test --size=1G --rw=rw --bs=128k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --rwmixread=${ratio} --output-format=json --output=mixed_sweep_128k_r${ratio}_degraded.json
done

echo "5. 결과를 data 디렉토리로 이동..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
mv *_degraded.json /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/ 2>/dev/null || true

echo "=== Phase-A 열화상태 Device Envelope 그리드 스윕 완료 ===" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
echo "완료 시간: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
echo "결과 파일:" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
ls -la /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/ | grep degraded | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log

echo "열화 상태 Device Envelope 그리드 스윕이 완료되었습니다!" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
echo "주요 결과:" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
echo "  - Block Size 스윕: 36개 테스트" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
echo "  - Queue Depth 스윕: 16개 테스트" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
echo "  - Parallel Jobs 스윕: 12개 테스트" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
echo "  - Mixed R/W Ratio 스윕: 28개 테스트" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
echo "  - 총 테스트: 92개" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_grid_sweep.log
