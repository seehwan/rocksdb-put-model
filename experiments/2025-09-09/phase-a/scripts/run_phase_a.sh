#!/bin/bash
# Phase-A: 디바이스 캘리브레이션 실행 스크립트
# 실행일: 2025-09-09

echo "=== Phase-A: 디바이스 캘리브레이션 시작 ==="
echo "디바이스: /dev/nvme1n1p2"
echo "결과 디렉토리: experiments/2025-09-09/phase-a/"
echo ""

# 결과 디렉토리 생성
mkdir -p experiments/2025-09-09/phase-a

# 1. fio 그리드 스윕 실행
echo "1. fio 그리드 스윕 실행 중..."
sudo ./rocksdb_bench_templates/fio/fio_matrix.sh /dev/nvme1n1p2 128k 32 60 > experiments/2025-09-09/phase-a/fio_matrix.csv

# 2. fio 상세 테스트 실행
echo "2. fio 상세 테스트 실행 중..."

# 순수 쓰기 테스트
echo "  - 순수 쓰기 테스트..."
sudo fio --name=write_test --filename=/dev/nvme1n1p2 --rw=write --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > experiments/2025-09-09/phase-a/write_test.json

# 순수 읽기 테스트
echo "  - 순수 읽기 테스트..."
sudo fio --name=read_test --filename=/dev/nvme1n1p2 --rw=read --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > experiments/2025-09-09/phase-a/read_test.json

# 혼합 I/O 테스트 (50:50)
echo "  - 혼합 I/O 테스트 (50:50)..."
sudo fio --name=mixed_test --filename=/dev/nvme1n1p2 --rw=rw --rwmixread=50 --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > experiments/2025-09-09/phase-a/mixed_test.json

# 3. 결과 분석
echo "3. 결과 분석 중..."
python3 - << 'PY'
import json
import csv

def analyze_fio_json(filename):
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

# 각 테스트 결과 분석
write_results = analyze_fio_json('experiments/2025-09-09/phase-a/write_test.json')
read_results = analyze_fio_json('experiments/2025-09-09/phase-a/read_test.json')
mixed_results = analyze_fio_json('experiments/2025-09-09/phase-a/mixed_test.json')

# CSV 파일 분석
csv_results = []
with open('experiments/2025-09-09/phase-a/fio_matrix.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_results.append({
            'mix_read': int(row['mix_read']),
            'mbps': float(row['MBps']),
            'iops': float(row['IOPS']),
            'lat_mean_usec': float(row['lat_mean_usec'])
        })

# 종합 결과 생성
device_calibration = {
    'device': '/dev/nvme1n1p2',
    'test_date': '2025-09-09',
    'write_test': write_results,
    'read_test': read_results,
    'mixed_test': mixed_results,
    'matrix_sweep': csv_results,
    'summary': {
        'max_write_bandwidth_mib_s': write_results['bandwidth_mib_s'],
        'max_read_bandwidth_mib_s': read_results['bandwidth_mib_s'],
        'mixed_bandwidth_mib_s': mixed_results['bandwidth_mib_s'],
        'total_bandwidth_mib_s': write_results['bandwidth_mib_s'] + read_results['bandwidth_mib_s']
    }
}

# 결과 저장
with open('experiments/2025-09-09/phase-a/device_calibration_results.json', 'w') as f:
    json.dump(device_calibration, f, indent=2)

print("디바이스 캘리브레이션 결과:")
print(f"  쓰기 대역폭: {write_results['bandwidth_mib_s']:.1f} MiB/s")
print(f"  읽기 대역폭: {read_results['bandwidth_mib_s']:.1f} MiB/s")
print(f"  혼합 대역폭: {mixed_results['bandwidth_mib_s']:.1f} MiB/s")
print(f"  총 대역폭: {device_calibration['summary']['total_bandwidth_mib_s']:.1f} MiB/s")
PY

# 4. 결과 확인
echo "4. 결과 확인..."
echo "생성된 파일들:"
ls -la experiments/2025-09-09/phase-a/

echo ""
echo "=== Phase-A 완료 ==="
echo "결과 파일 위치: experiments/2025-09-09/phase-a/"
