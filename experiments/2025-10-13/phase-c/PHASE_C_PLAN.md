# Phase-C: Model Analysis and Prediction

**Phase:** C - Model Application and Comparison  
**Status:** ⏳ Pending  
**Duration:** 2-3 hours  
**Depends On:** Phase-A, Phase-B

---

## 🎯 Objectives

1. Apply all models to experimental data
2. Generate predictions for each phase
3. Compare model performance
4. Identify model strengths and weaknesses

---

## 📋 Models to Evaluate

### 1. V4 Device Envelope Model

**Description:** Single-parameter model with dual-structure integration

**Implementation:**
```python
predicted_s_max = (device_write_bw * 1024^2 / 1040) * U_phase

where:
  U_initial = 0.019
  U_middle = 0.047
  U_final = 0.046
```

**Expected Accuracy:** 81.4% overall

---

### 2. V4.1 Temporal Model

**Description:** V4 with explicit temporal evolution factors

**Implementation:**
```python
predicted_s_max = V4_base * temporal_adjustment_factor

where temporal_adjustment_factor varies by:
  - Initial: 0.85 (volatility penalty)
  - Middle: 1.10 (transition bonus)
  - Final: 0.95 (complexity adjustment)
```

**Expected Accuracy:** 78.6% overall (96.9% in middle phase)

---

### 3. V5.3 Initial-Phase-Optimized Model

**Description:** Phase-specific optimization (current champion)

**Implementation:**
```python
predicted_s_max = V4_base * phase_optimization_factor

Phase optimizations:
  - Initial: 2.440x (volatility exploitation)
  - Middle: 1.0 (maintain V4 excellence)
  - Final: 2.743x (stability exploitation)
```

**Expected Accuracy:** 84.5% overall

---

## 📊 Tasks

### Task 1: Data Preparation

**Objective:** Prepare input data for all models

**Steps:**
1. Load Phase-B performance timeline
2. Load Phase-A device envelope
3. Calculate phase boundaries
4. Extract relevant features

**Script:**
```bash
python scripts/prepare_model_inputs.py \
    --timeline ../phase-b/results/performance_timeline.json \
    --envelope ../phase-a/results/device_envelope.json \
    --output data/model_inputs.json
```

**Output:**
```json
{
  "timeline": [
    {
      "timestamp": 60,
      "device_write_bw": 4116.6,
      "actual_qps": 138769,
      "phase": "initial",
      "cv": 0.538,
      "wa": 1.2,
      "ra": 0.1,
      "lsm_depth": 2
    },
    ...
  ]
}
```

---

### Task 2: Apply V4 Model

**Objective:** Generate V4 predictions

**Command:**
```bash
python scripts/apply_v4_model.py \
    --input data/model_inputs.json \
    --output results/v4_predictions.json
```

**Output Format:**
```json
{
  "model": "V4_Device_Envelope",
  "version": "4.0",
  "predictions": [
    {
      "timestamp": 60,
      "predicted_s_max": 78860,
      "actual_qps": 138769,
      "phase": "initial",
      "accuracy": 56.8
    },
    ...
  ],
  "overall_accuracy": 81.4
}
```

---

### Task 3: Apply V4.1 Model

**Objective:** Generate V4.1 temporal predictions

**Command:**
```bash
python scripts/apply_v4_1_model.py \
    --input data/model_inputs.json \
    --output results/v4_1_predictions.json
```

---

### Task 4: Apply V5.3 Model

**Objective:** Generate V5.3 optimized predictions

**Command:**
```bash
python scripts/apply_v5_3_model.py \
    --input data/model_inputs.json \
    --output results/v5_3_predictions.json
```

---

### Task 5: Model Comparison

**Objective:** Compare all models side-by-side

**Command:**
```bash
python scripts/compare_models.py \
    --v4 results/v4_predictions.json \
    --v4_1 results/v4_1_predictions.json \
    --v5_3 results/v5_3_predictions.json \
    --output results/model_comparison.json
```

**Comparison Metrics:**
- Overall accuracy
- Phase-specific accuracy
- Prediction stability (std dev)
- Error distribution
- Best/worst cases

---

## 📈 Visualization

### Task 6: Generate Comparison Charts

**Objective:** Create visual comparisons

**Charts to Generate:**

1. **Prediction vs Actual Timeline**
   - Line plot: Time vs QPS
   - Show all models + actual
   - Highlight phase boundaries

2. **Accuracy Comparison**
   - Bar chart: Model vs Overall Accuracy
   - Phase-wise accuracy breakdown
   - Error bars

3. **Error Distribution**
   - Box plot: Prediction errors by model
   - By phase analysis
   - Outlier identification

4. **Phase Performance Heatmap**
   - Heatmap: Model x Phase → Accuracy
   - Color-coded performance

**Command:**
```bash
python scripts/create_visualizations.py \
    --comparison results/model_comparison.json \
    --output results/visualizations/
```

---

## ✅ Success Criteria

- [ ] All three models applied successfully
- [ ] Predictions generated for all time points
- [ ] Model comparison complete
- [ ] All visualizations created
- [ ] Results match expected accuracy ranges
- [ ] Documentation complete

---

## 🛠️ Scripts to Create

### 1. prepare_model_inputs.py

```python
#!/usr/bin/env python3
"""Prepare input data for model evaluation"""

import json
import sys

def load_performance_data(timeline_path):
    """Load Phase-B performance timeline"""
    pass

def detect_phases(timeline):
    """Classify time points into phases"""
    # Initial: 0-30 min
    # Middle: 30-90 min
    # Final: 90-120 min
    pass

def extract_features(timeline):
    """Extract model input features"""
    pass

if __name__ == '__main__':
    # Add argument parsing
    # Add main logic
    pass
```

---

### 2. apply_v4_model.py

```python
#!/usr/bin/env python3
"""Apply V4 Device Envelope Model"""

import sys
sys.path.append('/home/sslab/rocksdb-put-model')

from model.envelope import V4DeviceEnvelopeModel

def apply_v4(input_data):
    """Apply V4 model to timeline"""
    model = V4DeviceEnvelopeModel()
    
    predictions = []
    for point in input_data['timeline']:
        result = model.predict_s_max(
            device_write_bw_mbps=point['device_write_bw'],
            phase=point['phase']
        )
        
        predictions.append({
            'timestamp': point['timestamp'],
            'predicted_s_max': result.predicted_s_max,
            'actual_qps': point['actual_qps'],
            'phase': point['phase'],
            'accuracy': calculate_accuracy(result.predicted_s_max, point['actual_qps'])
        })
    
    return predictions

if __name__ == '__main__':
    # Add main logic
    pass
```

---

### 3. compare_models.py

```python
#!/usr/bin/env python3
"""Compare model predictions"""

def calculate_metrics(predictions):
    """Calculate accuracy metrics"""
    mape = mean(|pred - actual| / actual) * 100
    rmse = sqrt(mean((pred - actual)^2))
    r_squared = calculate_r_squared(pred, actual)
    
    return {
        'mape': mape,
        'rmse': rmse,
        'r_squared': r_squared
    }

def compare_by_phase(models):
    """Compare models by phase"""
    pass

def rank_models(comparison_results):
    """Rank models by overall performance"""
    pass

if __name__ == '__main__':
    # Add main logic
    pass
```

---

## 📊 Expected Results

### Model Performance Summary

| Model | Initial | Middle | Final | Overall |
|-------|---------|--------|-------|---------|
| V4    | 56.8%   | 96.9%  | 86.6% | 81.4%   |
| V4.1  | 68.5%   | 96.9%  | 70.5% | 78.6%   |
| V5.3  | 75.0%   | 92.2%  | 86.4% | 84.5%   |

### Key Insights to Document

1. **V4 Strengths:**
   - Outstanding middle phase (96.9%)
   - Simple and robust
   - Consistent across conditions

2. **V4.1 Strengths:**
   - Temporal awareness
   - Excellent middle phase
   - Research applications

3. **V5.3 Strengths:**
   - Highest overall (84.5%)
   - Balanced across all phases
   - Context-aware optimization

---

## 🔗 Dependencies

**Input Data:**
- Phase-A: device_envelope.json
- Phase-B: performance_timeline.json

**Model Implementations:**
- `/home/sslab/rocksdb-put-model/model/envelope.py`
- `/home/sslab/rocksdb-put-model/model/v4_1_temporal.py`
- `/home/sslab/rocksdb-put-model/model/v5_3_initial_phase_optimized.py`

**Python Libraries:**
- numpy
- pandas
- scipy
- matplotlib
- seaborn

---

*Phase-C Plan Version: 1.0*  
*Created: 2025-10-13*  
*Status: Ready for Execution*


