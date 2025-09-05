# RocksDB 모델 검증 실행 가이드

이 가이드는 `rocksdb_validation_plan.md`에 따라 이론 모델을 실제 RocksDB 시스템에서 검증하는 방법을 설명합니다.

## 🚀 빠른 시작

### 1. 환경 준비

```bash
# 가상환경 활성화
source .venv/bin/activate

# 필요한 패키지 확인
pip list | grep matplotlib
```

### 2. 디바이스 캘리브레이션 (Phase-A)

```bash
# Write 대역폭 측정
fio --name=w --filename=/dev/nvme0n1 --rw=write --bs=128k --iodepth=32 \
    --numjobs=1 --time_based=1 --runtime=60

# Read 대역폭 측정  
fio --name=r --filename=/dev/nvme0n1 --rw=read --bs=128k --iodepth=32 \
    --time_based=1 --runtime=60

# Mixed 대역폭 측정
fio --name=rw --filename=/dev/nvme0n1 --rw=rw --rwmixread=50 --bs=128k \
    --iodepth=32 --time_based=1 --runtime=60
```

### 3. RocksDB 벤치마크 실행 (Phase-B)

```bash
# RocksDB 벤치마크 실행
./db_bench --options_file=rocksdb_bench_templates/db/options-leveled.ini \
  --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 \
  --db=/rocksdb/data --wal_dir=/rocksdb/wal --statistics=1

# LOG 파일에서 통계 수집
# LOG 파일은 보통 /rocksdb/data/LOG에 생성되며, 심볼릭 링크로 ./log/LOG에 연결
```

### 4. 모델 검증 실행

#### 4.1 S_max 계산 (Phase-D)

```bash
# 측정된 디바이스 특성으로 S_max 계산
python3 scripts/smax_calc.py --cr 0.5 --wa 8.0 --bw 1000 --br 2000 --beff 2500 --eta 0.5 --wwal 1.0

# JSON 형식으로 출력 (자동화용)
python3 scripts/smax_calc.py --cr 0.5 --wa 8.0 --bw 1000 --br 2000 --beff 2500 --eta 0.5 --wwal 1.0 --json
```

#### 4.2 Per-Level WAF 분석 (Phase-C)

```bash
# RocksDB LOG에서 WAF 분석
python3 scripts/waf_analyzer.py --log /path/to/rocksdb/LOG \
  --user-mb 1000 --out-dir validation_results --plot

# 결과 확인
ls -la validation_results/
cat validation_results/summary.json
```

## 📊 검증 결과 해석

### 1. S_max 계산 결과

```
최종 S_max: 200.0 MiB/s
병목 지점: write
ops/s (1KB KV): 204800
```

**해석:**
- **S_max**: 이론적으로 계산된 최대 지속 가능한 put rate
- **병목 지점**: write/read/mixed 중 어떤 것이 제한 요소인지
- **ops/s**: 초당 처리 가능한 operation 수

### 2. WAF 분석 결과

```
=== Mass Balance 검증 ===
예상 쓰기: 9567902.50 MB
실제 쓰기: 9567902.50 MB
오류율: 0.00%
✅ Mass balance 검증 통과 (≤10%)
```

**해석:**
- **Mass Balance**: 이론적 예측과 실제 측정값의 일치도
- **오류율 ≤10%**: 검증 성공 기준
- **Per-Level WAF**: 각 레벨별 쓰기 앰플리피케이션

## 🔍 검증 성공 기준

### 1. 정량적 기준

- **Envelope error**: |S_max^meas - S_max^pred| / S_max^pred ≤ **10%**
- **Mass-balance error**: |∑Write_i - CR×WA×user_MB| / (CR×WA×user_MB) ≤ **10%**
- **Stabilization**: pending_compaction_bytes의 장기 기울기 ≤ 0

### 2. 정성적 기준

- **Stall time 패턴**: boundary 아래/근처/위에서 예상되는 단조 패턴
- **트렌드 일치**: 파라미터 변경 시 성능 변화 방향이 모델과 일치

## 🛠️ 고급 검증

### 1. Sensitivity Analysis (Phase-E)

```bash
# 압축률 변화에 따른 S_max 변화
python3 scripts/smax_calc.py --cr 0.3 --wa 8.0 --bw 1000 --br 2000 --beff 2500
python3 scripts/smax_calc.py --cr 0.5 --wa 8.0 --bw 1000 --br 2000 --beff 2500
python3 scripts/smax_calc.py --cr 0.7 --wa 8.0 --bw 1000 --br 2000 --beff 2500

# Write Amplification 변화에 따른 S_max 변화
python3 scripts/smax_calc.py --cr 0.5 --wa 4.0 --bw 1000 --br 2000 --beff 2500
python3 scripts/smax_calc.py --cr 0.5 --wa 8.0 --bw 1000 --br 2000 --beff 2500
python3 scripts/smax_calc.py --cr 0.5 --wa 12.0 --bw 1000 --br 2000 --beff 2500
```

### 2. 실제 성능 측정

```bash
# 예측된 S_max 주변에서 실제 성능 측정
# 0.9 × S_max, 1.0 × S_max, 1.1 × S_max에서 벤치마크 실행

# 예: S_max = 200 MiB/s인 경우
# 180 MiB/s, 200 MiB/s, 220 MiB/s에서 테스트
```

## 📈 결과 보고서 템플릿

### 1. 디바이스 캘리브레이션 결과

| 측정 항목 | 값 (MiB/s) | fio 파라미터 |
|-----------|------------|--------------|
| B_w (Write) | 1000 | bs=128k, iodepth=32 |
| B_r (Read) | 2000 | bs=128k, iodepth=32 |
| B_eff (Mixed) | 2500 | rwmixread=50 |

### 2. S_max 검증 결과

| 파라미터 | 예측값 | 측정값 | 오류율 |
|----------|--------|--------|--------|
| S_max | 200.0 MiB/s | 195.0 MiB/s | 2.5% |
| Mass Balance | 1000 MB | 1020 MB | 2.0% |

### 3. Sensitivity 분석 결과

| CR | WA | S_max | 병목 |
|----|----|-------|------|
| 0.3 | 8.0 | 333.3 | write |
| 0.5 | 8.0 | 200.0 | write |
| 0.7 | 8.0 | 142.9 | write |

## ⚠️ 주의사항

### 1. 환경 요구사항

- **전용 머신**: 다른 프로세스의 I/O 간섭 방지
- **충분한 디스크 공간**: 최소 10GB 이상 여유 공간
- **안정적인 전원**: 장시간 실행 중 중단 방지

### 2. 측정 정확도

- **3회 이상 반복**: 통계적 신뢰성 확보
- **충분한 실행 시간**: 최소 60초 이상
- **시스템 안정화**: 측정 전 5분 대기

### 3. 로그 분석

- **LOG 파일 위치**: RocksDB 설정에 따라 다름
- **통계 활성화**: `statistics=true` 설정 확인
- **충분한 데이터**: 최소 1시간 이상의 로그 필요

## 🎯 성공적인 검증을 위한 팁

1. **단계별 접근**: 한 번에 모든 것을 검증하려 하지 말고 단계별로 진행
2. **충분한 데이터**: 작은 데이터셋으로는 정확한 측정 어려움
3. **환경 통제**: 가능한 한 일정한 환경에서 측정
4. **문서화**: 모든 설정과 결과를 기록하여 재현 가능하게 유지

## 📞 문제 해결

### 자주 발생하는 문제

1. **LOG 파일을 찾을 수 없음**
   - RocksDB 설정에서 `statistics=true` 확인
   - LOG 파일 경로 확인

2. **Mass balance 검증 실패**
   - 충분한 데이터 수집 시간 확보
   - 압축률(CR) 정확한 측정

3. **S_max 계산 오류**
   - 디바이스 대역폭 측정 정확성 확인
   - Write Amplification 값 검증

이 가이드를 따라하면 이론 모델을 실제 RocksDB 시스템에서 성공적으로 검증할 수 있습니다.
