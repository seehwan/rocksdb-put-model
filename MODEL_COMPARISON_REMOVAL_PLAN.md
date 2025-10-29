# Model Comparison 섹션 제거 계획

## 🎯 **핵심 문제**

**현재 상황**:
- 논문은 **Phase-Optimized Model 하나**만 설명해야 함
- v1-v3는 **옛날 우리 모델** (프로젝트 내부 개발 버전)
- 논문에서 다른 모델들과 비교하는 것은 **부적절**

**사용자의 명확한 요구사항**:
> "v1, v2, v3, v4 모두 우리 모델이고, 옛날 버전이야. 
> 그런데, 해당 모델들은 이 연구에서 고려대상이 아닌데 왜 
> 이것들과 비교하려는거지?"

---

## 📋 **제거 대상**

### **1. Section 4.1: "Model Evolution: From v1 to v3"** 전체 삭제
- Line 261-302: v1, v2, v3 설명
- 이들은 연구 대상이 아님!

### **2. Section 6.2.1: "Baseline Comparison"** 수정
- v1-v3를 baseline으로 비교하는 것 제거
- 현재 모델만 설명

### **3. Figure references to v1-v3** 제거
- Line 665-676: Model v1, v2, v3 설명
- Figure `fig:model_evolution` 관련 내용

---

## ✅ **수정 계획**

### **Option 1: Simple Standalone Model** ⭐ **추천**

**Section 4 시작 부분을 간단하게**:

```latex
\section{Phase-Optimized Put-Rate Model}
\label{sec:phase_optimized_model}

We present a phase-optimized, context-aware put-rate prediction model 
that recognizes and adapts to three distinct operational phases. The 
model uses phase-specific calibration factors and context-driven 
refinement to achieve 84.5\% overall accuracy...

\subsection{Core Design Principles}

The model is based on three fundamental principles:
\begin{itemize}
    \item Phase-specific calibration factors (Initial: 1.579, Middle: 1.0, Final: 2.065)
    \item Context-aware adaptation using observable indicators (CV, LSM depth)
    \item Utilization factor reflecting device bandwidth constraints
\end{itemize}
```

**장점**:
- ✅ 논문이 간결하고 집중됨
- ✅ 현재 모델에만 집중
- ✅ 불필요한 비교 제거
- ✅ Self-explanatory 유지

---

### **수정 사항 요약**

1. **Section 4.1 삭제**: "Model Evolution: From v1 to v3" 전체 삭제
2. **Section 4 시작 단순화**: Current model만 설명
3. **Baseline Table 제거**: Section 6.2.1에서 v1-v3 비교 삭제
4. **Figure references 정리**: v1-v3 관련 그림/설명 제거

**논문의 명확한 구조**:
- Abstract: Phase-optimized model 소개
- Section 3: Background (RocksDB/LSM-tree)
- Section 4: **Phase-Optimized Model** (현재 모델만)
- Section 5: Experimental Validation (현재 모델 검증)
- Section 6: Key Findings
- ...

논문이 **완전히 standalone**이고 **self-explanatory**!

