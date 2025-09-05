# 실험 결과 업데이트 템플릿

## Phase-B: RocksDB 벤치마크 실행

### 1. RocksDB 설정
```bash
# RocksDB 빌드
git clone https://github.com/facebook/rocksdb.git
cd rocksdb
make db_bench -j$(nproc)

# 설정 파일 사용
./db_bench --options_file=rocksdb_bench_templates/db/options-leveled.ini \
  --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 \
  --db=/rocksdb/data --statistics=1
```

### 2. 측정 결과
- **실제 CR (압축률)**: ___ (LOG에서 추출)
- **실제 WA (Write Amplification)**: ___ (LOG에서 추출)
- **실제 RA_c (Read Amplification)**: ___ (LOG에서 추출)
- **지속 가능한 put rate**: ___ MiB/s
- **실제 ops/s**: ___

### 3. LOG 파일 분석
```bash
# LOG 파일 위치
LOG_PATH="./log/LOG"

# WAF 분석
python3 scripts/waf_analyzer.py --log $LOG_PATH \
  --user-mb 1000 --out-dir validation_results --plot
```

---

## Phase-C: Per-Level WAF 분석

### 1. 레벨별 I/O 분해
```bash
# Per-level breakdown
python3 scripts/per_level_breakdown.py
```

**결과:**
- L0: Write=___, Read=___
- L1: Write=___, Read=___
- L2: Write=___, Read=___
- L3: Write=___, Read=___
- L4: Write=___, Read=___
- L5: Write=___, Read=___
- L6: Write=___, Read=___

### 2. Mass Balance 검증
- **예상 총 쓰기**: ___ MB
- **실제 총 쓰기**: ___ MB
- **오류율**: ___% (≤10% 목표)

---

## Phase-D: 모델 검증

### 1. S_max 검증
- **예측값**: ___ MiB/s
- **측정값**: ___ MiB/s
- **오류율**: ___% (≤10% 목표)

### 2. 성공 기준 검증
- [ ] Envelope error ≤ 10%
- [ ] Mass-balance error ≤ 10%
- [ ] Stabilization 확인
- [ ] Stall time 패턴 일치

---

## Phase-E: 민감도 분석

### 1. 압축률 변화
- CR=0.3: S_max=___
- CR=0.5: S_max=___
- CR=0.7: S_max=___

### 2. Write Amplification 변화
- WA=4: S_max=___
- WA=8: S_max=___
- WA=12: S_max=___

---

## 최종 검증 결과

### 모델 정확도
- **전체 오류율**: ___%
- **검증 상태**: [ ] 성공 [ ] 부분 성공 [ ] 실패

### 운영 권장사항
- **권장 Rate Limiter**: ___ bytes/sec
- **예상 최대 성능**: ___ ops/s
- **주요 병목**: ___

---

**업데이트 일시**: ___  
**업데이트자**: ___
