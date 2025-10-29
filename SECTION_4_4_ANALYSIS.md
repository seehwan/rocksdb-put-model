# Section 4.4 "V3 Dynamic Model Framework" 분석

## 🔍 **현재 상황**

### **Section 4.4에 V3 Dynamic Model Algorithm이 있음**
- Line 538-589: V3 Dynamic Model Framework 설명
- Per-level capacity constraints, backlog dynamics 포함
- 50여 줄의 복잡한 알고리즘

### **실제 구현된 모델은 V5.3**
```bash
model/
├── v5_1_corrected_model.py
├── v5_2_final_phase_optimized.py
├── v5_3_initial_phase_optimized.py
├── v5_3_wa_ra_enhanced.py
├── v5_3_with_pilot_run.py
└── ... (모두 V5.3 계열)
```

**→ V3 Dynamic Model은 구현되지 않음!**

---

## ❓ **V3 Model이 필요한가?**

### **No - 불필요함!**

**이유**:
1. **논문의 핵심 메시지**: Phase-optimized model (V5.3) 하나만 설명
2. **V3와 V5.3은 다른 접근**: 
   - V3: Dynamic simulation with per-level tracking (35 parameters)
   - V5.3: Phase-specific prediction (5 parameters)
3. **V3는 구현 안 됨**: 코드에 없음
4. **혼란만 증가**: 독자가 어느 모델이 메인인지 혼란

---

## ✅ **해결 방법**

### **Option 1: Section 4.4 전체 삭제** (추천)
- V3 Dynamic Model Framework 제거
- Phase-optimized model만 설명
- 논문 집중도 향상
- **절감 페이지**: ~3-4 pages

### **Option 2: Appendix로 이동**
- V3는 이전 연구로 Appendix B에
- 메인 섹션은 V5.3만 설명
- 이론적 완성도 유지

### **Option 3: 간소화**
- V3 설명을 1-2 paragraph로 축소
- 알고리즘은 Reference로만 인용
- 핵심은 V5.3에 집중

---

## 📊 **영향 분석**

### **Pages 절감**
- 현재: 40 pages
- Section 4.4 삭제: ~36-37 pages (목표 35-38 달성!)

### **논문 품질**
- ✅ 핵심 집중도 향상
- ✅ V5.3 설명 명확화
- ✅ Real-time performance 집중
- ✅ Implemented model만 설명

---

## 🎯 **추천: Section 4.4 삭제**

**이유**:
1. 논문은 "phase-optimized model" 1개만 설명
2. V3는 구현 안 됨
3. 페이지 절감 (40 → 36-37)
4. 혼란 제거

