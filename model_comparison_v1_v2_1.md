# RocksDB Put Model v1 vs v2.1 비교

## 📊 개요

이 문서는 RocksDB Put Model의 v1과 v2.1 버전 간의 주요 차이점과 개선사항을 설명합니다.

## 🔄 주요 변경사항

### 1. Mixed I/O Capacity 모델링

#### v1 (기본 모델)
```math
S_write = B_w / w_req
S_read  = B_r / r_req
S_mix   = B_eff / (w_req + η · r_req)
S_max = min(S_write, S_read, S_mix)
```

#### v2.1 (개선된 모델)
```math
B_eff(ρ_r, ρ_w) = 1 / (ρ_r / B_r + ρ_w / B_w)
```

**개선점:**
- Compaction 시 읽기/쓰기가 동시에 발생하는 현실적 상황 반영
- Harmonic mean을 사용한 더 정확한 혼합 I/O 대역폭 계산
- ρ_r, ρ_w: 실제 LOG에서 측정된 읽기/쓰기 비율

### 2. Per-Level Capacity & Concurrency

#### v1
- 레벨별 제약사항 미고려
- 전체 시스템을 단일 병목으로 가정

#### v2.1
```math
Device write bytes/s = WA_device · S_put
Per-level writes W_l = share_l · (WA_device · S_put)
Per-level reads R_l = (read_to_write)_l · W_l

Global I/O: Σ_l (W_l + R_l) ≤ B_eff
Level capacity: (W_l + R_l) ≤ k_l · s_l · μ_eff_l · B_eff
```

**개선점:**
- 각 레벨별 쓰기 공유율 (share_l) 고려
- 레벨별 읽기/쓰기 비율 (read_to_write)_l) 반영
- 동시성 제약 (k_l, s_l) 및 효율성 (μ_eff_l) 모델링

### 3. Stall Duty Cycle

#### v1
- Stall 효과 미고려

#### v2.1
```math
S_put(final) = (1 - p_stall) · S_put(feasible)
```

**개선점:**
- L0 score, pending compactions에 의한 stall 효과 반영
- 실제 시스템의 간헐적 성능 저하 모델링

## 📈 파라미터 비교

| 파라미터 | v1 | v2.1 | 설명 |
|----------|----|----|------|
| B_r, B_w | ✅ | ✅ | 순수 읽기/쓰기 대역폭 |
| η | ✅ | ❌ | 읽기 오버헤드 (v2.1에서 제거) |
| ρ_r, ρ_w | ❌ | ✅ | 읽기/쓰기 혼합 비율 |
| WA_device | ✅ | ✅ | 디바이스 쓰기 증폭 |
| share_l | ❌ | ✅ | 레벨별 쓰기 공유율 |
| (read_to_write)_l | ❌ | ✅ | 레벨별 읽기/쓰기 비율 |
| k_l, s_l | ❌ | ✅ | 동시성 제약 |
| μ_eff_l | ❌ | ✅ | 레벨별 효율성 |
| p_stall | ❌ | ✅ | Stall 확률 |

## 🎯 검증 방법 차이

### v1 검증
1. Phase-A: B_r, B_w 측정
2. Phase-B: WA, CR 측정
3. Phase-C: 기본 WAF 분석
4. Phase-D: S_max 계산 및 비교

### v2.1 검증
1. Phase-A: B_r, B_w, B_eff(ρ_r, ρ_w) 측정
2. Phase-B: WA, CR, stall 통계 측정
3. Phase-C: Per-level WAF 및 동시성 분석
4. Phase-D: v2.1 모델로 S_max 계산
5. Phase-E: 민감도 분석 (stall, mix ratio)

## 📊 예상 정확도 개선

### v1 모델 한계
- **과대추정**: Mixed I/O 상황에서 실제보다 높은 성능 예측
- **레벨 무시**: LSM-tree의 레벨별 특성 미반영
- **Stall 무시**: 실제 시스템의 간헐적 성능 저하 미고려

### v2.1 모델 개선
- **현실적 모델링**: 실제 Compaction 패턴 반영
- **세밀한 분석**: 레벨별 상세 분석 가능
- **Stall 고려**: 실제 운영 환경의 성능 변동성 반영

## 🔧 마이그레이션 가이드

### 기존 v1 실험에서 v2.1로 전환

1. **추가 측정 필요**:
   ```bash
   # ρ_r, ρ_w 측정을 위한 추가 fio 테스트
   fio --name=mixed --filename=/dev/nvme1n1p1 --rw=rw --rwmixread=50 --bs=128k --iodepth=32 --time_based=1 --runtime=60
   ```

2. **LOG 분석 확장**:
   ```bash
   # Per-level 분석을 위한 추가 스크립트
   python3 scripts/per_level_breakdown.py --log ./log/LOG --out-dir phase-c-results
   ```

3. **Stall 통계 수집**:
   ```bash
   # Stall 관련 통계 수집
   grep -E "(stall|L0|pending)" ./log/LOG > stall_stats.txt
   ```

## 📈 예상 결과

### 정확도 개선
- **v1**: ±20-30% 오차
- **v2.1**: ±10-15% 오차 (예상)

### 분석 깊이
- **v1**: 시스템 전체 수준
- **v2.1**: 레벨별 상세 분석

### 실용성
- **v1**: 기본 성능 예측
- **v2.1**: 튜닝 가이드 제공

## 🚀 권장사항

1. **신규 실험**: v2.1 모델 사용 권장
2. **기존 데이터**: v1과 v2.1 결과 비교 분석
3. **운영 환경**: v2.1의 stall 모델링이 특히 유용

---

**참고**: 이 비교는 `putmodel_v2_1.html`의 내용을 바탕으로 작성되었습니다.
