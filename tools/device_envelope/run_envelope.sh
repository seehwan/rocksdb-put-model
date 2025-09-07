#!/bin/bash
# PutModel v4 Device Envelope fio Grid Sweep
# 180개 포인트 그리드 스윕 실행

DEVICE="/dev/nvme1n1p1"
OUTPUT_DIR="device_envelope_results"
FIO_RUNTIME=30
FIO_RAMP_TIME=10

echo "=== PutModel v4 Device Envelope fio Grid Sweep ==="
echo "Device: $DEVICE"
echo "Output Directory: $OUTPUT_DIR"
echo "Runtime: ${FIO_RUNTIME}s + ${FIO_RAMP_TIME}s ramp"
echo "Total Points: 180 (5×4×3×3)"
echo ""

# 출력 디렉토리 생성
mkdir -p $OUTPUT_DIR

# 진행 상황 추적
total_points=180
current_point=0

# 그리드 스윕 실행
for rho_r in 0 25 50 75 100; do
    for iodepth in 1 4 16 64; do
        for numjobs in 1 2 4; do
            for bs_k in 4 64 1024; do
                current_point=$((current_point + 1))
                echo "[$current_point/$total_points] Testing: rho_r=${rho_r}%, iodepth=${iodepth}, numjobs=${numjobs}, bs=${bs_k}K"
                
                # fio 명령 실행
                fio --name=mixed_test \
                    --filename=${DEVICE} \
                    --ioengine=io_uring \
                    --direct=1 \
                    --rw=randrw \
                    --rwmixread=${rho_r} \
                    --iodepth=${iodepth} \
                    --numjobs=${numjobs} \
                    --bs=${bs_k}k \
                    --runtime=${FIO_RUNTIME} \
                    --ramp_time=${FIO_RAMP_TIME} \
                    --norandommap=1 \
                    --randrepeat=0 \
                    --output-format=json \
                    --output=${OUTPUT_DIR}/result_${rho_r}_${iodepth}_${numjobs}_${bs_k}.json \
                    --quiet
                
                # 진행률 표시
                progress=$((current_point * 100 / total_points))
                echo "Progress: ${progress}%"
                echo ""
            done
        done
    done
done

echo "=== fio Grid Sweep Complete ==="
echo "Results saved to: $OUTPUT_DIR"
echo "Total files: $(ls -1 $OUTPUT_DIR/*.json | wc -l)"

# 결과 요약
echo ""
echo "=== Quick Summary ==="
echo "Checking for successful runs..."
successful_runs=0
failed_runs=0

for file in $OUTPUT_DIR/*.json; do
    if [ -f "$file" ] && [ -s "$file" ]; then
        # JSON 파일이 유효한지 확인
        if python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
            successful_runs=$((successful_runs + 1))
        else
            failed_runs=$((failed_runs + 1))
            echo "Invalid JSON: $file"
        fi
    else
        failed_runs=$((failed_runs + 1))
        echo "Missing or empty: $file"
    fi
done

echo "Successful runs: $successful_runs"
echo "Failed runs: $failed_runs"
echo "Success rate: $((successful_runs * 100 / total_points))%"

if [ $successful_runs -eq $total_points ]; then
    echo "✅ All runs completed successfully!"
else
    echo "⚠️  Some runs failed. Check the output above."
fi
