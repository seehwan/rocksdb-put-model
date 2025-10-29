#!/usr/bin/env python3
"""
Calculate accuracy based on S_max prediction
S_max = maximum sustainable put rate that the system can handle
"""

import pandas as pd
import numpy as np
import json

def load_model_params():
    """Load model parameters from the optimized parameters file"""
    with open('model/v5_3_optimized_parameters.json', 'r') as f:
        data = json.load(f)
    
    params = {}
    for phase in ['initial', 'middle', 'final']:
        params[phase] = {
            'U': data['optimized_parameters'][phase]['U'],
            'C': data['optimized_parameters'][phase]['C']
        }
    
    return params

def predict_smax(phase, device_bw_mib_s, record_size_bytes, params):
    """Predict S_max using phase-specific parameters
    S_max = (B_w / record_size) * U * C
    This represents the maximum sustainable put rate
    """
    U = params[phase]['U']
    C = params[phase]['C']
    
    # S_max = (device_bandwidth / record_size) * U * C
    return (device_bw_mib_s * 1024 * 1024) / record_size_bytes * U * C

def calculate_accuracy(actual_qps, predicted_smax):
    """
    Calculate accuracy based on S_max prediction.
    For each data point, we compare:
    - actual_qps: measured QPS
    - predicted_smax: predicted maximum sustainable QPS
    
    Accuracy = 1 - |actual - predicted| / predicted
    This tells us how close the actual rate is to the predicted maximum
    """
    if len(actual_qps) == 0:
        return 0.0
    
    # Calculate mean actual QPS for this phase
    mean_actual_qps = np.mean(actual_qps)
    
    # Calculate relative error: how close is actual to predicted S_max?
    if predicted_smax > 0:
        error = abs(mean_actual_qps - predicted_smax) / predicted_smax
        accuracy = (1 - error) * 100
    else:
        accuracy = 0.0
    
    return max(0, accuracy)

def main():
    print("=" * 80)
    print("S_max (Maximum Sustainable Put Rate) Accuracy Calculation")
    print("=" * 80)
    
    # Load experimental data
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    
    # Convert to hours
    df['time_hours'] = df['secs_elapsed'] / 3600
    df['qps'] = df['interval_qps']
    
    # Phase boundaries
    initial_end = 9.81
    middle_end = 42.0
    
    # Device characteristics from Phase-A
    device_write_bw = 1484  # MiB/s
    
    # Record size (1040 bytes as used in optimization)
    record_size_bytes = 1040
    
    # Model parameters
    params = load_model_params()
    
    # Segment data by phase
    initial_df = df[df['time_hours'] < initial_end]
    middle_df = df[(df['time_hours'] >= initial_end) & (df['time_hours'] < middle_end)]
    final_df = df[df['time_hours'] >= middle_end]
    
    results = {}
    
    phases = [
        ('Initial', initial_df, 'initial', 0, initial_end),
        ('Middle', middle_df, 'middle', initial_end, middle_end),
        ('Final', final_df, 'final', middle_end, None)
    ]
    
    print("\nPhase-Specific S_max Accuracy:")
    print("-" * 80)
    
    for phase_name, phase_df, phase_key, start_time, end_time in phases:
        if len(phase_df) == 0:
            continue
        
        actual_qps = phase_df['qps'].values
        predicted_smax = predict_smax(phase_key, device_write_bw, record_size_bytes, params)
        mean_actual = np.mean(actual_qps)
        
        # Calculate accuracy
        accuracy = calculate_accuracy(actual_qps, predicted_smax)
        
        # Calculate what % of S_max the actual rate is
        utilization_pct = (mean_actual / predicted_smax * 100) if predicted_smax > 0 else 0
        
        results[phase_name] = {
            'accuracy': accuracy,
            'predicted_smax': predicted_smax,
            'actual_mean_qps': mean_actual,
            'utilization_pct': utilization_pct,
            'start': start_time,
            'end': end_time,
            'duration': len(phase_df),
            'cv': np.std(actual_qps) / np.mean(actual_qps) if np.mean(actual_qps) > 0 else 0
        }
        
        print(f"\n{phase_name} Phase ({start_time}h - {end_time if end_time else 'end'}h):")
        print(f"  Predicted S_max: {predicted_smax:.0f} QPS")
        print(f"  Actual Mean QPS: {mean_actual:.0f} QPS")
        print(f"  Utilization: {utilization_pct:.1f}% of S_max")
        print(f"  S_max Accuracy: {accuracy:.1f}%")
        print(f"  CV: {results[phase_name]['cv']:.3f}")
    
    # Calculate overall accuracy
    phase_accuracies = []
    for phase_name in ['Initial', 'Middle', 'Final']:
        if phase_name in results:
            phase_accuracies.append(results[phase_name]['accuracy'])
    
    overall_acc = np.mean(phase_accuracies)
    
    print("\n" + "=" * 80)
    print(f"Overall S_max Accuracy: {overall_acc:.1f}%")
    print("=" * 80)
    
    # Save results
    results['Overall'] = {'accuracy': overall_acc}
    
    with open('smax_accuracy_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to smax_accuracy_results.json")
    
    # Additional analysis
    print("\n" + "=" * 80)
    print("Analysis:")
    print("=" * 80)
    print("\nInterpretation:")
    print("- This accuracy measures how well the model predicts the MAXIMUM sustainable put rate")
    print("- A high accuracy (close to 100%) means the predicted S_max is close to observed rates")
    print("- If actual rate < predicted S_max, the system is operating below capacity")
    print("- If actual rate ≈ predicted S_max, the system is at capacity")
    
    return results

if __name__ == '__main__':
    results = main()


