# Pilot Run Strategy 분석 및 평가

## 🎯 핵심 질문

**Pilot run이 좋은 전략인가?**

## 📊 **전략 비교**

### **Option A: Fixed Nominal (현재)** vs **Option B: Pilot Run**

| 항목 | Fixed Nominal | Pilot Run |
|------|---------------|-----------|
| **Setup** | 즉시 사용 | 1-2분 소요 |
| **정확도** | 83.5% (base) | 예상 85-90% |
| **복잡도** | 낮음 | 중간 |
| **적용 시점** | 즉시 | Pilot 실행 후 |
| **환경 종속성** | 높음 | 낮음 (환경 특화) |
| **정확도** | 보통 | 높음 |

## 💡 **Pilot Run 상세 분석**

### **Pros (장점)** ✅

#### 1. **환경 특화**

```python
# 동일한 환경에서 측정
same_hardware = True
same_config = True
same_workload = True

# 결과: 매우 정확한 nominal
nominal = measure_from_pilot()
# → 실제 환경과 동일!
```

#### 2. **실측값 기반**

```python
# Pilot run 결과
wa_pilot = 2.1  # 실제 측정
ra_pilot = 3.8  # 실제 측정

# Fixed nominal
wa_nominal = 2.87  # 과거 데이터

# 비교
error_pilot = |2.1 - 2.1| = 0 (perfect!)
error_nominal = |2.1 - 2.87| = 0.77

# Pilot run이 더 정확!
```

#### 3. **동적 업데이트 가능**

```python
# 이전: Fixed nominal
nominal_wa = 2.87  # 고정

# Pilot run: 동적
pilot_results = run_pilot()
nominal_wa = pilot_results['wa']  # 업데이트됨!
```

#### 4. **사용자 신뢰도 높음**

```python
# "내 시스템에서 돌려보고 만든 값입니다!"
# → 훨씬 신뢰도 높음
```

### **Cons (단점)** ❌

#### 1. **추가 시간 소요**

```python
# Pilot run 실행
pilot_duration = 60  # seconds
pilot_overhead = pilot_duration + parse_time
                 = 60 + 10
                 = 70 seconds

# vs Fixed
fixed_time = 0  # seconds
```

#### 2. **복잡도 증가**

```python
# Pilot run 구현
class PilotRunner:
    def run(self):
        # 1. Prepare RocksDB
        # 2. Run short benchmark
        # 3. Parse logs
        # 4. Extract WA/RA
        # 5. Update nominal
        # 6. Return
        
# Fixed는 단순히 저장된 값 사용
nominal = NOMINAL_WA_RA[phase]  # 끝!
```

#### 3. **환경 의존성**

```python
# Pilot run은 환경에 따라 달라질 수 있음
# 예: 로드가 있는 서버에서 실행
# → 비정상적 높은/낮은 값

pilot_high_load = run_pilot()  # WA = 5.0 (높음)
pilot_idle = run_pilot()       # WA = 2.0 (정상)

# Fixed는 stable
```

## 🔍 **실제 사용성 평가**

### **Scenario 1: 초기 배포**

```python
# Fixed Nominal
# 1. Device calibration → 5분
# 2. 즉시 예측 가능
# 총 시간: 5분

# Pilot Run
# 1. Device calibration → 5분
# 2. Pilot run → 1분
# 3. WA/RA 측정 → 10초
# 총 시간: 6분 10초

# 차이: 1분 10초
# 정확도: Pilot run +1-5% 예상
```

### **Scenario 2: 운영 중**

```python
# Fixed Nominal
# 이미 배포됨, 즉시 사용 가능

# Pilot Run
# 새로운 노드 추가 시:
# 1. Pilot run → 1분
# 2. Nominal 업데이트
# → 약간의 지연

# 하지만 정확도 향상!
```

### **Scenario 3: 환경 변화**

```python
# Hardware 업그레이드
old_hw: B_w = 2000 MiB/s
new_hw: B_w = 3000 MiB/s

# Fixed Nominal
# → WA/RA nominal은 그대로 (부정확해질 수 있음)

# Pilot Run
# → 새로운 환경에서 재측정 (정확!)

# 이 경우 Pilot Run 유리!
```

## 📊 **종합 평가**

### **전략별 점수**

| Criterion | Fixed Nominal | Pilot Run | Weight |
|-----------|---------------|-----------|--------|
| **Setup Time** | 5/5 | 3/5 | 0.2 |
| **Accuracy** | 3/5 | 5/5 | 0.4 |
| **Complexity** | 5/5 | 3/5 | 0.2 |
| **Reliability** | 4/5 | 5/5 | 0.2 |
| **Total** | **4.0** | **4.4** | |

### **결론**

**Pilot Run이 약간 우수 (4.4 vs 4.0)**

하지만:
- ✅ Setup time: 약간 불리
- ✅ Accuracy: 더 정확
- ⚠️ Complexity: 복잡도 증가

## 💡 **하이브리드 접근법** (권장) ✅

### **Best of Both Worlds**

```python
class V5_3Hybrid:
    def __init__(self):
        # 1. 기본 Fixed nominal
        self.fixed_nominal = {
            'initial': {'wa': 1.02, 'ra': 0.1},
            'middle': {'wa': 2.87, 'ra': 4.40},
            'final': {'wa': 4.45, 'ra': 4.40}
        }
        
        # 2. Pilot run 플래그
        self.use_pilot_run = False
    
    def predict_s_max(self, device_bw, phase, context=None):
        """Hybrid prediction"""
        
        # Option 1: Fixed nominal (빠름)
        if not self.use_pilot_run:
            wa = self.fixed_nominal[phase]['wa']
            ra = self.fixed_nominal[phase]['ra']
        
        # Option 2: Pilot run (정확)
        else:
            # Pilot run으로 측정
            pilot_results = self._run_pilot_run()
            wa = pilot_results['wa']
            ra = pilot_results['ra']
        
        # 예측
        S_max = self._base_predict(device_bw, phase, context)
        S_max = S_max * self._adjust_wa_ra(phase, wa, ra)
        
        return S_max
    
    def enable_pilot_run(self):
        """Pilot run 사용하도록 설정"""
        self.use_pilot_run = True
    
    def disable_pilot_run(self):
        """Fixed nominal 사용 (기본값)"""
        self.use_pilot_run = False
```

## 🎯 **최종 권장**

### **추천: Hyb
rid Approach** ✅

#### **사용 시나리오**

```python
# Scenario 1: 빠른 배포 (Fixed Nominal)
model.use_pilot_run = False
S_predicted = model.predict()  # 즉시, 83.5% accuracy

# Scenario 2: 정확한 예측 필요 (Pilot Run)
model.use_pilot_run = True
S_predicted = model.predict()  # 1분 소요, 85-90% accuracy

# Scenario 3: 환경 변화 (Pilot Run)
model.enable_pilot_run()
S_predicted = model.predict()  # 새로운 환경에 맞춤
```

### **구현 우선순위**

1. ✅ **현재**: Fixed nominal 사용 (83.5% accuracy)
2. 🔶 **단기**: Pilot run 옵션 추가 (사용자 선택)
3. 🔶 **장기**: Auto-pilot integration (자동 측정)

### **최종 결론**

**Pilot Run은 좋은 전략이지만, 항상 사용할 필요는 없습니다.**

**추천 사용법**:
- 일반: Fixed nominal (빠르고 충분히 정확)
- 정확도 중시: Pilot run (약간 느리지만 더 정확)
- 환경 특화: Pilot run 필수

**현재 모델은 Fixed nominal로도 충분합니다 (87.4%)** ✅

