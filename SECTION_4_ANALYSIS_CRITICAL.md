# Section 4 재분석: 불필요한 V3 수식 제거 필요

## ❌ **발견된 문제**

### **Line 316-470: V3 수식들이 남아있음**

현재 Section 4 구조:
1. **Line 295-314**: ✅ V5.3 Core Prediction Formula (필요)
2. **Line 316-364**: ❌ Notation and Symbol Definitions (V3용, 35개 파라미터!)
3. **Line 366-382**: ❌ Per-User Device Requirements (V3 수식)
4. **Line 384-398**: ❌ Harmonic Mean for Mixed I/O (V3 수식)
5. **Line 401-415**: ❌ Per-Level Capacity Constraints (V3 수식)
6. **Line 417-432**: ❌ Dynamic Stall Function (V3 수식)
7. **Line 434-450**: ❌ Non-linear Concurrency Scaling (V3 수식)
8. **Line 452-470**: ❌ Backlog Dynamics (V3 수식)
9. **Line 472-536**: ✅ Phase-Specific Parameters (필요)

**→ Line 316-470 전체 삭제 필요!**

---

## 📝 **V5.3에 실제 필요한 것**

### **필요한 것만 남기기**:
1. Core Prediction Formula (Line 295-314) ✅
2. Phase-Specific Parameters (Line 472-536) ✅

### **삭제해야 할 V3 수식들**:
- Notation and Symbol Definitions (35개 파라미터 정의) ❌
- Per-User Device Requirements ❌
- Harmonic Mean for Mixed I/O ❌
- Per-Level Capacity Constraints ❌
- Dynamic Stall Function ❌
- Non-linear Concurrency Scaling ❌
- Backlog Dynamics ❌

**→ 150+ 줄 삭제 → 3-4 pages 감소!**

---

## 🎯 **삭제 후 예상 효과**

- 현재: 39 pages
- V3 수식 삭제 후: ~35-36 pages
- 목표 달성: 35-38 pages ✅

**변화**:
- ✅ V5.3 모델에 집중
- ✅ 불필요한 V3 수식 제거
- ✅ 혼란 제거
- ✅ 논문 가독성 향상

