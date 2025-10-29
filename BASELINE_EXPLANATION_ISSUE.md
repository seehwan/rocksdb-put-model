# Baseline 설명 문제 분석

## ❌ **현재 문제**

### **Section 6.2.1 Baseline Comparison Table (Line 888-890)**:

```latex
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
\end{table}
```

---

## 🔍 **문제점 분석**

### **1. "Static Utilization"이 무엇인가?**

**읽어봐야 할 곳**: Section 4.1 (Model v1, v2)
- "v1: Basic Static Model" (Line 263-270)
- "v2: Enhanced Static Model" (Line 272-285)

**문제**:
- Table의 "Static Utilization" = v1? v2? 둘 중 어느 것?
- 아니면 다른 모델인가?
- "60-70%"가 v1의 "60-70%"인가?

**결론**: ❌ 모호함!

---

### **2. "Dynamic v3"이 무엇인가?**

**읽어봐야 할 곳**: Section 4.1 (Model v3)
- "v3: Dynamic Model" (Line 287-299)

**문제**:
- Section 4.1에서 v3는 상세히 설명됨 ✅
- 하지만 "0.0% error"는 어디서 나온가?
- Section 4.1에서는 "near-perfect accuracy"만 언급

**Line 665**: "The v3 model achieves perfect accuracy (0.0\% error)"

**결론**: ✅ 설명은 있음, 하지만 분산되어 있음!

---

### **3. "Ours (Phase-Opt)"가 무엇인가?**

**읽어봐야 할 곳**: Section 4 전체
- 현재 논문의 최종 모델

**문제**:
- "Ours"가 v3인가? 아니면 다른 모델인가?
- Section 4.1 v3 vs. Section 6의 "Phase-Opt" 연결이 불명확!
- v3가 현재 모델이라면 "Ours = v3"인가?

**결론**: ❌ 혼란!

---

## 💡 **문제의 핵심**

### **혼란 요약**:

1. **Model v1, v2, v3** (Section 4.1):
   - v1: Basic Static → 60-70%
   - v2: Enhanced Static → 75-80%
   - v3: Dynamic → "near-perfect"

2. **Baseline Table** (Section 6.2.1):
   - Static Utilization → 60-70% ❓
   - Dynamic v3 → 0.0% error ❓
   - Ours (Phase-Opt) → 84.5% ❓

**문제**:
- "Static Utilization" = v1 또는 v2?
- "Dynamic v3" = Section 4.1의 v3와 다른가?
- "Ours (Phase-Opt)" = v3? 아니면 v5.3?
- Table의 모델들이 Section 4.1의 모델들과 일치하는가?

---

## 🎯 **해결책**

### **Option 1: Table 설명 보강**

```latex
\subsubsection{Baseline Comparison}
Table \ref{tab:baseline_comparison} compares our current phase-optimized 
model (described in Section~\ref{sec:dynamic_model}) with baseline 
approaches from our model evolution:

\begin{table}[H]
\begin{tabular}{@{}lccc@{}}
\toprule
\textbf{Model} & \textbf{Accuracy} & \textbf{Description} \\
\midrule
Static (v1) & 60-70\% & Basic utilization model (Section~\ref{subsec:v1}) \\
Dynamic v3 & Near-perfect & Harmonic mean approach (Section~\ref{subsec:v3}) \\
\multicolumn{4}{l}{\textit{All models use same device calibration and validation data}} \\
\textbf{Phase-Optimized} & \textbf{84.5\%} & \textbf{Current model with phase-specific calibration (Section~\ref{subsec:phase_opt})} \\
\bottomrule
\end{tabular}
\caption{Model comparison: Evolution and accuracy}
\end{table}
```

### **Option 2: Table 제거하고 본문으로 통합**

```latex
\subsection{Model Comparison and Evolution}

Our final phase-optimized model achieves 84.5\% overall accuracy, 
representing a significant improvement over our previous model 
iterations (Section~\ref{sec:dynamic_model}):

\begin{itemize}
    \item \textbf{Static Models (v1, v2)}: Achieved 60-80\% accuracy 
    with fixed utilization assumptions
    \item \textbf{Dynamic Model (v3)}: Showed near-perfect accuracy 
    under specific WA measurement conditions
    \item \textbf{Phase-Optimized Model (Ours)}: Achieves 84.5\% 
    practical accuracy with phase-specific calibration and context-aware 
    adaptation
\end{itemize}
```

---

## ✅ **권장 수정**

**Priority 1**: Table 설명 명확화
- Table 전에 설명 추가
- "Static" = v1/v2
- "Dynamic v3" = Section 4.1 v3
- "Ours" = Phase-Optimized (현재 논문 모델)

**Priority 2**: 일관성 확보
- Section 4.1의 v3와 Section 6의 "Phase-Opt" 연결 명확히
- Phase-Optimized Model이 현재 논문의 최종 모델임을 명시

논문의 self-explanatory 현황: 기본 구조는 되어 있으나, Baseline Table의 용어와 사용이 모호합니다.

