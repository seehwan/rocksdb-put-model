# System Design vs. Prediction Model: 핵심 차이점

## ✅ **TRIAD/SILK vs. Our Work**

### **핵심 차이점**:

| 특성 | TRIAD/SILK (Balmau et al.) | Our Work |
|------|---------------------------|----------|
| **목적** | System design improvement | Performance prediction |
| **방법** | Modify RocksDB internals | Model without modification |
| **접근** | I/O scheduling, device co-design | Predictive modeling |
| **결과** | Better performing systems | Predictive capability |
| **용도** | Runtime optimization | Proactive planning |

---

## 💡 **자세한 설명**

### **TRIAD/SILK (Balmau et al.)**:

**핵심 기여**:
1. **TRIAD (2017)**: Memory/disk/log synergies
   - System co-design
   - Write amplification alleviation
   - Foreground throughput improvement

2. **SILK (2019)**: I/O scheduling
   - Flush/compaction scheduling
   - Latency spike prevention
   - Stable tail latencies

**특징**:
- ✅ **System modification**: RocksDB 내부 수정
- ✅ **I/O scheduling**: Device interaction 개선
- ✅ **Runtime behavior**: Adaptive mechanisms
- ❌ **No prediction**: Reactive only

---

### **Our Work (This Paper)**:

**핵심 기여**:
1. **Performance prediction model**
2. **Phase-specific optimization**
3. **Context-aware adaptation**

**특징**:
- ✅ **No system modification**: Model only
- ✅ **Predictive capability**: Anticipate performance
- ✅ **Proactive planning**: Capacity planning
- ✅ **Explainable**: Phase-specific factors

---

## 🎯 **왜 Prediction Model이 더 유리한가?**

### **1. Deployment Independence**:
```
TRIAD/SILK: RocksDB 수정 필요 → 배포 어려움
Our Model: Existing RocksDB 사용 → 즉시 적용 가능
```

### **2. Proactive vs Reactive**:
```
TRIAD/SILK: 문제 발생 → Adapt → Solve
Our Model: 예측 → 미리 준비 → 문제 방지
```

### **3. Capacity Planning**:
```
TRIAD/SILK: "시스템을 개선합니다" (어느 정도? 모름)
Our Model: "초기 280 MiB/s → 최종 12 MiB/s 예측" (구체적)
```

### **4. System Design**:
```
TRIAD/SILK: 기존 시스템 수정
Our Model: 새 시스템 설계 시 최적화 가능
```

---

## ✅ **논문에 추가된 내용**

```latex
\textbf{Key Difference:} These works focus on system design 
improvement by modifying RocksDB's internal mechanisms (I/O 
scheduling, memory management, device interaction), while our 
work provides a performance prediction model that anticipates 
behavior without modifying the system. TRIAD/SILK design better 
systems, while our model predicts system performance to enable 
proactive optimization and capacity planning.
```

**핵심 메시지**:
- ✅ TRIAD/SILK = System **improvement** (modification)
- ✅ Our work = **Prediction** (no modification)
- ✅ 각각 다른 목적과 용도

논문이 훨씬 더 명확해졌습니다! ✅

