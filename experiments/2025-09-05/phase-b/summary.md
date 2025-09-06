# Phase-B: RocksDB 벤치마크 실행 결과 요약

**실행 일시**: 2025-09-05  
**RocksDB 버전**: 10.7.0  
**벤치마크**: fillrandom  

## 🎯 주요 성과

### 성능 지표
- **지속 가능한 put rate**: **187.1 MiB/s**
- **실제 ops/s**: **188,617 ops/sec**
- **실행 시간**: **16,965.531 초** (약 4.7시간)
- **총 operations**: **3,200,000,000** (32억 operations)
- **평균 latency**: **84.824 micros/op**

### 압축 및 효율성
- **압축률 (CR)**: **0.5406** (54.06%, 1:1.85 압축 비율)
- **Write Amplification (WA)**: **1.02** (매우 낮음 - 거의 1:1)
- **Compaction 비율**: **0.878** (읽기 대비 쓰기)

### I/O 통계
- **사용자 데이터 크기**: **3,051.76 GB**
- **실제 쓰기 바이트**: **3,115.90 GB**
- **Compaction 읽기**: **13,439.09 GB**
- **Compaction 쓰기**: **11,804.86 GB**
- **Flush 쓰기**: **1,751.57 GB**

### Stall 분석
- **총 Stall 시간**: **7,687.69 초**
- **Stall 비율**: **45.31%** (높음)
- **평균 Stall 시간**: **2.40 micros/op**

## 📊 분석 결과

### ✅ 긍정적 요소
1. **높은 성능**: 187.1 MiB/s의 안정적인 put rate
2. **우수한 압축률**: Snappy 압축이 54% 효과적
3. **매우 낮은 WA**: 1.02로 거의 1:1 비율
4. **효율적인 Compaction**: 0.878 비율로 읽기 대비 쓰기 효율적

### ⚠️ 주의사항
1. **높은 Stall 비율**: 45.31%로 I/O 병목 발생
2. **긴 실행 시간**: 4.7시간으로 장시간 실행
3. **높은 Compaction 읽기**: 13.4TB의 대량 읽기

## 🔍 다음 단계 준비사항

### Phase-C: Per-Level WAF 분석
- [ ] LOG 파일 위치 확인: `./log/LOG`
- [ ] WAF 분석기 실행: `python3 scripts/waf_analyzer.py`
- [ ] Per-Level I/O 분해 분석

### Phase-A: 디바이스 캘리브레이션 (필요시)
- [ ] B_w (Write 대역폭) 측정
- [ ] B_r (Read 대역폭) 측정  
- [ ] B_eff (Mixed 대역폭) 측정

### Phase-D: 모델 검증
- [ ] S_max 예측값 계산
- [ ] 예측값 vs 측정값 비교
- [ ] 오류율 검증 (≤10% 목표)

## 📁 관련 파일
- `benchmark_results.txt`: 전체 벤치마크 결과
- `./log/LOG`: RocksDB LOG 파일 (WAF 분석용)
- `experiment_template.md`: 실험 진행 상황

---
**완료일**: 2025-09-05  
**상태**: ✅ 완료  
**다음 단계**: Phase-C (Per-Level WAF 분석)
