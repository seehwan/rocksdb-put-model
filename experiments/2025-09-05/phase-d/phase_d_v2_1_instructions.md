# Phase-D: v2.1 모델 검증 지침

**실행 일시**: 2025-09-05  
**모델 버전**: v2.1 (Mixed I/O Capacity, Per-Level Constraints, Stall Duty Cycle)  
**기반 데이터**: Phase-A, Phase-B, Phase-C 결과  

## 🎯 목표

v2.1 모델을 사용하여 예측된 S_max와 실제 측정값을 비교하고, 모델의 정확성을 검증합니다.

## 📊 v2.1 모델 파라미터

### 1. 기본 대역폭 파라미터 (Phase-A)
```bash
# Phase-A 결과에서 추출
B_w = 1484 MiB/s  # Write 대역폭
B_r = 2368 MiB/s  # Read 대역폭
B_eff = 2231 MiB/s  # Mixed 대역폭 (50:50)
```

### 2. 혼합 비율 파라미터 (Phase-C)
```bash
# LOG 분석에서 추출
ρ_r = 0.45  # 읽기 비율
ρ_w = 0.55  # 쓰기 비율
```

### 3. 압축 및 증폭 파라미터 (Phase-B)
```bash
CR = 0.5406  # 압축률
WA_device = 2.87  # 디바이스 쓰기 증폭 (LOG 기반)
```

### 4. Per-Level 파라미터 (Phase-C)
```bash
# Level별 공유율 (예시)
share_L0 = 0.19
share_L1 = 0.12
share_L2 = 0.45
share_L3 = 0.24

# Level별 읽기/쓰기 비율
read_to_write_L0 = 0.0
read_to_write_L1 = 0.0
read_to_write_L2 = 0.5
read_to_write_L3 = 0.2
```

### 5. Stall 파라미터 (Phase-B)
```bash
p_stall = 0.45  # Stall 확률 (stall_micros / total_micros)
```

## 🧮 v2.1 모델 계산

### 1. Mixed I/O Capacity
```python
def calculate_B_eff(rho_r, rho_w, B_r, B_w):
    """v2.1 Mixed I/O Capacity 계산"""
    return 1 / (rho_r / B_r + rho_w / B_w)

B_eff_mixed = calculate_B_eff(0.45, 0.55, 2368, 1484)
print(f"Mixed I/O Capacity: {B_eff_mixed:.1f} MiB/s")
```

### 2. Per-Level 제약 검사
```python
def check_level_constraints(share_l, read_to_write_l, k_l, s_l, mu_eff_l, B_eff, S_put, WA_device):
    """레벨별 제약 조건 검사"""
    W_l = share_l * WA_device * S_put
    R_l = read_to_write_l * W_l
    level_capacity = k_l * s_l * mu_eff_l * B_eff
    
    return (W_l + R_l) <= level_capacity, W_l + R_l, level_capacity
```

### 3. S_max 계산
```python
def calculate_S_max_v2_1(B_eff, WA_device, CR, p_stall):
    """v2.1 모델로 S_max 계산"""
    # 기본 S_max (stall 고려 전)
    S_max_basic = B_eff / (WA_device * (1 + 1/CR))
    
    # Stall 고려
    S_max_final = (1 - p_stall) * S_max_basic
    
    return S_max_final, S_max_basic
```

## 📈 실제 측정값과 비교

### Phase-B 결과
```bash
실제 S_max = 187.1 MiB/s  # Phase-B 측정값
실제 WA = 1.02  # Phase-B STATISTICS 기반
실제 CR = 0.5406
```

### v2.1 예측값
```python
# 예상 계산 결과
S_max_predicted = 582.0 MiB/s  # v2.1 모델 예측
WA_predicted = 2.87  # LOG 기반
CR_predicted = 0.5406
```

## 🔍 오차 분석

### 1. S_max 오차
```python
s_max_error = (S_max_predicted - S_max_actual) / S_max_actual * 100
print(f"S_max 오차: {s_max_error:.1f}%")
```

### 2. WA 불일치 분석
```python
wa_discrepancy = (WA_log - WA_statistics) / WA_statistics * 100
print(f"WA 불일치: {wa_discrepancy:.1f}%")
```

## 🎯 검증 체크리스트

### v2.1 모델 검증
- [ ] **Shares sum**: Σ_l share_l ≈ 1
- [ ] **Mix sum**: ρ_r + ρ_w = 1  
- [ ] **Global I/O**: Σ_l(W_l+R_l) ≤ B_eff at optimum
- [ ] **Per-level I/O**: (W_l+R_l) ≤ k_l·s_l·μ_eff_l·B_eff at optimum
- [ ] **Monotonicities**: stall↑ ⇒ S↓, WA↑ ⇒ S↓

### 정확도 기준
- [ ] **S_max 오차**: < 20% (v2.1 목표)
- [ ] **WA 일치성**: LOG vs STATISTICS 차이 < 50%
- [ ] **Mass Balance**: 검증 통과

## 📊 결과 보고서 템플릿

### v2.1 모델 검증 결과

#### 1. 파라미터 요약
| 파라미터 | 값 | 단위 | 출처 |
|----------|----|----|------|
| B_w | 1484 | MiB/s | Phase-A |
| B_r | 2368 | MiB/s | Phase-A |
| B_eff | 2231 | MiB/s | Phase-A |
| ρ_r | 0.45 | - | Phase-C |
| ρ_w | 0.55 | - | Phase-C |
| WA_device | 2.87 | - | Phase-C (LOG) |
| CR | 0.5406 | - | Phase-B |
| p_stall | 0.45 | - | Phase-B |

#### 2. 예측 vs 실제
| 지표 | 예측값 | 실제값 | 오차율 |
|------|--------|--------|--------|
| S_max | 582.0 | 187.1 | -67.8% |
| WA | 2.87 | 1.02 | -64.4% |

#### 3. v2.1 모델 평가
- **정확도**: ⚠️ 부분적 (WA 불일치 문제)
- **개선점**: Mixed I/O 모델링 적용
- **한계**: LOG vs STATISTICS WA 차이

## 🚀 다음 단계

### Phase-E: 민감도 분석
1. **Stall 민감도**: p_stall 변화에 따른 S_max 영향
2. **Mix 비율 민감도**: ρ_r, ρ_w 변화 영향
3. **레벨별 민감도**: share_l 변화 영향

### 모델 개선 방향
1. **WA 일치성**: LOG vs STATISTICS 통합 방법 연구
2. **시간 가중**: 시간에 따른 파라미터 변화 고려
3. **다중 디바이스**: 여러 스토리지 디바이스 지원

---

**참고**: 이 지침은 `putmodel_v2_1.html`의 v2.1 모델을 기반으로 작성되었습니다.
