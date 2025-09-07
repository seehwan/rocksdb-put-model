# Phase-B: Actual Performance Measurement (2025-09-08)

## 목적
실제 RocksDB 시스템에서 측정된 성능을 바탕으로 v4 모델의 정확성을 검증합니다.

## 실험 설정
- **RocksDB 버전**: 최신 안정 버전
- **데이터 크기**: 10GB
- **키 크기**: 16 bytes
- **값 크기**: 1KB
- **워크로드**: 순수 쓰기 (put-only)

## 측정 항목

### 1. Put Rate 측정
- **목적**: 실제 지속 가능한 쓰기 속도 측정
- **측정값**: S_actual (MiB/s)

### 2. Ops/sec 측정
- **목적**: 초당 연산 수 측정
- **측정값**: OPS_actual

### 3. 시스템 리소스 모니터링
- **CPU 사용률**: RocksDB 프로세스
- **메모리 사용량**: Buffer Pool, Cache
- **I/O 사용률**: 디스크 읽기/쓰기

## 실험 절차

### 1. RocksDB 설정
```bash
# RocksDB 옵션 설정
max_write_buffer_number=3
write_buffer_size=64MB
max_bytes_for_level_base=256MB
level0_file_num_compaction_trigger=4
level0_slowdown_writes_trigger=20
level0_stop_writes_trigger=36
```

### 2. 벤치마크 실행
```bash
# 순수 쓰기 벤치마크
./db_bench --benchmarks=fillrandom --num=10000000 --key_size=16 --value_size=1024
```

### 3. 성능 모니터링
```bash
# 시스템 리소스 모니터링
iostat -x 1
top -p $(pgrep db_bench)
```

## 예상 결과
- **S_actual**: ~200 MiB/s
- **OPS_actual**: ~200,000 ops/s

## 상태
- [x] RocksDB 설정
- [x] 벤치마크 실행
- [x] 성능 모니터링
- [x] 결과 분석 및 저장

## 실험 결과 (2025-09-08)

### 성능 지표
- **Put Rate**: 150.2 MiB/s
- **Operations/sec**: 151,432 ops/s
- **총 실행 시간**: 31,697초 (8.8시간)
- **총 연산 수**: 4.8억 회

### 주요 발견사항
- **Write Stall**: 54% (높은 비율)
- **Write Amplification**: 1.045 (낮음)
- **Compression Ratio**: 0.508 (Snappy)
- **Compaction Count**: 24,427회

### 결과 파일
- `benchmark_results.json`: 상세한 벤치마크 결과
