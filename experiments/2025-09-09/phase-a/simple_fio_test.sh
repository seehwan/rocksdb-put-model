#!/bin/bash
# 간단한 fio 테스트 스크립트

DEV=${1:-/dev/nvme1n1p2}
OUTPUT_DIR=${2:-experiments/2025-09-09/phase-a}

echo "=== 간단한 fio 테스트 시작 ==="
echo "디바이스: $DEV"
echo "결과 디렉토리: $OUTPUT_DIR"
echo ""

# 결과 디렉토리 생성
mkdir -p $OUTPUT_DIR

# 1. 순수 쓰기 테스트
echo "1. 순수 쓰기 테스트..."
sudo fio --name=write_test --filename=$DEV --rw=write --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > $OUTPUT_DIR/write_test.json

# 2. 순수 읽기 테스트  
echo "2. 순수 읽기 테스트..."
sudo fio --name=read_test --filename=$DEV --rw=read --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > $OUTPUT_DIR/read_test.json

# 3. 혼합 I/O 테스트 (50:50)
echo "3. 혼합 I/O 테스트 (50:50)..."
sudo fio --name=mixed_test --filename=$DEV --rw=rw --rwmixread=50 --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > $OUTPUT_DIR/mixed_test.json

# 4. 결과 분석
echo "4. 결과 분석 중..."
python3 - << PY
import json
import os

def analyze_fio_json(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        job = data['jobs'][0]
        bw_kbps = job['bw']
        iops = job['iops']
        lat_mean = job['clat']['mean'] if job['clat']['mean'] is not None else 0
        
        return {
            'bandwidth_mib_s': bw_kbps / 1024,
            'iops': iops,
            'latency_mean_us': lat_mean
        }
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")
        return None

# 각 테스트 결과 분석
write_results = analyze_fio_json('$OUTPUT_DIR/write_test.json')
read_results = analyze_fio_json('$OUTPUT_DIR/read_test.json')
mixed_results = analyze_fio_json('$OUTPUT_DIR/mixed_test.json')

# 결과 출력
print("\\n=== fio 테스트 결과 ===")
if write_results:
    print(f"쓰기 성능: {write_results['bandwidth_mib_s']:.1f} MiB/s, {write_results['iops']:.0f} IOPS")
if read_results:
    print(f"읽기 성능: {read_results['bandwidth_mib_s']:.1f} MiB/s, {read_results['iops']:.0f} IOPS")
if mixed_results:
    print(f"혼합 성능: {mixed_results['bandwidth_mib_s']:.1f} MiB/s, {mixed_results['iops']:.0f} IOPS")

# 종합 결과 생성
device_calibration = {
    'device': '$DEV',
    'test_date': '2025-09-09',
    'write_test': write_results,
    'read_test': read_results,
    'mixed_test': mixed_results,
    'summary': {
        'max_write_bandwidth_mib_s': write_results['bandwidth_mib_s'] if write_results else 0,
        'max_read_bandwidth_mib_s': read_results['bandwidth_mib_s'] if read_results else 0,
        'mixed_bandwidth_mib_s': mixed_results['bandwidth_mib_s'] if mixed_results else 0
    }
}

# 결과 저장
with open('$OUTPUT_DIR/device_calibration_results.json', 'w') as f:
    json.dump(device_calibration, f, indent=2)

print(f"\\n결과가 $OUTPUT_DIR/device_calibration_results.json에 저장되었습니다.")
PY

echo ""
echo "=== 간단한 fio 테스트 완료 ==="
