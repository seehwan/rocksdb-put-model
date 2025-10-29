# Pilot Run Implementation Plan

## 🎯 목표

**Pilot run으로 nominal 값 정교화하여 모델 정확도 향상**

## 📋 **구현 전략**

### **Phase 1: Pilot Run 실행**

```python
# Step 1: Short pilot run
pilot_result = run_pilot_benchmark(
    phase='initial',
    num_records=1_000_000,  # 1M records
    max_duration=60  # 60초
)

# Step 2: Measure WA/RA
wa, ra = extract_wa_ra_from_pilot(pilot_result)

# Step 3: Update nominal
model.update_nominal(phase='initial', wa=wa, ra=ra)
```

### **Phase 2: 예측 개선**

```python
# Before pilot run (fixed nominal)
S_pred_fixed = model.predict(bw, phase, {})
# Accuracy: 83.5%

# After pilot run (measured nominal)
S_pred_pilot = model.predict(bw, phase, {})
# Accuracy: 85-90% (예상)
```

## 💡 **Expected Improvement**

### **정확도 향상 예측**

```python
# Fixed nominal: 87.4% (baseline)
# Pilot run nominal: 90-92% (예상)

# Improvement: +2.6% ~ +4.6%
```

### **이유**

1. **환경 특화**: 실제 환경과 동일
2. **실측값**: 추정이 아닌 측정
3. **적응성**: 환경 변화에 대응

## 🔧 **구현 방법**

### **Option A: Standalone Pilot Run** (간단) ✅

```python
# 사용자가 별도로 실행
pilot_result = run_pilot(num_records=1M)
model.use_nominal_from_pilot(pilot_result)
```

**장점**: 구현 간단
**단점**: 사용자 부담

### **Option B: Integrated Pilot Run** (권장) ✅

```python
# 모델이 자동으로 실행
model.enable_auto_pilot()
S_pred = model.predict_s_max(bw, phase)

# Behind the scenes:
# 1. Check if pilot run needed
# 2. Run automatically if needed
# 3. Measure WA/RA
# 4. Update nominal
# 5. Predict
```

**장점**: 자동화, 사용자 편의
**단점**: 초기 실행 시간 증가

## 📊 **구현 우선순위**

### **Priority 1: Manual Pilot Run** (즉시 구현)

```python
class V5_3WithPilotRun:
    def run_pilot(self, phase, db_path, wal_dir):
        """사용자가 직접 실행"""
        # ...
    
    def predict_with_pilot(self, bw, phase):
        """Pilot run nominal 사용"""
        # ...
```

**구현 난이도**: 낮음
**예상 시간**: 1시간
**정확도 향상**: +2-5%

### **Priority 2: Auto Pilot Run** (향후)

```python
class V5_3AutoPilot:
    def predict_s_max(self, bw, phase, context):
        """자동으로 pilot run 필요성 확인"""
        if self.need_pilot_run(phase):
            self.run_pilot_automatically(phase)
        
        # 예측
        return self._predict(bw, phase)
```

**구현 난이도**: 중간
**예상 시간**: 4시간
**정확도 향상**: +2-5% (manual과 동일)

## 🎯 **최종 권장사항**

### **단계별 접근**

#### **Step 1: Manual Pilot Run 구현** (즉시) ✅

```python
# 구현 완료: model/v5_3_with_pilot_run.py
# 사용법:
pilot_result = model.run_pilot_benchmark('initial', '/db', '/wal')
model.update_nominal_from_pilot('initial', pilot_result)
S_pred = model.predict_s_max(bw, 'initial', use_pilot_nominal=True)
```

#### **Step 2: 검증**

```python
# Pilot run vs Fixed nominal 비교
fixed_acc = evaluate_with_fixed()
pilot_acc = evaluate_with_pilot()

print(f"Fixed: {fixed_acc:.1f}%")
print(f"Pilot: {pilot_acc:.1f}%")
print(f"Improvement: {pilot_acc - fixed_acc:.1f}%")
```

#### **Step 3: Integration (선택적)**

```python
# Auto pilot run integration
# 사용자가 투명하게 사용
```

## ✅ **Implementation Status**

### **Completed** ✅

1. ✅ Pilot run framework 구현
2. ✅ Nominal update 기능
3. ✅ Integration structure

### **Next Steps**

1. 🔶 Pilot run 실행 및 검증
2. 🔶 정확도 비교
3. 🔶 Auto-pilot (선택적)

**현재 상태**: Pilot run framework 준비 완료! 🎉

