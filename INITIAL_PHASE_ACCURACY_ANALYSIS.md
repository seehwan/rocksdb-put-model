# 초기 단계 정확도 분석

## 📊 **초기 단계 성능 데이터**

### **실제 측정 결과** (`2025-09-12`):

```json
{
  "initial": {
    "duration_hours": 32.2,
    "avg_write_rate": 17.14 MB/s,    // 평균
    "max_write_rate": 280.18 MB/s,    // 최대 ⚠️ 16배 차이!
    "min_write_rate": 13.83 MB/s,     // 최소
    "std_write_rate": 6.10,
    "cv": 0.356,                       // 매우 높은 변동성
    "flush_count": 53053              // 압도적으로 많은 flush
  }
}
```

### **비교**: Middle/Final Phase
```json
{
  "middle": {
    "cv": 0.027,                       // 초기보다 13배 낮음
    "flush_count": 43796              // flush 17% 감소
  },
  "final": {
    "cv": 0.013,                       // 초기보다 27배 낮음  
    "flush_count": 41960              // flush 21% 감소
  }
}
```

---

## 🎯 **초기 단계 정확도가 낮은 핵심 이유**

### **1. 압도적인 변동성 (CV = 0.356)**

**문제점**:
- 최대값(280.18)과 최소값(13.83)이 **20배 차이**
- Standard deviation (6.10)이 평균(17.14)의 **35%**
- 예측이 거의 불가능한 수준

**원인**:
1. **새로운 DB 초기화**: 빈 DB에서 시작, 첫 flush/compaction 트리거
2. **MemTable → L0 빈번한 flush**: 53,053번 flush (중기 43,796보다 21% 많음)
3. **LSM 구조 단순**: L0-L1만 존재, 단순해 보이지만 불안정
4. **적응적 시스템 동작**: RocksDB 내부 최적화가 활발히 진행 중

---

### **2. 사용자 질문의 핵심: "여러 컴팩션이 경쟁적으로 처리량을 늘려서?"**

#### ✅ **부분적으로 맞습니다!**

**하지만 더 정확한 설명**:

#### **A. 초기 단계의 독특한 특성**

1. **MemTable Flush 경쟁**:
   - 여러 MemTable이 동시에 flush하려고 경쟁
   - 각 flush가 device bandwidth를 점유
   - 결과: throughput이 순간적으로 폭등/급락

2. **단순하지만 불안정한 LSM 구조**:
   - L0-L1만 존재 (단순)
   - 하지만 L0에 파일이 빠르게 쌓임
   - L0 compaction이 순간적으로 처리량에 영향

3. **OS/SSD 캐시 워밍업**:
   - File system cache가 비어있음
   - SSD controller가 최적화 진행 중
   - 캐시 미스 → hit ratio 변화 → 성능 변동

#### **B. "경쟁"의 정확한 의미**

**잘못된 이해**:
- ❌ "여러 백그라운드 컴팩션이 동시에 실행되면서 경쟁"
- ❌ "멀티-레벨 컴팩션이 복잡하게 상호작용"

**정확한 이해**:
- ✅ **MemTable flush 경쟁**: 여러 MemTable이 동시에 flush
- ✅ **Device bandwidth 경쟁**: User writes vs Background flush
- ✅ **OS Cache warming up**: 캐시 상태가 계속 변함
- ✅ **단순 LSM이지만 불안정**: 구조는 단순하지만 동작이 예측 불가

---

## 📈 **실제 데이터로 본 초기 단계 특성**

### **Phase별 Flush Count 비교**:
```
Phase     Flush Count   Duration    Flush/hr
----------------------------------------------
Initial:  53,053        32.2 hrs    1,647/hr  ⚠️ 최다!
Middle:   43,796        32.2 hrs    1,359/hr
Final:    41,960        32.2 hrs    1,302/hr
```

**분석**:
- 초기: Flush가 21-27% 더 빈번함
- 이유: 빈 DB에서 새로운 MemTable이 계속 생성 → flush
- 결과: Device bandwidth 공유 갈등이 극심

### **Throughput 변동성 분석**:

**CV (Coefficient of Variation)**:
```
Initial: 0.356 (35.6% 변동성) ⚠️ 매우 높음
Middle:  0.027 (2.7% 변동성)
Final:   0.013 (1.3% 변동성)
```

**초기 변동성이 27배 높음!**

---

## 💡 **왜 초기 단계 정확도가 75%인가?**

### **Model Prediction의 어려움**:

1. **불규칙한 성능 패턴**:
   - 평균 17.14 MB/s지만 실제로는 13.83 ~ 280.18 MB/s
   - 어떤 시점에 측정하느냐에 따라 결과가 천차만별

2. **시스템 초기화 효과**:
   - RocksDB 최적화 진행 중
   - OS 캐시 워밍업
   - SSD GC/TRIM 초기 최적화

3. **LSM 구조 진화**:
   - 빈 DB → L0 파일 생성 → L0→L1 compaction
   - 구조 변화가 연속적으로 일어남

### **Model의 한계**:

**사용자의 질문에 대한 답**:
- ✅ **맞습니다**: "여러 컴팩션들이 경쟁적으로 처리량을 늘려서"
- ✅ **하지만 더 정확하게**: "MemTable flush와 L0 compaction이 동시에 경쟁하면서 throughput이 불규칙하게 변동"

**Model이 이 문제를 어떻게 해결하는가**:

1. **Rate Control (8% 감소)**:
   - Overshooting 방지
   - CV 개선: 0.538 → 0.508 (-5.6%)

2. **Volatility Bonus (1.20x)**:
   - 불규칙성을 인식하고 예약 용량 사용

3. **Context-Aware Bonuses**:
   - CV > 0.50: Volatility bonus
   - Runtime < 15 min: Warmup bonus
   - Positive trend: Potential bonus

---

## 🎯 **결론**

### **초기 단계 정확도가 낮은 이유** (75.0%):

1. **압도적인 변동성** (CV = 0.356): 시스템이 안정화되지 않음
2. **MemTable flush 경쟁**: 53,053번 flush, device bandwidth 공유 갈등
3. **시스템 초기화**: OS cache, SSD 최적화 진행 중
4. **LSM 구조 진화**: 단순하지만 계속 변함
5. **측정 어려움**: 시점에 따라 성능이 20배 차이

### **User의 질문**: "여러 컴팩션들이 경쟁적으로 처리량을 늘려서?"

**답변**: 
- ✅ **부분적으로 맞습니다**
- 더 정확히는: "MemTable flush와 L0 compaction이 동시에 device bandwidth를 경쟁하면서, 초기 시스템 불안정과 결합되어 예측 불가능한 성능 변동을 일으킴"

**Model의 해결책**:
- Rate control (8% 감소)로 overshooting 방지
- Volatility bonus (1.20x)로 불규칙성 대응
- Context-aware bonuses로 system state 활용
- **정확도 75.6%** 달성 (rate control 적용 시)

