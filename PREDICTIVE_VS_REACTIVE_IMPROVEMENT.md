# Predictive vs Reactive: 논문 개선 완료

## ✅ **핵심 개선사항**

### **사용자 지적**:
"이전 연구들에서는 이론적인 기반을 가지고 성능 예측 모델을 만들기 보다, ad-hoc하게 동적으로 제어하는 기법들을 바탕으로 시스템을 개선하지 않았니? 성능 예측 모델을 만드는 것이 어떤 점에서 더 유리한지를 작성하는게 어때?"

---

## ✅ **개선 완료**

### **이전 (모호한 표현)**:
```latex
Existing LSM-tree research focuses primarily on write amplification 
reduction, compaction strategies, and filter optimization...
```

### **개선 (명확한 구분)**:
```latex
Existing LSM-tree research primarily focuses on ad-hoc dynamic control 
techniques (RL-based configuration \cite{mo2023ruskey}, LLM-based tuning 
\cite{thakkar2024llmtune}, automated compaction selection \cite{wang2025ecotune}) 
that adapt system behavior reactively. While these approaches provide adaptive 
optimization, they lack predictive capability to anticipate performance changes 
before they occur.
```

**추가 강조**:
```latex
In contrast, our work provides a predictive model that enables:
- Proactive capacity planning
- System design decisions
- Performance optimization based on anticipated behavior
- Data-driven system design and optimization
```

---

## 🎯 **핵심 메시지**

### **기존 연구 (Reactive)**:
1. ✅ **RL-based configuration** (Mo et al., 2023)
   - 시스템이 동적으로 adapt
   - 이미 문제가 발생한 후 adjustment

2. ✅ **LLM-based tuning** (Thakkar et al., 2024)
   - Automated configuration generation
   - Optimization based on workload description

3. ✅ **Automated compaction** (Wang et al., 2025)
   - Policy/parameter selection
   - Runtime optimization

**한계**:
- ❌ Predictive capability 없음
- ❌ Performance changes anticipate 불가능
- ❌ Reactive only (문제 발생 후 대응)

---

### **우리 연구 (Predictive)**:

**장점**:
1. ✅ **Proactive planning**:
   - Performance degradation anticipate 가능
   - Capacity planning before deployment
   - System design decisions based on predicted behavior

2. ✅ **Time-aware prediction**:
   - Phase-specific characteristics 이해
   - Initial/Middle/Final phase별 예측
   - Context-aware adaptation

3. ✅ **Data-driven optimization**:
   - Quantitative predictions (84.5% accuracy)
   - Observable system indicators 활용
   - Phase-specific calibration factors

---

## 📊 **비교 분석**

### **Reactive vs Predictive**:

| 특성 | Reactive (기존 연구) | Predictive (우리 연구) |
|------|---------------------|----------------------|
| **방식** | Adaptive control | Predictive modeling |
| **시점** | Problem 발생 후 | Problem 발생 전 |
| **계획** | Impulsive | Proactive |
| **이해** | Empirical adaptation | Theoretical foundation |
| **용도** | Runtime optimization | Capacity planning, system design |
| **예측** | 불가능 | 가능 (84.5% accuracy) |
| **해석** | Black box | Explainable (phase-specific) |

---

## 💡 **Why Predictive Model is Better**

### **1. Proactive vs Reactive**:
```
Reactive: 문제 발생 → 감지 → 대응
Predictive: 시스템 상태 → 예측 → 미리 준비
```

### **2. Capacity Planning**:
```
Reactive: "시스템이 느려졌습니다" → "설정 변경하세요"
Predictive: "초기 phase는 280 MiB/s, final phase는 12 MiB/s가 될 것입니다" 
             → "Capacity를 미리 계획하세요"
```

### **3. System Design**:
```
Reactive: 배포 후 문제 발견 → 수정
Predictive: 배포 전 예측 → 최적화된 설계
```

### **4. Explainability**:
```
Reactive: "RL이 최적 설정 선택" (왜? 모름)
Predictive: "Phase-specific calibration factors (1.579, 1.0, 2.065) 
             based on observed volatility patterns"
```

---

## ✅ **최종 답변**

### **사용자 질문**: "성능 예측 모델을 만드는 것이 어떤 점에서 더 유리한가?"

**답변**:

1. ✅ **Proactive vs Reactive**:
   - Predictive: 문제 발생 전 예측 → 대비
   - Reactive: 문제 발생 후 감지 → 대응

2. ✅ **Capacity Planning**:
   - Predictive: 초기/중기/최종 phase performance 예측 가능
   - Reactive: 실시간 최적화만 제공

3. ✅ **System Design**:
   - Predictive: 배포 전 최적 설계 가능
   - Reactive: 배포 후 조정

4. ✅ **Explainability**:
   - Predictive: Phase-specific factors로 설명 가능
   - Reactive: Black box adaptation

논문이 훨씬 더 명확하고 강력해졌습니다! ✅

**Predictive model의 우월성을 명확히 강조했습니다!**

