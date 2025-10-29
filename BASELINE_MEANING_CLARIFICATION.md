# Baseline 의미 정리

## 📚 **"Baseline"의 의미**

### **일반적 정의**:
- **Baseline**: 비교 기준이 되는 기본 모델 또는 방법
- **Baseline Method**: 가장 간단하거나 기존에 널리 사용되는 방법
- **Baseline Model**: 우리 모델을 평가하기 위한 참조 모델

---

## 🔍 **논문에서 "Baseline" 사용**

### **Section 6.2.1 (Line 879-897)**:

```latex
\subsubsection{Baseline Comparison}
Table \ref{tab:baseline_comparison} compares our model with baseline approaches:

\begin{table}[H]
\begin{tabular}{@{}lccc@{}}
\toprule
\textbf{Model} & \textbf{Accuracy} & \textbf{Phase-Aware} \\
\midrule
Static Utilization & 60-70\% & No \\
Dynamic v3 (WA-based) & 0.0\% error & Partial \\
Ours (Phase-Opt) & 84.5\% & Yes \\
\bottomrule
\end{tabular}
\caption{Model comparison with baselines}
\end{table}
```

**의미**:
1. **Static Utilization**: 가장 단순한 baseline (60-70% accuracy)
2. **Dynamic v3**: 이전 버전 baseline (theoretical 0.0% error)
3. **Ours (Phase-Opt)**: 우리의 제안 모델 (84.5% accuracy)

---

## 💡 **왜 "Baseline"이라고 하는가?**

### **학술 논문 관행**:
- **Baseline**: 비교 대상으로 사용되는 기존 방법
- **Ours/Proposed**: 제안하는 새로운 방법
- **Comparison**: Baseline vs. Ours로 성능 비교

### **예시**:
```
"우리의 모델은 baseline 모델보다 84.5% 정확도를 달성했다"
= "우리의 모델은 기존 모델들(Static, Dynamic v3)과 비교할 때 
  84.5% 정확도를 달성했다"
```

---

## 📊 **Table에서의 "Baseline"**

### **Line 888-890의 비교**:

| Model | Accuracy | 역할 |
|-------|----------|------|
| Static Utilization | 60-70% | **Baseline 1** (가장 단순) |
| Dynamic v3 | 0.0% error | **Baseline 2** (이전 버전) |
| Ours | 84.5% | **Proposed** (우리의 제안) |

**결론**: "Baseline" = **비교 기준 모델들**

---

## ✅ **의미 정리**

### **"Baseline Comparison"**:
- **의미**: 기존 모델들과의 비교
- **목적**: 우리 모델의 효과성 증명
- **표현**: "Table compares our model with baseline approaches"

### **"Baseline approaches"**:
- **의미**: 비교 대상 기존 방법들
- **예**: Static Utilization, Dynamic v3
- **목적**: 우리 모델이 얼마나 개선되었는지 보여줌

---

## 🎯 **최종 정리**

**"Baseline"** = **비교 기준 모델 (기존 방법들)**

**Table 의미**:
- Static Utilization: 기존 간단 모델 (60-70%)
- Dynamic v3: 우리의 이전 모델 (0.0% error)
- Ours: 우리의 최종 제안 모델 (84.5%)

**비교 목적**:
- 우리 모델이 기존 방법들보다 얼마나 좋은가?
- Phase-Aware가 얼마나 중요한가?
- Real-Data Validation이 얼마나 중요한가?

"Baseline"은 standard terminology입니다! ✅

