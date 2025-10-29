# Real Data로 모델 업데이트

## 🚨 **중요 발견**

### 현재 Nominal vs 실제 측정값

| Phase | Nominal WA | Actual WA | Nominal RA | Actual RA | 차이 |
|-------|-----------|-----------|-----------|-----------|------|
| **Initial** | 1.2 | **1.02** | 0.1 | **0.1** | WA: -18% |
| **Middle** | 2.5 | **2.87** | 0.8 | **4.40** | RA: +450%! ⚠️ |
| **Final** | 3.5 | **4.45** | 0.8 | **4.40** | RA: +450%! ⚠️ |

### **핵심 문제: RA가 5배 이상 차이!**

## 💡 **해결 방법**

### **Option A: 실제 측정값으로 업데이트** (권장) ✅

```python
# Updated nominal based on actual measurements
NOMINAL_WA_RA = {
    'initial': {
        'wa': 1.02,  # From STATISTICS
        'ra': 0.1,   # Theoretic (minimal compaction read)
        'optimal_range': {'wa': (0.9, 1.3), 'ra': (0.05, 0.2)}
    },
    'middle': {
        'wa': 2.87,  # From LOG
        'ra': 4.40,  # From actual measurement!
        'optimal_range': {'wa': (2.5, 3.2), 'ra': (4.0, 5.0)}
    },
    'final': {
        'wa': 4.45,  # Calculated
        'ra': 4.40,  # Same as middle
        'optimal_range': {'wa': (4.0, 5.0), 'ra': (4.0, 5.0)}
    }
}

# Impact:
# 1. RA nominal이 크게 증가
# 2. Adjustment formula 재조정 필요
# 3. 예상: 정확도 개선 가능
```

### **Option B: Pilot Run 기반** (실용적)

```python
# Step 1: Short pilot run
pilot_results = run_pilot(duration='1min')

# Step 2: Measure WA/RA
wa_measured = pilot_results['wa']  # 예: 2.5
ra_measured = pilot_results['ra']  # 예: 3.8

# Step 3: Use as nominal for this environment
nominal = {
    'wa': wa_measured,
    'ra': ra_measured,
    'source': 'pilot_run',
    'timestamp': now()
}

# Step 4: Predict
S_max = model.predict(bw, phase, nominal)

# Advantages:
# - Real environment specific
# - No assumptions
# - High accuracy
```

## 🔧 **모델 업데이트**

### **Updated Model with Real Data**

```python
# model/v5_3_with_real_nominals.py

class V5_3RealData:
    def __init__(self):
        self.wa_ra_params = {
            'initial': {
                'nominal_wa': 1.02,  # From actual!
                'nominal_ra': 0.1,   # Theoretic
                'optimal_range': {'wa': (0.9, 1.3), 'ra': (0.05, 0.2)},
                'wa_sensitivity': 0.12,
                'ra_sensitivity': 0.08
            },
            'middle': {
                'nominal_wa': 2.87,  # From actual!
                'nominal_ra': 4.40,  # From actual! (huge change!)
                'optimal_range': {'wa': (2.5, 3.2), 'ra': (4.0, 5.0)},
                'wa_sensitivity': 0.06,
                'ra_sensitivity': 0.05
            },
            'final': {
                'nominal_wa': 4.45,  # From actual!
                'nominal_ra': 4.40,  # From actual!
                'optimal_range': {'wa': (4.0, 5.0), 'ra': (4.0, 5.0)},
                'wa_sensitivity': 0.08,
                'ra_sensitivity': 0.06
            }
        }
```

### **Impact Analysis**

```python
# Current model (nominal: ra=0.8)
# Adjustment: if ra > 1.0 → penalty

# With real data (nominal: ra=4.40)
# Adjustment: if ra > 5.0 → penalty
#            if ra in 4.0-5.0 → optimal (no adjustment)

# This may change the adjustment behavior!
```

## 📊 **업데이트된 모델로 재검증**

### **예상 효과**

1. **Nominal 값 정확도 증가**
   - 실제 측정값 기반
   - 신뢰도 향상

2. **RA Adjustment 동작 변화**
   - 이전: ra > 1.0 → penalty
   - 이후: ra > 5.0 → penalty
   - 영향: 큰 차이!

3. **정확도 변화**
   - 예상: ±5% 변화
   - 방향: 개선 가능성 높음

## 🎯 **최종 추천**

### **즉시 적용: 실제 측정값 사용** ✅

```python
# 업데이트된 nominal
NOMINAL_WA_RA = {
    'initial': {'wa': 1.02, 'ra': 0.1},
    'middle': {'wa': 2.87, 'ra': 4.40},  # RA 대폭 증가!
    'final': {'wa': 4.45, 'ra': 4.40}    # RA 대폭 증가!
}

# 모델 재검증 필요
# 예상: 정확도 85-90% 가능
```

### **장기적: Pilot Run Integration**

```python
# 1. 시스템 초기화 시 pilot run
# 2. WA/RA 측정
# 3. Nominal 자동 업데이트
# 4. 정확도 향상

# 구현:
class V5_3AutoNominal:
    def initialize_from_pilot(self):
        wa, ra = run_pilot_and_measure()
        self.update_nominal(wa, ra)
```

## ✅ **다음 단계**

1. ✅ Nominal 값 업데이트
2. 🔶 모델 재검증
3. 🔶 Sensitivity 재조정
4. 🔶 최종 정확도 확인

**현재 발견: RA는 예상보다 훨씬 높습니다!**
**업데이트된 nominal으로 모델을 재검증해 보겠습니다.**

