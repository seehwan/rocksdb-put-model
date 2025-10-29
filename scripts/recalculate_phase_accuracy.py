#!/usr/bin/env python3
"""
Recalculate phase-specific accuracy based on final phase boundaries (9.81h, 42.0h)
"""

import pandas as pd
import numpy as np
import json

def load_model_params():
    """Load model parameters from the optimized parameters file"""
    import json
    with open('model/v5_3_optimized_parameters.json', 'r') as f:
        data = json.load(f)
    
    params = {}
    for phase in ['initial', 'middle', 'final']:
        params[phase] = {
            'U': data['optimized_parameters'][phase]['U'],
            'C': data['optimized_parameters'][phase]['C']
        }
    
    return params

def calculate_smax(qps, device_bw_mib_s, record_size_mb):
    """Calculate predicted S_max for a given QPS"""
    return (device_bw_mib_s * 1024 * 1024) / record_size_mb

def predict_qps(phase, device_bw_mib_s, record_size_bytes, params):
    """Predict QPS using phase-specific parameters"""
    U = params[phase]['U']
    C = params[phase]['C']
    
    # QPS = (B_w * 1024 * 1024) / record_size_bytes * U * C
    return (device_bw_mib_s * 1024 * 1024) / record_size_bytes * U * C

def calculate_accuracy(actual_qps, predicted_qps):
    """Calculate accuracy percentage based on mean QPS comparison"""
    if len(actual_qps) == 0:
        return 0.0
    
    # Use mean values for accuracy calculation (as in optimization)
    mean_actual = np.mean(actual_qps)
    
    # Accuracy = 1 - |mean_actual - predicted| / mean_actual
    error = abs(mean_actual - predicted_qps) / mean_actual
    accuracy = (1 - error) * 100
    
    return max(0, accuracy)  # Cap at 0% minimum

def main():
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
    
    print("=" * 60)
    print("Phase-Specific Accuracy Recalculation")
    print("=" * 60)
    
    # Calculate for each phase
    phases = [
        ('Initial', initial_df, 'initial', 0, initial_end),
        ('Middle', middle_df, 'middle', initial_end, middle_end),
        ('Final', final_df, 'final', middle_end, None)
    ]
    
    results = {}
    
    for phase_name, phase_df, phase_key, start_time, end_time in phases:
        if len(phase_df) == 0:
            continue
        
        actual_qps = phase_df['qps'].values
        predicted_qps = predict_qps(phase_key, device_write_bw, record_size_bytes, params)
        
        # Calculate accuracy
        accuracy = calculate_accuracy(actual_qps, predicted_qps)
        
        results[phase_name] = {
            'accuracy': accuracy,
            'start': start_time,
            'end': end_time,
            'duration': len(phase_df),
            'mean_qps': np.mean(actual_qps),
            'cv': np.std(actual_qps) / np.mean(actual_qps) if np.mean(actual_qps) > 0 else 0
        }
        
        print(f"\n{phase_name} Phase:")
        print(f"  Time: {start_time}h - {end_time if end_time else 'end'}h")
        print(f"  Data points: {len(phase_df)}")
        print(f"  Accuracy: {accuracy:.1f}%")
        print(f"  Mean QPS: {np.mean(actual_qps):.0f}")
        print(f"  CV: {results[phase_name]['cv']:.3f}")
    
    # Calculate overall accuracy using phase-specific accuracies
    phase_accuracies = []
    for phase_name in ['Initial', 'Middle', 'Final']:
        if phase_name in results:
            phase_accuracies.append(results[phase_name]['accuracy'])
    
    overall_acc = np.mean(phase_accuracies)
    
    print("\n" + "=" * 60)
    print(f"Overall Accuracy: {overall_acc:.1f}%")
    print("=" * 60)
    
    # Save results
    results['Overall'] = {'accuracy': overall_acc}
    
    with open('phase_accuracy_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to phase_accuracy_results.json")
    
    return results

if __name__ == '__main__':
    results = main()

