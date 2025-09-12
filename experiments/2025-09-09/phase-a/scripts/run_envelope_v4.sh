#!/bin/bash

# Phase-A: Device Envelope Measurement for v4 Model
# 4D 그리드 스윕을 통한 실제 장치 특성 측정 (180개 포인트)

set -e

# 설정
DEVICE="/dev/nvme1n1p2"  # raw NVMe 디스크 직접 접근
OUTPUT_DIR="device_envelope_results"
RUNTIME=30
RAMP_TIME=10

echo "=== Phase-A: Device Envelope Measurement for v4 Model ==="
echo "Device: $DEVICE"
echo "Output Directory: $OUTPUT_DIR"
echo "Runtime: ${RUNTIME}s, Ramp: ${RAMP_TIME}s"
echo "Grid: 5×4×3×3 = 180 points"
echo ""

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

# 디스크 접근 권한 확인
echo "Checking device access permissions..."
if [ ! -r "$DEVICE" ]; then
    echo "Warning: Cannot read $DEVICE directly. Will use sudo for fio commands."
    USE_SUDO=true
else
    echo "Device $DEVICE is accessible."
    USE_SUDO=false
fi

# 그리드 스윕 실행
echo "Starting fio 4D grid sweep..."
echo "Parameters:"
echo "  - rho_r (read ratio): 0, 25, 50, 75, 100%"
echo "  - iodepth: 1, 4, 16, 64"
echo "  - numjobs: 1, 2, 4"
echo "  - bs (block size): 4, 64, 1024 KiB"
echo ""

count=0
total=180

for rho_r in 0 25 50 75 100; do
    for iodepth in 1 4 16 64; do
        for numjobs in 1 2 4; do
            for bs_k in 4 64 1024; do
                count=$((count + 1))
                echo "[$count/$total] Testing: rho_r=${rho_r}%, iodepth=${iodepth}, numjobs=${numjobs}, bs=${bs_k}K"
                
                # fio 실행 (sudo 권한 필요시)
                if [ "$USE_SUDO" = true ]; then
                    sudo fio --name=mixed_io \
                        --filename="$DEVICE" \
                        --rw=randrw \
                        --rwmixread=$rho_r \
                        --bs=${bs_k}k \
                        --ioengine=libaio \
                        --iodepth=$iodepth \
                        --numjobs=$numjobs \
                        --runtime=$RUNTIME \
                        --ramp_time=$RAMP_TIME \
                        --direct=1 \
                        --group_reporting \
                        --output-format=json \
                        --output="$OUTPUT_DIR/result_${rho_r}_${iodepth}_${numjobs}_${bs_k}.json"
                else
                    fio --name=mixed_io \
                        --filename="$DEVICE" \
                        --rw=randrw \
                        --rwmixread=$rho_r \
                        --bs=${bs_k}k \
                        --ioengine=libaio \
                        --iodepth=$iodepth \
                        --numjobs=$numjobs \
                        --runtime=$RUNTIME \
                        --ramp_time=$RAMP_TIME \
                        --direct=1 \
                        --group_reporting \
                        --output-format=json \
                        --output="$OUTPUT_DIR/result_${rho_r}_${iodepth}_${numjobs}_${bs_k}.json"
                fi
                
                # 진행률 표시
                if [ $((count % 20)) -eq 0 ]; then
                    echo "Progress: $count/$total ($((count * 100 / total))%)"
                fi
            done
        done
    done
done

echo ""
echo "=== Phase-A Complete ==="
echo "Results saved in: $OUTPUT_DIR/"
echo "Total files: $(ls -1 $OUTPUT_DIR/*.json | wc -l)"
echo ""
echo "Next step: Run envelope analysis script"
