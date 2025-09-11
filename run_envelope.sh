#!/bin/bash

# Phase-A: Device Envelope Measurement
# fio 그리드 스윕을 통한 실제 장치 특성 측정

set -e

# 설정
DEVICE="/dev/nvme1n1p2"  # 사용 가능한 NVMe 디스크
OUTPUT_DIR="device_envelope_results"
RUNTIME=30
RAMP_TIME=10

echo "=== Phase-A: Device Envelope Measurement ==="
echo "Device: $DEVICE"
echo "Output Directory: $OUTPUT_DIR"
echo "Runtime: ${RUNTIME}s, Ramp: ${RAMP_TIME}s"
echo ""

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

# 그리드 스윕 실행
echo "Starting fio grid sweep..."
echo "Total combinations: 5 × 4 × 3 × 3 = 180 points"
echo ""

count=0
total=180

for rho_r in 0 25 50 75 100; do
    for iodepth in 1 4 16 64; do
        for numjobs in 1 2 4; do
            for bs_k in 4 64 1024; do
                count=$((count + 1))
                echo "[$count/$total] Testing: rho_r=${rho_r}%, iodepth=${iodepth}, numjobs=${numjobs}, bs=${bs_k}K"
                
                # fio 실행
                fio --name=mixed_test \
                    --filename=${DEVICE} \
                    --ioengine=io_uring \
                    --direct=1 \
                    --rw=randrw \
                    --rwmixread=${rho_r} \
                    --iodepth=${iodepth} \
                    --numjobs=${numjobs} \
                    --bs=${bs_k}k \
                    --runtime=${RUNTIME} \
                    --ramp_time=${RAMP_TIME} \
                    --norandommap=1 \
                    --randrepeat=0 \
                    --output-format=json \
                    --output=${OUTPUT_DIR}/result_${rho_r}_${iodepth}_${numjobs}_${bs_k}.json \
                    --quiet
                
                # 진행률 표시
                if [ $((count % 20)) -eq 0 ]; then
                    echo "Progress: $count/$total ($((count * 100 / total))%)"
                fi
            done
        done
    done
done

echo ""
echo "=== Grid sweep completed ==="
echo "Results saved in: $OUTPUT_DIR/"
echo "Total files: $(ls -1 $OUTPUT_DIR/*.json | wc -l)"

# 결과 요약
echo ""
echo "=== Summary ==="
echo "Device: $DEVICE"
echo "Total combinations: $total"
echo "Completed: $count"
echo "Output directory: $OUTPUT_DIR"
