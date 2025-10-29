# Phase 구분 방법 분석

## ✅ **논문에서 언급된 Phase 구분**

### **Introduction (Section 1)**:
```latex
"The initial phase (0-30 min) shows extreme volatility (CV=0.356)... 
the middle phase (30-90 min) stabilizes (CV=0.027)...
the final phase (90+ min) achieves mature steady-state performance (CV=0.013)"
```

**기준**: **시간 (runtime)**
- Initial: 0-30 minutes
- Middle: 30-90 minutes
- Final: 90+ minutes

---

## 📊 **실제 코드/모델에서의 Phase Detection**

### **방법 1: 시간 기반 (Time-based)**:
```python
if runtime_minutes < 30:
    phase = 'initial'
elif runtime_minutes < 90:
    phase = 'middle'
else:
    phase = 'final'
```

### **방법 2: Bandwidth 기반**:
```python
if bandwidth_mbps > 3000:  # Fresh SSD
    phase = 'initial'
elif bandwidth_mbps > 800:  # Degraded
    phase = 'middle'
else:  # Heavy competition
    phase = 'final'
```

### **방법 3: CV 기반**:
```python
if cv > 0.4:  # High volatility
    phase = 'initial'
elif cv > 0.1:  # Moderate
    phase = 'middle'
else:  # Stable
    phase = 'final'
```

### **방법 4: DB Size 기반**:
```python
if db_size_gb < 5:
    phase = 'initial'
elif db_size_gb < 30:
    phase = 'middle'
else:
    phase = 'final'
```

### **방법 5: Consensus (다수결)**:
```python
phase_indicators = [
    time_based_detection(),      # 시간
    bandwidth_based_detection(), # 대역폭
    cv_based_detection(),         # 변동성
    size_based_detection()       # DB 크기
]
phase = majority_vote(phase_indicators)
```

---

## 💡 **논문에 명시된 기준**

### **Abstract & Introduction**:
- **시간 기반**만 언급
- "initial phase (0-30 min)"
- "middle phase (30-90 min)"
- "final phase (90+ min)"

### **실제 모델 구현**:
- **Multi-factor detection** (시간 + 대역폭 + CV)
- **Consensus voting** (다수결)
- **Bandwidth가 Primary indicator**

---

## ❓ **문제점**: 논문과 실제 구현 불일치

### **논문에서는**:
```
"0-30 min = initial"
```

### **실제 모델에서는**:
```
"Bandwidth > 3000 MB/s = initial
시간 < 30분 = initial
CV > 0.4 = initial
→ Consensus"
```

---

## ✅ **권장사항**

### **논문에 추가해야 할 내용**:
```latex
\subsection{Phase Detection Methodology}

Our model employs a multi-factor phase detection approach that combines:

\begin{enumerate}
    \item \textbf{Time-based detection}: Runtime boundaries
        (Initial: 0-30 min, Middle: 30-90 min, Final: 90+ min)
    \item \textbf{Bandwidth-based detection}: Device bandwidth patterns
        (Initial: >3000 MB/s, Middle: 800-3000 MB/s, Final: <800 MB/s)
    \item \textbf{Volatility-based detection}: CV thresholds
        (Initial: CV>0.4, Middle: 0.1<CV≤0.4, Final: CV≤0.1)
\end{enumerate}

The model employs consensus voting across these indicators to determine 
the operational phase, with time-based detection as the primary reference.
```

---

논문에는 시간만 언급되어 있지만, 실제 모델은 multi-factor detection을 사용합니다!

