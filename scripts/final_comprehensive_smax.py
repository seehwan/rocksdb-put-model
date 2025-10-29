#!/usr/bin/env python3
"""
Final Comprehensive S_max Calculation
Incorporating all factors: CV, WA, RA, compaction behavior, thread concurrency
"""

import pandas as pd
import numpy as np
import json

def calculate_final_smax():
    """Calculate final S_max using comprehensive model"""
    
    print("=" * 80)
    print("FINAL COMPREHENSIVE S_MAX CALCULATION")
    print("=" * 80)
    
    # Device characteristics (Phase-A)
    device_write_bw = 1484  # MiB/s
    device_read_bw = 2368    # MiB/s
    device_mixed_bw = 2231   # MiB/s
    record_size_bytes = 1024
    record_size_mib = record_size_bytes / (1024 * 1024)
    
    max_device_qps = device_write_bw / record_size_mib
    
    print(f"\nDevice Capacity:")
    print(f"  Max write bandwidth: {device_write_bw} MiB/s")
    print(f"  Record size: {record_size_bytes} bytes")
    print(f"  Max device QPS: {max_device_qps:.0f}")
    
    # Phase-specific parameters
    phases = {
        'initial': {
            'cv': 0.714,
            'wa': 1.02,
            'ra': 0.1,
            'calibration': 1.579,
            'context_bonus': 1.0,
            'phase_factor': 0.5,
            'compaction_intensity': 'high',
            'chain_risk': 'high'
        },
        'middle': {
            'cv': 0.516,
            'wa': 2.87,
            'ra': 4.40,
            'calibration': 1.0,
            'context_bonus': 1.1,
            'phase_factor': 0.8,
            'compaction_intensity': 'moderate',
            'chain_risk': 'moderate'
        },
        'final': {
            'cv': 0.474,
            'wa': 4.45,
            'ra': 4.40,
            'calibration': 2.065,
            'context_bonus': 1.2,
            'phase_factor': 0.7,
            'compaction_intensity': 'low',
            'chain_risk': 'low'
        }
    }
    
    # Thread characteristics
    thread_config = {
        'write_threads': 1,
        'compaction_threads': 4,
        'flush_threads': 1,
        'total_background': 5
    }
    
    # Calculate contention factor
    def thread_contention_factor(total_threads):
        if total_threads <= 2:
            return 0.9
        elif total_threads <= 4:
            return 0.8
        elif total_threads <= 8:
            return 0.7
        else:
            return 0.6
    
    contention = thread_contention_factor(thread_config['total_background'])
    
    # CV-based safety factor
    def cv_safety_factor(cv, chain_risk):
        """Calculate safety factor based on CV and chain compaction risk"""
        base_factor = {
            'high': 0.2,      # High CV + high chain risk
            'moderate': 0.3,  # Moderate risk
            'low': 0.4        # Low risk
        }[chain_risk]
        
        # Further adjust based on CV
        if cv > 0.7:
            return base_factor * 0.8  # Very high volatility
        elif cv > 0.5:
            return base_factor * 0.9
        elif cv > 0.3:
            return base_factor * 1.0
        else:
            return base_factor * 1.1
    
    # Compaction overhead calculation
    def compaction_overhead_factor(wa, ra, compaction_intensity):
        """Calculate compaction overhead based on amplification and intensity"""
        # Base overhead from WA
        wa_overhead = 1 + (wa - 1) * 0.8
        
        # RA overhead (compaction reads)
        ra_overhead = 1 + (ra / 10)  # Normalize RA
        
        # Intensity multiplier
        intensity_factor = {
            'high': 1.5,       # High intensity compaction
            'moderate': 1.2,   # Moderate
            'low': 1.0        # Low intensity
        }[compaction_intensity]
        
        return wa_overhead * ra_overhead * intensity_factor
    
    print(f"\nThread Configuration:")
    print(f"  Total background threads: {thread_config['total_background']}")
    print(f"  Contention factor: {contention:.2f}")
    
    print("\nPhase-Specific S_max Calculation:")
    print("=" * 80)
    print(f"{'Phase':<10} {'Base':<12} {'Safety':<8} {'WA_Over':<8} {'Context':<8} {'Final':<12} {'Exp':<12} {'Ratio':<8}")
    print("-" * 80)
    
    results = {}
    
    for phase_name, params in phases.items():
        # Calculate components
        base = max_device_qps
        safety = cv_safety_factor(params['cv'], params['chain_risk'])
        comp_overhead = compaction_overhead_factor(params['wa'], params['ra'], params['compaction_intensity'])
        context = params['calibration'] * params['context_bonus'] * params['phase_factor']
        
        # Final S_max calculation
        smax = (base * safety * context * contention) / comp_overhead
        
        # Load experimental mean
        exp_mean = {
            'initial': 168047,
            'middle': 124767,
            'final': 110280
        }[phase_name]
        
        ratio = smax / exp_mean
        
        results[phase_name] = {
            'predicted_smax': smax,
            'experimental_mean': exp_mean,
            'ratio': ratio,
            'components': {
                'base': base,
                'safety': safety,
                'comp_overhead': comp_overhead,
                'context': context,
                'contention': contention
            }
        }
        
        print(f"{phase_name:<10} {base:>11,.0f} {safety:>7.2f} {comp_overhead:>7.2f} "
              f"{context:>7.2f} {smax:>11,.0f} {exp_mean:>11,.0f} {ratio:>7.2f}")
    
    # Calculate recommended production S_max
    print("\n" + "=" * 80)
    print("RECOMMENDED PRODUCTION S_MAX")
    print("=" * 80)
    
    # Apply conservative factors for production
    production_safety_margin = 0.8  # 20% safety margin
    
    for phase_name in ['initial', 'middle', 'final']:
        predicted = results[phase_name]['predicted_smax']
        production_smax = predicted * production_safety_margin
        
        print(f"\n{phase_name.upper()} Phase:")
        print(f"  Model prediction: {predicted:,.0f} QPS")
        print(f"  Production S_max (with 20%% margin): {production_smax:,.0f} QPS")
        print(f"  Components:")
        comps = results[phase_name]['components']
        print(f"    - Base capacity: {comps['base']:,.0f}")
        print(f"    - Safety factor: {comps['safety']:.2f}")
        print(f"    - Compaction overhead: {comps['comp_overhead']:.2f}x")
        print(f"    - Context correction: {comps['context']:.2f}")
        print(f"    - Thread contention: {comps['contention']:.2f}")
    
    # Summary table
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Phase':<10} {'Predicted':<12} {'Production':<12} {'Experimental':<12} {'Match':<8}")
    print("-" * 60)
    
    for phase_name in ['initial', 'middle', 'final']:
        pred = results[phase_name]['predicted_smax']
        prod = pred * production_safety_margin
        exp = results[phase_name]['experimental_mean']
        match = "✅" if 0.8 < results[phase_name]['ratio'] < 1.2 else "⚠️"
        
        print(f"{phase_name:<10} {pred:>11,.0f} {prod:>11,.0f} {exp:>11,.0f} {match:>6}")
    
    # Save results
    with open('final_comprehensive_smax.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n✅ Results saved to final_comprehensive_smax.json")
    
    return results

if __name__ == '__main__':
    results = calculate_final_smax()


