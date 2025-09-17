# Phase-B: RocksDB FillRandom 실험 계획

## 🎯 목표
- **FillRandom 워크로드 실행**: 시간별 성능 변화 측정
- **LOG 파일 수집**: 상세한 RocksDB 내부 동작 로그
- **Compaction 분석**: 시간별 Compaction 패턴 및 성능 영향
- **안정화 여부 확인**: RocksDB가 안정적인 Put 속도에 도달하는지 검증

## 📋 실험 절차

### 1. 장치 파티셔닝 및 마운트
```bash
# 1. 기존 파티션 정리
sudo umount /dev/nvme1n1p1 2>/dev/null || true
sudo umount /dev/nvme1n1p2 2>/dev/null || true
sudo umount /dev/nvme1n1 2>/dev/null || true

# 2. 파티션 테이블 생성
sudo parted /dev/nvme1n1 mklabel gpt
sudo parted /dev/nvme1n1 mkpart primary 1MB 10GB    # WAL 파티션
sudo parted /dev/nvme1n1 mkpart primary 10GB 100%   # Data 파티션

# 3. 파일시스템 생성
sudo mkfs.f2fs /dev/nvme1n1p1  # WAL용
sudo mkfs.f2fs /dev/nvme1n1p2  # Data용

# 4. 마운트
sudo mkdir -p /rocksdb/wal /rocksdb/data
sudo mount /dev/nvme1n1p1 /rocksdb/wal
sudo mount /dev/nvme1n1p2 /rocksdb/data
sudo chown -R sslab:sslab /rocksdb
```

### 2. RocksDB 설정 및 FillRandom 실행
```bash
# FillRandom 실행 (LOG 파일 저장)
./db_bench --benchmarks=fillrandom \
  --db=/rocksdb/data \
  --wal_dir=/rocksdb/wal \
  --num=1000000000 \
  --value_size=1024 \
  --key_size=16 \
  --threads=32 \
  --stats_interval=1000000 \
  --stats_dump_period_sec=10 \
  --log_file=/rocksdb/data/LOG \
  --log_level=INFO \
  --max_log_file_size=1073741824 \
  --keep_log_file_num=10
```

### 3. 모니터링 및 데이터 수집
- **성능 지표**: 초당 Put 수, 처리량, 지연시간
- **LOG 분석**: Compaction 이벤트, 메모리 사용량, 레벨별 상태
- **시간별 변화**: 안정화 구간, 성능 저하 구간 식별

## 📊 예상 결과
- **초기 성능**: 높은 Put 속도 (초기 상태)
- **성능 저하**: Compaction 시작 후 성능 감소
- **안정화**: 일정 시간 후 안정적인 성능 구간 도달
- **최종 성능**: 장기간 안정화된 Put 속도

## 📁 출력 파일
- `LOG`: RocksDB 상세 로그
- `fillrandom_results.json`: 성능 측정 결과
- `compaction_analysis.json`: Compaction 패턴 분석
- `time_series_plots.png`: 시간별 성능 변화 시각화