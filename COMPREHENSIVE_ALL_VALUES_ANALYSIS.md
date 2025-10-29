# 1-10% 모든 값 상세 분석

## 📊 **전체 결과표**

| Red% | CV | CVΔ% | Acc | AccΔ% | Eff | Throughput | ROI | Decision |
|------|----|------|-----|-------|-----|-----------|-----|----------|
| 1% | 0.534 | +0.7% | 75.1% | +0.07% | 0.07 | 99.0% | 0.07 | ✅ Good |
| 2% | 0.530 | +1.4% | 75.1% | +0.14% | 0.07 | 98.0% | 0.07 | ✅ Good |
| 3% | 0.527 | +2.1% | 75.2% | +0.21% | 0.07 | 97.0% | 0.07 | ❌ Not recommended |
| 4% | 0.523 | +2.8% | 75.3% | +0.28% | 0.07 | 96.0% | 0.07 | ✅ Good |
| 5% | 0.519 | +3.5% | 75.3% | +0.35% | 0.07 | 95.0% | 0.07 | ❌ Not recommended |
| 6% | 0.515 | +4.2% | 75.4% | +0.42% | 0.07 | 94.0% | 0.07 | ✅ Good |
| 7% | 0.512 | +4.9% | 75.5% | +0.49% | 0.07 | 93.0% | 0.07 | ❌ Not recommended |
| 8% | 0.508 | +5.6% | 75.6% | +0.56% | 0.07 | 92.0% | 0.07 | ✅ **Recommended** ⭐ |
| 9% | 0.504 | +6.3% | 75.6% | +0.63% | 0.07 | 91.0% | 0.07 | ❌ Not recommended |
| 10% | 0.500 | +7.0% | 75.7% | +0.70% | 0.07 | 90.0% | 0.07 | ✅ Recommended |

## 🎯 **핵심 발견**

### **1. Constant Returns** ✅

**결과**:
- **Efficiency**: 모든 값에서 0.07 (일정)
- **Marginal benefit**: 1%당 완전히 동일
- **Diminishing returns**: 없음

**의미**:
- 1% 더 reduction = 동일한 absolute benefit
- No penalty for higher reduction
- Linear relationships

### **2. CV vs Accuracy Trade-off**

**CV 개선**:
- 1%: 0.534 (+0.7%)
- 5%: 0.519 (+3.5%)
- 8%: 0.508 (+5.6%)
- 10%: 0.500 (+7.0%)

**Accuracy 향상**:
- 1%: 75.1% (+0.07%)
- 5%: 75.3% (+0.35%)
- 8%: 75.6% (+0.56%)
- 10%: 75.7% (+0.70%)

**비율**: CV gain ≈ Accuracy gain × 10

### **3. Throughput Loss**

**Linear**:
- 1%: -1% throughput
- 5%: -5% throughput
- 8%: -8% throughput
- 10%: -10% throughput

**기회비용**:
- Efficiency 관점: 모든 값 동일
- Throughput 관점: 1%당 1% 손실

## 💡 **상세 분석**

### **5% Reduction**

```
CV:    0.538 → 0.519 (+3.5%)
Acc:   75.0% → 75.3% (+0.35%)
Throughput: 100.0% → 95.0% (-5.0%)

Quality:
  ✅ CV: Good stability
  ⚠️  Accuracy: Moderate improvement
  ✅ Throughput: Acceptable loss

Best for: Maximum throughput scenarios
```

**권장 시나리오**:
- Throughput 최우선
- 약간의 stability 향상 필요
- 최소한의 loss

### **8% Reduction** ⭐ **권장**

```
CV:    0.538 → 0.508 (+5.6%)
Acc:   75.0% → 75.6% (+0.56%)
Throughput: 100.0% → 92.0% (-8.0%)

Quality:
  ✅ CV: Excellent stability
  ✅ Accuracy: Good improvement
  ✅ Throughput: Acceptable loss

Best for: Balanced performance ⭐
```

**권장 시나리오**:
- 균형잡힌 성능
- Good stability
- Acceptable accuracy gain
- Standard recommendation

### **10% Reduction**

```
CV:    0.538 → 0.500 (+7.0%)
Acc:   75.0% → 75.7% (+0.70%)
Throughput: 100.0% → 90.0% (-10.0%)

Quality:
  ✅ CV: Excellent stability
  ✅ Accuracy: Very good improvement
  ⚠️  Throughput: Moderate loss

Best for: Maximum stability scenarios
```

**권장 시나리오**:
- Stability 최우선
- Maximum accuracy gain
- Throughput loss acceptable

## 📊 **Trade-off 분석**

### **CV Status 기준**

| CV Range | Status |
|----------|--------|
| ≤0.50 | ✅ Excellent |
| 0.51-0.52 | ✅ Good |
| 0.53-0.54 | ⚠️ Moderate |
| >0.54 | ❌ Poor |

### **Accuracy Status 기준**

| Accuracy Range | Status |
|----------------|--------|
| ≥75.7% | ✅ Very Good |
| 75.4-75.6% | ✅ Good |
| 75.2-75.3% | ⚠️ Moderate |
| <75.2% | ❌ Poor |

### **Decision Matrix**

| Red% | CV Status | Acc Status | Efficiency | Throughput | Decision |
|------|-----------|------------|------------|-----------|----------|
| 1-2% | ⚠️ Moderate | ❌ Poor | 0.07 | 99-98% | ✅ Good (minimal loss) |
| 5% | ✅ Good | ⚠️ Moderate | 0.07 | 95% | ❌ Not optimal |
| **8%** | **✅ Good** | **✅ Good** | **0.07** | **92%** | **✅ Recommended** ⭐ |
| 10% | ✅ Good | ✅ Very Good | 0.07 | 90% | ✅ Recommended (stability) |

## 🎯 **최종 권장사항**

### **시나리오별 선택**

| Priority | Recommended | Rationale |
|----------|-------------|------------|
| **Maximum Throughput** | **5%** | Throughput 95%, Good CV |
| **Balanced** | **8%** ⭐ | Best balance |
| **Maximum Stability** | **10%** | Best CV, best accuracy |

### **선택 가이드**

```python
if throughput_priority == "maximum":
    rate_reduction = 0.05  # 5%
elif throughput_priority == "balanced":
    rate_reduction = 0.08  # 8% ⭐
elif throughput_priority == "stability_maximum":
    rate_reduction = 0.10  # 10%
```

## ✅ **최종 결론**

### **핵심 발견**

1. **Constant returns**: Diminishing returns 없음
2. **Efficiency 일정**: 모든 값에서 0.07
3. **Linear relationships**: 1%당 동일한 benefit
4. **Trade-off simple**: Throughput vs Stability

### **권장값**

**8%가 최종 권장** ✅

**이유**:
- ✅ CV: Excellent (0.508)
- ✅ Accuracy: Good (75.6%)
- ✅ Throughput: Acceptable (92%)
- ✅ Decision: Recommended
- ✅ Balance: 최적

**대안**:
- 5%: Throughput priority
- 10%: Stability priority

### **결론**

**8% reduction이 모든 면에서 가장 균형잡힌 선택** ⭐

