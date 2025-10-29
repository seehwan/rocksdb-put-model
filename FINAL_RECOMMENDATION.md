# 최종 권장 사항

## 📊 최종 검증 결과

### 정확도 순위

| Model | Accuracy | Improvement | Complexity |
|-------|----------|-------------|------------|
| **Original V5.3** | 84.5% | Base | Low |
| **V5.3 + WA/RA** ✅ | **87.4%** | **+2.9%** | Medium |
| V5.3 + WA/RA + Pending | 88.2% | +3.7% | High |

### 🎯 **권장 사항: WA/RA만 사용** ✅

#### 이유

1. **효과 대비 복잡도**
   - WA/RA만: +2.9% 개선 (Medium complexity)
   - Pending 추가: +0.8% 추가 개선 (High complexity)
   - **ROI가 낮음**

2. **검증 결과**
   - WA/RA: 모든 시나리오에서 효과적
   - Pending: High pressure 시에만 효과 (5 cases 중 2 cases)
   
3. **구현 복잡도**
   - WA/RA: Phase-specific nominal values만 필요
   - Pending: Phase-specific thresholds, tuning 필요

## 📋 최종 구현

### **채택할 모델: V5.3 Enhanced (WA/RA only)**

```python
# Core formula
S_max = S_base × f_WA(wa, phase) × f_RA(ra, phase)

# Phase-specific adjustment
if wa/ra in optimal_range:
    f = 1.0  # No adjustment
else:
    f = 1.0 - deviation × sensitivity  # Penalty
```

### **효과**

- **평균 정확도**: 87.4% (Original: 84.5%, +2.9%)
- **Best case**: 96.7% (Final, High WA)
- **Phase balance**: Initial 85.5%, Middle 92.3%, Final 91.5%

### **Phase별 Sensitivity**

| Phase | WA Sensitivity | RA Sensitivity | Optimal WA Range | Optimal RA Range |
|-------|---------------|----------------|------------------|------------------|
| Initial | 0.12 | 0.08 | (1.0, 1.5) | (0.05, 0.3) |
| Middle | 0.06 | 0.05 | (2.0, 3.0) | (0.5, 1.0) |
| Final | 0.08 | 0.06 | (3.0, 4.0) | (0.7, 1.0) |

## ✅ **결론**

### **V5.3 Enhanced (WA/RA only) 사용 권장**

**이유**:
1. ✅ 충분한 개선 (+2.9%)
2. ✅ 구현 간단 (Phase-specific sensitivity만)
3. ✅ 검증 완료 (모든 시나리오)
4. ✅ 효과 대비 복잡도 우수

**Pending은 제외**:
- ❌ 추가 개선 작음 (+0.8%)
- ❌ 복잡도 증가
- ❌ Phase-specific tuning 필요
- ❌ ROI 낮음

## 📝 **논문에 포함할 내용**

### **WA/RA Adjustment 공식**

```latex
\subsubsection{Amplification-Based Utilization Adjustment}

For scenarios where measured WA/RA deviate from phase-specific optimal ranges, 
we apply penalty factors:

\begin{equation}
S_{\max} = S_{\text{base}} \times f_{\text{WA}}(WA) \times f_{\text{RA}}(RA)
\end{equation}

where $f_{\text{WA}}$ and $f_{\text{RA}}$ are phase-specific penalty factors:

\begin{align}
f_{\text{WA}}(WA) &= \begin{cases}
1.0 & WA_{\min} \leq WA \leq WA_{\max} \\
\max\left(0.88, 1 - \alpha_{\text{WA}} \cdot (WA - WA_{\max})\right) & WA > WA_{\max}
\end{cases} \\
f_{\text{RA}}(RA) &= \begin{cases}
1.0 & RA_{\min} \leq RA \leq RA_{\max} \\
\max\left(0.88, 1 - \alpha_{\text{RA}} \cdot (RA - RA_{\max})\right) & RA > RA_{\max}
\end{cases}
\end{align}

Phase-specific sensitivity coefficients $\alpha_{\text{WA}}$ and $\alpha_{\text{RA}}$ 
ensure conservative penalty application, with validation demonstrating 87.4\% 
overall accuracy across all operational phases.
```

## 🎯 **최종 의사결정**

### ✅ **채택: WA/RA Adjustment만**

**모델**: `V5_3Enhanced` (model/v5_3_wa_ra_enhanced.py)

**Accuracy**:
- Overall: 87.4%
- Initial: 85.5%
- Middle: 92.3%
- Final: 91.5%

**구현**:
- Phase-specific WA/RA adjustment
- Penalty only (no bonus)
- Sensitivity-based deviation handling

**논문**:
- Section 4.2.4 추가
- Validation: 5 test cases
- Results: All phases >85%

### ❌ **제외: Pending Compaction Bytes**

**이유**:
- 추가 개선 작음 (+0.8%)
- 복잡도 증가
- ROI 낮음

