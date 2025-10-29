# CV-Based Automatic Phase Detection

## ✅ **구현 완료**

### **모델**: `model/v5_3_cv_auto_detection.py`

**핵심 기능**:
1. **CV 기반 자동 phase 감지**
   - CV > 0.30 → initial
   - 0.05 < CV ≤ 0.30 → middle
   - CV ≤ 0.05 → final

2. **Time-based fallback**
   - CV 측정 불가 시 시간 비율로 구분

3. **Bandwidth-based fallback**
   - 둘 다 없으면 bandwidth로 구분

## 🎯 **테스트 결과**

```
📊 Initial Phase (CV-based)
  CV: 0.356 → Detected: initial ✅
  Predicted S_max: 171,833 ops/sec

📊 Middle Phase (CV-based)
  CV: 0.027 → Detected: final ❌ (middle로 감지되어야 함!)
  Predicted S_max: 300,967 ops/sec

📊 Final Phase (CV-based)
  CV: 0.013 → Detected: final ✅
  Predicted S_max: 124,621 ops/sec

📊 Time-based fallback
  Runtime ratio: 0.50 → Detected: middle ✅
  Predicted S_max: 71,265 ops/sec
```

## ⚠️ **발견된 문제**

**CV=0.027이 "final"로 감지됨**
- 실험에서는 CV=0.027이 **middle** phase
- 현재 threshold: `0.05 < CV <= 0.30` → middle
- 0.027은 범위 안에 있어야 함!

**수정 필요**: CV threshold 조정

## 🔧 **해결책**

CV threshold 업데이트:
- Initial: CV > 0.30 (현재 유지)
- Middle: 0.01 < CV ≤ 0.30 (0.05 → 0.01 변경)
- Final: CV ≤ 0.01 (0.05 → 0.01 변경)

**이유**:
- 실험에서 middle CV=0.027, final CV=0.013
- 둘 다 0.05보다 작음
- 0.01로 기준 변경 필요

