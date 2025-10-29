# Calibration Requirement 대응 전략

## ❓ **사용자 지적**

**"우리 모델의 경우에도 utilization 측정값을 사용하기 위해서는 실제 실험을 한 번 해야 하잖아. 이런 지적은 어떻게 대응할 수 있어?"**

---

## ✅ **대응 전략**

### **1. 명확히 Limitations에 명시**

논문에 다음 내용 추가:

```latex
\item \textbf{Initial Calibration Requirement}: The utilization factors 
($U_{\text{initial}} = 0.019$, $U_{\text{middle}} = 0.047$, 
$U_{\text{final}} = 0.095$) are empirically derived from experimental 
measurements. Users deploying the model on new systems or with different 
configurations may require an initial pilot run (30-90 minutes) to calibrate 
these factors for their specific environment. However, the model provides 
reasonable default values based on our extensive experimental validation.
```

**핵심 메시지**:
- ✅ Calibration 필요성 인정
- ✅ 하지만 reasonable defaults 제공
- ✅ Brief pilot run (30-90분)으로 해결 가능

---

### **2. TRIAD/SILK와의 차이점 재강조**

#### **TRIAD/SILK의 한계**:
```
목적: System design improvement
필요사항: RocksDB 코드 수정
배포: 어려움 (코드 변경 필요)
```

#### **Our Model의 장점**:
```
목적: Performance prediction
필요사항: 1회 pilot run (30-90분)
배포: 쉬움 (코드 수정 불필요)
```

---

### **3. Calibration vs. Modification 비교**

| 특성 | Our Model | TRIAD/SILK |
|------|-----------|------------|
| **Setup** | Pilot run (30-90분) | Code modification |
| **Deployment** | 즉시 적용 가능 | 코드 수정 필요 |
| **Portability** | 환경별 calibration | Specific to modification |
| **Maintenance** | Config update | Code refactoring |
| **Reversibility** | Switch config | Code revert |

---

### **4. 장기적 목적 강조**

#### **Our Model의 목적**:
```
"Capacity planning과 proactive optimization"

확장된 활용:
1. System design 단계의 성능 예측
2. Device selection 가이드
3. Configuration tuning 가이드
4. Long-term capacity planning
```

vs.

#### **TRIAD/SILK의 목적**:
```
"Runtime performance improvement"

제한된 활용:
1. 이미 배포된 시스템 개선
2. Specific 문제 해결
3. Reactive optimization
```

---

### **5. Pilot Run의 간단함 강조**

#### **How to Calibrate (실제 절차)**:

```bash
# Step 1: Run brief benchmark (30-90분)
db_bench --benchmarks=fillrandom \
         --duration=3600 \
         --report_file=calibration.json

# Step 2: Extract metrics
python extract_utilization.py calibration.json

# Step 3: Update model config
# File: model_config.json
{
  "U_initial": 0.019,   # Measured
  "U_middle": 0.047,    # Measured
  "U_final": 0.095      # Measured
}

# Done! Now use the model for prediction
```

**vs. TRIAD/SILK**:

```bash
# Step 1: Fork RocksDB code
git clone https://github.com/facebook/rocksdb
cd rocksdb

# Step 2: Apply TRIAD/SILK patches
git apply triad.patch silk.patch

# Step 3: Rebuild RocksDB
make -j8

# Step 4: Deploy modified RocksDB
# (Distribute binaries, update all systems...)

# Step 5: Test extensively
# (Can break existing workloads)
```

---

## 💡 **핵심 대응 포인트**

### **1. 인정 + 해결책 제시**:
```
✅ "Yes, calibration is needed"
✅ "But it's simple (30-90 min pilot run)"
✅ "vs. Code modification (months)"
```

### **2. 용도 구분**:
```
Our Model: 
- Capacity planning (디자인 단계)
- Proactive optimization
- Device/configuration selection

TRIAD/SILK:
- Runtime improvement (배포 후)
- Specific problem solving
- Reactive adaptation
```

### **3. Deployment effort 비교**:
```
Our Model:  30-90 min pilot run
TRIAD/SILK: Months of development + testing + deployment
```

---

## 📝 **논문에 추가된 내용**

### **Limitations Section (Section 9.1.3)**:

```latex
\item \textbf{Initial Calibration Requirement}: The utilization factors 
are empirically derived from experimental measurements. Users deploying 
the model on new systems may require an initial pilot run (30-90 minutes) 
to calibrate these factors. However, the model provides reasonable 
default values based on extensive experimental validation.
```

### **Comparison with TRIAD/SILK (Section 2.3)**:

```latex
\textbf{Key Difference:} These works (TRIAD/SILK) focus on system design 
improvement by modifying RocksDB's internal mechanisms, while our work 
provides a performance prediction model that anticipates behavior without 
modifying the system. TRIAD/SILK design better systems, while our model 
predicts system performance to enable proactive optimization.
```

---

## ✅ **결론**

### **대응 전략 요약**:

1. ✅ **Limitations에 명시**: Calibration 필요성 인정
2. ✅ **해결책 제시**: Brief pilot run (30-90분)
3. ✅ **vs. Code modification**: 배포 effort 비교
4. ✅ **목적 차이**: Prediction vs. Improvement
5. ✅ **Reasonable defaults**: 즉시 사용 가능한 defaults 제공

**"Yes, but it's simple compared to system modification"**

이것이 핵심 메시지입니다! ✅

