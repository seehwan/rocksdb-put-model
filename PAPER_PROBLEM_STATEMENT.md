# 논문이 풀려고 하는 문제 정리

**분석 일시**: 2025-10-29  
**출처**: `rocksdb_put_model_paper.tex`

---

## 🎯 핵심 문제 (Core Problem)

### **1줄 요약**
> **"RocksDB의 time-varying write 성능을 예측하고, 안정적으로 write 성능을 낼 수 있는 rate (S_max)를 찾는 문제"**

---

## 📋 문제의 구성 요소

### **메인 문제 (Main Problem)**

**위치**: Abstract (Line 48), Introduction (Line 55, 57)

**진술**:
```
"existing models fail to capture time-varying performance characteristics"
"existing performance models often fail to capture the complex interactions 
between various system components, leading to inaccurate predictions and 
suboptimal configurations"
```

**의미**:
- 기존 모델들이 **부정확한 예측**을 함
- 결과적으로 **최적의 설정을 찾지 못함**

---

### **구체적 도전과제 1: Time-Varying Characteristics**

**위치**: Introduction Line 57

**진술**:
```
"First, the dynamic nature of compaction processes creates time-varying 
performance characteristics that are difficult to predict using static models"
```

**의미**:
- **문제**: Compaction 과정이 동적이어서 성능이 시간에 따라 변함
- **기존 방법의 한계**: Static models은 이를 예측하지 못함
- **증거**: 
  - Initial phase: CV=0.714 (높은 변동성)
  - Middle phase: CV=0.516
  - Final phase: CV=0.474
  - Phase boundaries: 9.81h, 42.0h

**핵심 질문**:
- "언제 성능이 어떻게 변할 것인가?"
- "각 phase에서 얼마의 성능을 기대할 수 있는가?"

---

### **구체적 도전과제 2: Non-linear Dependencies**

**위치**: Introduction Line 57

**진술**:
```
"Second, the interaction between write amplification, compression ratios, 
and device bandwidth constraints creates non-linear dependencies that are 
not well understood"
```

**의미**:
- **문제**: WA, CR, Bandwidth가 서로 상호작용하며 **비선형 관계**를 만듦
- **기존 이해의 한계**: 이런 상호작용이 잘 이해되지 않음
- **증거**:
  - WA와 CR의 상호작용
  - Device bandwidth 제약
  - Mixed I/O에서 25-53% 성능 저하 관측

**핵심 질문**:
- "WA가 높아지면 bandwidth utilization이 어떻게 변하는가?"
- "CR과 bandwidth의 관계는?"
- "이런 상호작용을 어떻게 모델링할 것인가?"

---

### **구체적 도전과제 3: Stall and Background Process Impact**

**위치**: Introduction Line 57

**진술**:
```
"Third, the impact of stalls and background processes on foreground 
performance introduces additional complexity that existing models often overlook"
```

**의미**:
- **문제**: Stall과 background process가 foreground 성능에 큰 영향을 미침
- **기존 모델의 한계**: 이런 영향이 간과됨
- **증거**:
  - Stall percentage: 45.31% (거의 절반 시간!)
  - Background compaction 활동
  - Thread contention

**핵심 질문**:
- "Stall이 얼마나 성능을 저하시키는가?"
- "Background process가 foreground에 어떤 영향을 미치는가?"
- "이를 어떻게 예측 모델에 반영할 것인가?"

---

### **구체적 도전과제 4: Complex Interactions**

**위치**: Introduction Line 55

**진술**:
```
"existing performance models often fail to capture the complex interactions 
between various system components"
```

**의미**:
- **문제**: 시스템 컴포넌트들 간의 복잡한 상호작용을 포착하지 못함
- **결과**: 부정확한 예측, 최적이 아닌 설정

---

## 🎯 왜 이 문제가 중요한가?

### **실용적 필요성** (Line 55)

```
"Understanding and predicting RocksDB's write performance is essential for:
- system optimization
- capacity planning  
- performance tuning"
```

### **실제 영향**

**부정확한 예측의 결과**:
- ❌ 시스템 용량을 과소 또는 과대 산정
- ❌ 최적이 아닌 설정으로 운영
- ❌ 성능 저하나 리소스 낭비

---

## 📊 문제의 본질

### **핵심 문제 정의**

**질문**:
> "RocksDB에서 안정적으로 처리할 수 있는 최대 put rate (S_max)는 얼마인가?"
> "그리고 이 값이 시간에 따라 어떻게 변하는가?"

**현실적 필요성**:
- Production 환경에서 얼마의 put rate를 기대할 수 있는가?
- Capacity planning: 얼마의 시스템이 필요한가?
- Performance tuning: 최적의 설정은 무엇인가?

### **기존 모델의 실패**

**왜 기존 모델이 실패하는가?**

1. **Static assumption**
   - 성능이 시간에 따라 변한다는 것을 고려하지 않음
   - Phase별 특성을 무시

2. **Linear thinking**
   - WA, CR, bandwidth를 독립적으로 고려
   - 상호작용을 단순화

3. **Incomplete factors**
   - Stall, background process를 간과
   - Complex interactions 무시

---

## 🔍 문제의 수준 (Level of Problem)

### **1. 이론적 문제 (Theoretical Problem)**
- Time-varying performance를 어떻게 모델링하는가?
- Non-linear dependencies를 어떻게 포착하는가?

### **2. 실용적 문제 (Practical Problem)**
- Production 환경에서 정확한 예측이 필요
- Capacity planning에 활용 가능해야 함

### **3. 방법론적 문제 (Methodological Problem)**
- 어떤 접근법이 time-varying characteristics를 포착할 수 있는가?
- Phase detection을 어떻게 할 것인가?

---

## 💡 문제 해결의 목표

### **논문이 달성하고자 하는 것**

1. **정확한 예측**
   - Phase별로 다른 성능 예측
   - Time-varying characteristics 포착

2. **포괄적 모델링**
   - WA, CR, bandwidth 상호작용 모델링
   - Stall, background process 영향 반영

3. **실용적 가치**
   - Production deployment에 활용 가능
   - Capacity planning 도구 제공

---

## 📝 문제 진술의 명확성 평가

### ✅ **강점**

1. **구체적 증거 제시**
   - CV 값 (0.714, 0.516, 0.474)
   - Phase boundaries (9.81h, 42.0h)
   - Stall percentage (45.31%)

2. **3가지 구체적 도전과제**
   - Time-varying
   - Non-linear dependencies
   - Stall/background impact

3. **실용적 필요성 명시**
   - System optimization
   - Capacity planning
   - Performance tuning

### ⚠️ **약점**

1. **"Existing models"이 구체적이지 않음**
   - 어떤 모델들이 실패하는가?
   - Related Work에서 구체적으로 언급 필요

2. **"Non-linear dependencies"의 의미 불명확**
   - 어떤 종류의 non-linearity인가?
   - 구체적 예시 필요

3. **문제의 우선순위 불명확**
   - 3가지 도전과제 중 어느 것이 가장 중요한가?
   - 또는 모두 동등하게 중요한가?

---

## 🎯 최종 문제 진술 (Refined Problem Statement)

### **핵심 질문**:
> **"RocksDB에서 시간에 따라 변하는 write 성능을 예측하고, 안정적으로 처리할 수 있는 maximum sustainable put rate (S_max)를 찾는 문제"**

### **구체화된 질문들**:

1. **Put Rate 예측 질문**:
   - 최대 sustainable put rate (S_max)는 얼마인가?
   - 이 값이 시간에 따라 어떻게 변하는가? (time-varying)
   - 각 phase에서 예상되는 S_max는 무엇인가?

2. **안정성 질문**:
   - 안정적으로 write 성능을 낼 수 있는 rate는 얼마인가?
   - Phase별로 안정적인 rate가 다른가?
   - Production 환경에서 안전하게 운영할 수 있는 rate는?

3. **Time-Varying 예측 질문**:
   - RocksDB 성능이 시간에 따라 어떻게 변하는가?
   - 언제 phase transition이 일어나는가?
   - 각 phase의 특성은 무엇인가?

---

## 📊 문제의 중요성

### **학술적 중요성**
- LSM-tree 성능 모델링의 새로운 방향 제시
- Time-varying characteristics를 포착하는 방법론

### **실용적 중요성**
- Production 환경에서의 실용성
- Capacity planning의 정확성 향상

---

## ✅ 최종 정리

**논문이 풀려고 하는 문제**:

### **1줄 요약**:
> **"RocksDB의 time-varying write 성능을 예측하고, 안정적으로 write 성능을 낼 수 있는 rate (S_max)를 찾는 문제"**

### **상세 설명**:

**핵심 문제**:
1. **Time-varying put rate 예측**: 
   - Write 성능이 시간에 따라 변함 (Initial/Middle/Final phases)
   - Static models은 이를 예측하지 못함
   
2. **안정적인 S_max 찾기**:
   - Maximum sustainable put rate를 phase별로 찾아야 함
   - Production에서 안전하게 운영할 수 있는 rate 결정 필요

**주요 도전과제** (문제를 해결하기 위해 극복해야 할 것들):
1. **Time-varying characteristics**: Static models이 동적 성능 변화를 포착하지 못함
2. **Non-linear dependencies**: WA, CR, bandwidth의 복잡한 상호작용
3. **Stall/background impact**: Foreground 성능에 미치는 영향
4. **Complex interactions**: 시스템 컴포넌트들 간의 복잡한 상호작용

### **해결 목표**:
- **Phase-optimized S_max prediction**: Phase별로 다른 S_max 예측
- **Stable put rate recommendation**: 안정적으로 운영할 수 있는 rate 제시
- **Context-aware adaptation**: 시스템 상태에 따라 동적 조정
- **Production deployment guidance**: 실제 운영을 위한 권장값 제공

---

**문제 정의의 명확성**: **8.5/10**

- ✅ 구체적 도전과제 3가지 명시
- ✅ 실용적 필요성 제시
- ⚠️ "Existing models" 구체화 필요
- ⚠️ Problem의 우선순위 불명확

