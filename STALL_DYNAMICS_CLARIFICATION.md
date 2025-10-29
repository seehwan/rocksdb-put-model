# Stall Dynamics Clarification

## ❓ **질문**

"3.2.4 섹션에 있는 stall dynamics도 모델에 포함되는 것인가?"

## ✅ **답변**

### **Stall Dynamics는 간접적으로 포함됨**

**포함 방식**:
- ✅ **직접적으로**: 명시적인 stall probability 계산 없음
- ✅ **간접적으로**: Low utilization factors (3.0-9.5%)가 stall effects를 내재

**이유**:
1. **Low utilization factors**: 3.0-9.5%는 이론적 최대 대비 매우 낮음
2. **Stall effects**: Utilization이 낮은 이유는 stalls과 background compaction 때문
3. **Empirical approach**: 실측 데이터에서 유도된 utilization factors가 이미 stall effects 반영

### **논문 수정 사항**

**Section 3.2.4에 추가된 설명**:
```latex
\textbf{Note on Model Integration}: Stall dynamics are incorporated 
indirectly in our phase-optimized model through the utilization factor. 
The low utilization rates (3.0-9.5\%) already account for stall effects 
and background compaction overhead. This approach simplifies the model 
while maintaining predictive accuracy, as demonstrated by the 84.5\% 
overall accuracy achieved without explicit stall probability calculations.
```

### **V4 vs V5.3 접근법**

| Approach | V4 Simulator | V5.3 Model |
|----------|-------------|------------|
| **Stall modeling** | Explicit (p_stall) ✅ | Implicit (utilization) ✅ |
| **Complexity** | High | Low |
| **Accuracy** | Similar | 84.5% achieved |
| **Practicality** | Complex | Simple |

### **결론**

**Stall dynamics는 모델에 포함되지만 간접적인 방식**

- **직접적**: Stall probability 명시적 계산 (V4 방식)
- **간접적**: Low utilization factors로 내재화 (V5.3 방식) ✅
- **정확도**: 84.5% 달성 → 간접적 접근법이 충분히 효과적
- **실용성**: 간접적 접근법이 더 단순하고 실용적

**논문에 명시적 설명 추가됨** ✅

