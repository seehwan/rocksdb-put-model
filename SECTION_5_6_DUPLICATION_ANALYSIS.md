# Section 5 vs Section 6 중복 분석

## 📊 **중복 내용 확인**

### **Section 5 (Experimental Validation)**:
- Line 602-611: Model Validation Results (예측 정확도)
- Line 583-600: Per-Level Performance Analysis (L2 bottleneck, WA)
- Line 571-580: Write Amplification Analysis
- Line 560-570: Actual Performance Metrics
- Line 558-600: RocksDB Performance Measurements

### **Section 6 (Key Findings)**:
- Line 806-817: Model Accuracy and Validation (중복!)
- Line 821-829: L2 Level Bottleneck Identification (중복!)
- Line 831-839: Stall Dynamics Impact
- Line 841-849: Read/Write Ratio Anomaly (중복!)
- Line 851-860: Write Amplification Measurement Discrepancy (중복!)

---

## 🔍 **중복 내용 정리**

### **1. Model Accuracy 중복** ❌

**Section 5 (Line 602-611)**:
```latex
\subsection{Model Validation Results}
Our dynamic model achieved excellent prediction accuracy:
- Predicted put rate: 187 MiB/s
- Actual put rate: 187.1 MiB/s
- Prediction error: 0.0%
```

**Section 6 (Line 806-817)**:
```latex
\subsection{Model Accuracy and Validation}
Our dynamic model achieved excellent prediction accuracy:
- Overall accuracy: 84.5%
- Phase-specific accuracy: Initial: 75.0%, Middle: 92.2%, Final: 86.4%
```

**해결**: Section 6만 유지, Section 5는 제거

---

### **2. L2 Bottleneck 중복** ❌

**Section 5 (Line 583-590)**:
```latex
\subsubsection{Level-wise Write Amplification}
- L2: WA = 22.6 (major bottleneck, 3,968.1 GB written, 45.2% of total)
```

**Section 6 (Line 821-829)**:
```latex
\subsection{L2 Level Bottleneck Identification}
- Write concentration: 45.2% of total writes occur at L2
- Write amplification: WA = 22.6
```

**해결**: Section 6만 유지, Section 5는 간략화

---

### **3. WA Measurement 중복** ❌

**Section 5 (Line 571-580)**:
```latex
\subsubsection{Write Amplification Analysis}
- Statistics-based WA: 1.02
- LOG-based WA: 2.87
- Discrepancy factor: 2.8x
```

**Section 6 (Line 851-860)**:
```latex
\subsection{Write Amplification Measurement Discrepancy}
- Statistics-based WA: 1.02
- LOG-based WA: 2.87
- Discrepancy factor: 2.8x
```

**해결**: Section 6만 유지, Section 5는 간략화

---

### **4. Read/Write Ratio 중복** ❌

**Section 5 (Line 592-600)**:
```latex
\subsubsection{Read/Write Ratio Analysis}
- Total read/write ratio: 0.0005
- Compaction read: 13,439.09 GB
```

**Section 6 (Line 841-849)**:
```latex
\subsection{Read/Write Ratio Anomaly}
- Total ratio: 0.0005
- Compaction read: 13,439.09 GB
```

**해결**: Section 5에서 제거, Section 6만 유지 (Key Finding)

---

## ✅ **해결 전략**

### **Section 5 역할**: 실험 설계 + 결과 측정
- **유지**: Hardware/Software Configuration
- **유지**: Device Calibration
- **유지**: RocksDB 측정값 (요약)
- **제거**: 상세 분석 (Section 6으로 이동)

### **Section 6 역할**: Key Findings + Insights
- **유지**: 모든 subsection (이미 Key Findings)
- **강화**: Context-aware adaptation
- **강화**: Model accuracy justification

---

## 📝 **수정 계획**

### **Section 5 축약** (8 pages → 4-5 pages)

**제거할 subsections**:
1. ❌ "Model Validation Results" (Line 602-611) → Section 6으로
2. ❌ "Per-Level Performance Analysis" 상세 (Line 583-600) → 요약으로
3. ❌ "Write Amplification Analysis" 중복 (Line 571-580) → 요약으로

**유지**:
- ✅ Experimental Environment
- ✅ Device Calibration
- ✅ RocksDB Performance Measurements (요약)

### **Section 6 강화** (이미 Key Findings로 적절)

**유지**:
- ✅ Context-Aware Adaptation
- ✅ Model Accuracy
- ✅ L2 Bottleneck
- ✅ Stall Dynamics
- ✅ WA Measurement Discrepancy

---

## 📊 **예상 효과**

- **Before**: Section 5 (8 pages) + Section 6 (10 pages) = 18 pages
- **After**: Section 5 (4-5 pages) + Section 6 (8 pages) = 12-13 pages
- **감소**: 5-6 pages (41 pages → 35-36 pages)

**목표 달성**: ✅ 35-38 pages

