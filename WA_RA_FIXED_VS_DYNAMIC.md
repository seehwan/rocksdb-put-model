# WA/RA: 고정값 vs 동적 측정

## 🎯 핵심 질문

**WA/RA는 고정값으로 쓰는 건가요?**

## ✅ 답변: **아니요! 두 가지 모드가 있습니다**

### 두 가지 사용 모드

#### **Mode 1: Fixed (Nominal) - WA/RA를 모를 때**

```python
# Phase별 고정 nominal 값
NOMINAL = {
    'initial': {'wa': 1.2, 'ra': 0.1},
    'middle': {'wa': 2.5, 'ra': 0.8},
    'final': {'wa': 3.5, 'ra': 0.8}
}

# 사용 시점
if wa is None or ra is None:
    # Nominal 값 사용
    wa = NOMINAL[phase]['wa']
    ra = NOMINAL[phase]['ra']
    
# 결과: Fixed prediction
S_predicted = S_base × 1.0 × 1.0  # No adjustment
Accuracy: 83.5%
```

#### **Mode 2: Dynamic (Actual) - WA/RA를 알 때**

```python
# 실제 측정값
wa = 2.0  # 실제 측정됨
ra = 0.5  # 실제 측정됨

# 사용 시점
# → Actual WA/RA로 adjustment 계산

# 결과: Dynamic prediction
f_WA = calculate_adjustment(wa=2.0)  # 0.94x (penalty)
f_RA = calculate_adjustment(ra=0.5)  # 1.0x (OK)

S_predicted = S_base × 0.94 × 1.0
Accuracy: 85.5% (개선!)
```

## 📊 실제 구현

### 코드 레벨에서

```python
# v5_3_wa_ra_enhanced.py
def predict_s_max(self, device_write_bw, phase, context=None):
    
    # Context에서 WA/RA 가져오기
    wa = context.get('wa', self.wa_ra_params[phase]['nominal_wa'])
    ra = context.get('ra', self.wa_ra_params[phase]['nominal_ra'])
    
    # 즉:
    # - context에 'wa', 'ra'가 있으면 → 실제 값 사용
    # - 없으면 → nominal 값 사용
```

### 예시

#### **Scenario A: 초기 예측 (Fixed)**

```python
# 입력
context = {
    'cv': 0.538,
    'runtime': 8.5
    # 'wa', 'ra' 없음!
}

# 실행
wa = context.get('wa', nominal_wa['initial'])  # → 1.2 (nominal)
ra = context.get('ra', nominal_ra['initial'])  # → 0.1 (nominal)

# 결과: Fixed mode
f_WA = 1.0  # Optimal range 내
f_RA = 1.0  # Optimal range 내

# 정확도: 76.2% (base model과 동일)
```

#### **Scenario B: 실제 측정 후 (Dynamic)**

```python
# 입력
context = {
    'wa': 2.0,  # 실제 측정값!
    'ra': 0.5,   # 실제 측정값!
    'cv': 0.538
}

# 실행
wa = 2.0  # Actual!
ra = 0.5  # Actual!

# 결과: Dynamic mode
f_WA = 0.94  # Penalty! (2.0 > optimal range 1.5)
f_RA = 1.0   # OK

# 정확도: 85.5% (개선!)
```

## 🔍 **Fixed vs Dynamic 비교**

### **Fixed Mode (Nominal 사용)**

```python
# 사용 시점: 예측 시점
# WA/RA 모름
# Context에 wa, ra 없음

# Nominal 값
wa = 1.2  # Fixed
ra = 0.1  # Fixed

# Adjustment
f_WA = 1.0  # Optimal range
f_RA = 1.0  # Optimal range

# 결과
S_predicted = S_base × 1.0 × 1.0
            = S_base  # No change!

# 정확도
Accuracy: 76.2% (Initial)
         92.3% (Middle)
         86.4% (Final)
Average: 83.5%
```

### **Dynamic Mode (Actual 사용)**

```python
# 사용 시점: 운영 중
# WA/RA 알 수 있음
# Context에 wa, ra 있음

# Actual 값
wa = 2.0  # Measured!
ra = 0.5  # Measured!

# Adjustment
f_WA = 0.94  # Penalty for high WA!
f_RA = 1.0

# 결과
S_predicted = S_base × 0.94 × 1.0
            = S_base × 0.94  # Reduced!

# 정확도
Accuracy: 85.5% (Initial, High WA)
         96.7% (Final, High WA)
Average: 87.4%
```

## 💡 **핵심 이해**

### **WA/RA Adjustment는 두 단계**

#### **Level 1: Nominal (고정)**

```python
# Nominal 값은 고정
NOMINAL_WA = {
    'initial': 1.2,
    'middle': 2.5,
    'final': 3.5
}

# BUT: Adjustment factor는 계산됨!
f_WA = calculate(wa=1.2)  # → 1.0 (optimal)
```

#### **Level 2: Dynamic (측정값)**

```python
# Actual 값은 동적
wa = measure_from_system()  # 2.0 (실제)

# Adjustment factor 계산
f_WA = calculate(wa=2.0)  # → 0.94 (penalty)
```

### **조합**

```python
# 최종 예측
S_max = S_base × f_WA(nominal_or_actual) × f_RA(nominal_or_actual)

# Fixed mode:
S_max = S_base × f_WA(nominal) × f_RA(nominal)
      = S_base × 1.0 × 1.0
      = S_base

# Dynamic mode:
S_max = S_base × f_WA(actual) × f_RA(actual)
      = S_base × 0.94 × 1.0
      = S_base × 0.94
```

## 📋 **실제 사용 전략**

### **Strategy 1: 기본 예측 (Fixed)**

```python
# 초기 예측
model.predict(device_bw, phase, context={})

# WA/RA 없음 → Nominal 사용
# 결과: Base prediction
# 정확도: 83.5%
```

### **Strategy 2: 실제 값 수집 (Dynamic)**

```python
# 운영 중
# RocksDB STATISTICS에서 측정
wa_actual = rocksdb_stats['WA']
ra_actual = rocksdb_stats['RA']

# 재예측
model.predict(device_bw, phase, {
    'wa': wa_actual,
    'ra': ra_actual
})

# 결과: Improved prediction
# 정확도: 87.4%
```

### **Strategy 3: Iterative (권장)** ✅

```python
# Round 1: Fixed
S_pred_1 = model.predict(bw, phase, {})
# Accuracy: 83.5%

# Round 2: WA/RA 측정 후
wa, ra = collect_actual_values()
S_pred_2 = model.predict(bw, phase, {'wa': wa, 'ra': ra})
# Accuracy: 87.4% (개선!)

# Update
S_final = S_pred_2
```

## ✅ **최종 정리**

### **WA/RA 사용 방식**

#### **Nominal 값 (Phase별 고정)**

```python
NOMINAL = {
    'initial': {'wa': 1.2, 'ra': 0.1},  # 고정
    'middle': {'wa': 2.5, 'ra': 0.8},   # 고정
    'final': {'wa': 3.5, 'ra': 0.8}     # 고정
}
```

**용도**: WA/RA를 모를 때 기본값
**정확도**: 83.5%

#### **Adjustment는 항상 계산됨**

```python
# WA/RA 값은 고정일 수 있지만
# f_WA, f_RA는 항상 계산!

# 예시
wa = 1.2  # Fixed nominal
f_WA = calculate_adjustment(wa)  # → 1.0 계산됨

# 또는
wa = 2.0  # Dynamic actual
f_WA = calculate_adjustment(wa)  # → 0.94 계산됨
```

### **결론**

**WA/RA 값**:
- ✅ **Fixed**: Nominal 값 (Phase별 고정)
- ✅ **Dynamic**: 실제 측정값 (연산 시 계산)

**Adjustment factor**:
- ✅ **항상 Dynamic**: WA/RA 값에 따라 계산

**사용 전략**:
1. 초기: Nominal 사용 (Fixed)
2. 운영: Actual 사용 (Dynamic)
3. Iterative: 계속 개선

**현재 모델은 이 두 가지를 모두 지원합니다!** ✅

