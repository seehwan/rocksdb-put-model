#!/bin/bash

# Phase-A: Device Envelope Measurement for v4 Model
# 4D 그리드 스윕을 통한 실제 장치 특성 측정 (180개 포인트)

set -e

# 설정
DEVICE="/dev/nvme1n1p2"  # 사용 가능한 NVMe 디스크
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

# 결과 요약 생성
echo "Generating summary..."
python3 - << 'PY'
import json
import os
import numpy as np

def analyze_fio_result(filename):
    """fio JSON 결과 파일 분석"""
    with open(filename, 'r') as f:
        data = json.load(f)
    
    job = data['jobs'][0]
    
    # 대역폭 계산 (KB/s -> MiB/s)
    write_bw = job['write']['bw'] / 1024  # MiB/s
    read_bw = job['read']['bw'] / 1024    # MiB/s
    total_bw = write_bw + read_bw
    
    # IOPS
    write_iops = job['write']['iops']
    read_iops = job['read']['iops']
    total_iops = write_iops + read_iops
    
    # 지연시간 (μs)
    write_lat = job['write']['clat']['mean'] if job['write']['clat']['mean'] is not None else 0
    read_lat = job['read']['clat']['mean'] if job['read']['clat']['mean'] is not None else 0
    
    return {
        'write_bandwidth_mib_s': write_bw,
        'read_bandwidth_mib_s': read_bw,
        'total_bandwidth_mib_s': total_bw,
        'write_iops': write_iops,
        'read_iops': read_iops,
        'total_iops': total_iops,
        'write_latency_us': write_lat,
        'read_latency_us': read_lat
    }

# 모든 결과 파일 분석
results = []
output_dir = 'device_envelope_results'

for filename in os.listdir(output_dir):
    if filename.startswith('result_') and filename.endswith('.json'):
        # 파일명에서 파라미터 추출
        parts = filename.replace('result_', '').replace('.json', '').split('_')
        rho_r = int(parts[0])
        iodepth = int(parts[1])
        numjobs = int(parts[2])
        bs_k = int(parts[3])
        
        # 결과 분석
        result = analyze_fio_result(os.path.join(output_dir, filename))
        result.update({
            'rho_r': rho_r,
            'iodepth': iodepth,
            'numjobs': numjobs,
            'bs_k': bs_k
        })
        results.append(result)

# 결과를 파라미터별로 정렬
results.sort(key=lambda x: (x['rho_r'], x['iodepth'], x['numjobs'], x['bs_k']))

# 요약 통계 계산
total_bandwidths = [r['total_bandwidth_mib_s'] for r in results]
write_bandwidths = [r['write_bandwidth_mib_s'] for r in results]
read_bandwidths = [r['read_bandwidth_mib_s'] for r in results]

summary = {
    'device': '/dev/nvme1n1p2',
    'test_date': '2025-09-09',
    'total_points': len(results),
    'parameters': {
        'rho_r_values': [0, 25, 50, 75, 100],
        'iodepth_values': [1, 4, 16, 64],
        'numjobs_values': [1, 2, 4],
        'bs_k_values': [4, 64, 1024]
    },
    'statistics': {
        'max_total_bandwidth_mib_s': max(total_bandwidths),
        'min_total_bandwidth_mib_s': min(total_bandwidths),
        'avg_total_bandwidth_mib_s': np.mean(total_bandwidths),
        'max_write_bandwidth_mib_s': max(write_bandwidths),
        'max_read_bandwidth_mib_s': max(read_bandwidths)
    },
    'results': results
}

# 결과 저장
with open('device_envelope_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("Device Envelope Measurement Summary:")
print(f"  Total points tested: {len(results)}")
print(f"  Max total bandwidth: {max(total_bandwidths):.1f} MiB/s")
print(f"  Max write bandwidth: {max(write_bandwidths):.1f} MiB/s")
print(f"  Max read bandwidth: {max(read_bandwidths):.1f} MiB/s")
print(f"  Average bandwidth: {np.mean(total_bandwidths):.1f} MiB/s")
print(f"  Results saved to: device_envelope_summary.json")
PY

echo ""
echo "=== Phase-A Device Envelope Measurement 완료 ==="
echo "결과 파일:"
echo "  - device_envelope_results/: 개별 fio 결과 파일들"
echo "  - device_envelope_summary.json: 종합 분석 결과"
