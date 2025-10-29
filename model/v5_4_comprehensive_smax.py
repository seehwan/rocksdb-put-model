#!/usr/bin/env python3
"""
V5.4 Phase-Optimized, Context-Integrated S_max Model
Comprehensive model incorporating CV, WA, RA, compaction behavior, thread concurrency
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple

class V54DeviceCapacity:
    """Device capacity calculation module"""
    
    def __init__(self):
        self.module_name = "device_capacity"
    
    def calculate_base_capacity(self, device_write_bw_mib_s: float, record_size_bytes: int) -> float:
        """
        Calculate theoretical maximum QPS from device bandwidth
        
        Args:
            device_write_bw_mib_s: Device write bandwidth in MiB/s
            record_size_bytes: Record size in bytes
            
        Returns:
            Base capacity in QPS
        """
        record_size_mib = record_size_bytes / (1024 * 1024)
        return device_write_bw_mib_s / record_size_mib

class V54VolatilitySafety:
    """CV-based safety factor calculation"""
    
    def __init__(self):
        self.module_name = "volatility_safety"
    
    def calculate_safety_factor(self, cv: float, chain_compaction_risk: str) -> float:
        """
        Calculate safety factor based on CV and chain compaction risk
        
        Args:
            cv: Coefficient of variation
            chain_compaction_risk: 'high', 'moderate', or 'low'
            
        Returns:
            Safety factor (0.0 to 1.0)
        """
        base_factors = {
            'high': 0.2,      # High CV + high chain risk
            'moderate': 0.3,  # Moderate risk
            'low': 0.4        # Low risk
        }
        
        base_factor = base_factors.get(chain_compaction_risk, 0.3)
        
        # Adjust based on CV
        if cv > 0.7:
            return base_factor * 0.8  # Very high volatility
        elif cv > 0.5:
            return base_factor * 0.9
        elif cv > 0.3:
            return base_factor * 1.0
        else:
            return base_factor * 1.1

class V54ContextCorrection:
    """Context-aware correction factors"""
    
    def __init__(self):
        self.module_name = "context_correction"
        
        # Phase-specific parameters
        self.phase_params = {
            'initial': {
                'calibration': 1.579,
                'context_bonus': 1.0,
                'phase_factor': 0.5
            },
            'middle': {
                'calibration': 1.0,
                'context_bonus': 1.1,
                'phase_factor': 0.8
            },
            'final': {
                'calibration': 2.065,
                'context_bonus': 1.2,
                'phase_factor': 0.7
            }
        }
    
    def calculate_context_factor(self, phase: str) -> float:
        """
        Calculate context-aware correction factor
        
        Args:
            phase: 'initial', 'middle', or 'final'
            
        Returns:
            Context correction factor
        """
        params = self.phase_params.get(phase, self.phase_params['middle'])
        return params['calibration'] * params['context_bonus'] * params['phase_factor']

class V54ThreadContention:
    """Thread concurrency and contention modeling"""
    
    def __init__(self):
        self.module_name = "thread_contention"
    
    def calculate_contention_factor(self, total_background_threads: int) -> float:
        """
        Calculate thread contention factor
        
        Args:
            total_background_threads: Number of background threads
            
        Returns:
            Contention factor (0.0 to 1.0)
        """
        if total_background_threads <= 2:
            return 0.9   # Low contention
        elif total_background_threads <= 4:
            return 0.8   # Moderate contention
        elif total_background_threads <= 8:
            return 0.7   # High contention
        else:
            return 0.6   # Very high contention

class V54CompactionOverhead:
    """Compaction overhead calculation"""
    
    def __init__(self):
        self.module_name = "compaction_overhead"
    
    def calculate_overhead_factor(self, wa: float, ra: float, compaction_intensity: str) -> float:
        """
        Calculate compaction overhead factor
        
        Args:
            wa: Write amplification
            ra: Read amplification
            compaction_intensity: 'high', 'moderate', or 'low'
            
        Returns:
            Overhead factor (multiplier)
        """
        # Base overhead from WA
        wa_overhead = 1 + (wa - 1) * 0.8
        
        # RA overhead (compaction reads)
        ra_overhead = 1 + (ra / 10)  # Normalize RA
        
        # Intensity multiplier
        intensity_factors = {
            'high': 1.5,       # High intensity compaction
            'moderate': 1.2,   # Moderate
            'low': 1.0        # Low intensity
        }
        
        intensity_factor = intensity_factors.get(compaction_intensity, 1.2)
        
        return wa_overhead * ra_overhead * intensity_factor

class V54PhaseOptimizedSMax:
    """V5.4 Phase-Optimized, Context-Integrated S_max Model"""
    
    def __init__(self):
        self.model_version = "v5.4"
        self.creation_time = datetime.now().isoformat()
        
        # Initialize modules
        self.device = V54DeviceCapacity()
        self.volatility = V54VolatilitySafety()
        self.context = V54ContextCorrection()
        self.threads = V54ThreadContention()
        self.compaction = V54CompactionOverhead()
        
        # Phase-specific parameters
        self.phase_configs = {
            'initial': {
                'cv': 0.714,
                'wa': 1.02,
                'ra': 0.1,
                'compaction_intensity': 'high',
                'chain_compaction_risk': 'high'
            },
            'middle': {
                'cv': 0.516,
                'wa': 2.87,
                'ra': 4.40,
                'compaction_intensity': 'moderate',
                'chain_compaction_risk': 'moderate'
            },
            'final': {
                'cv': 0.474,
                'wa': 4.45,
                'ra': 4.40,
                'compaction_intensity': 'low',
                'chain_compaction_risk': 'low'
            }
        }
    
    def predict_s_max(self, 
                      phase: str,
                      device_write_bw_mib_s: float = 1484.0,
                      record_size_bytes: int = 1024,
                      total_background_threads: int = 5,
                      production_safety_margin: float = 0.8) -> Dict[str, Any]:
        """
        Predict S_max using comprehensive V5.4 model
        
        Args:
            phase: 'initial', 'middle', or 'final'
            device_write_bw_mib_s: Device write bandwidth in MiB/s
            record_size_bytes: Record size in bytes
            total_background_threads: Number of background threads
            production_safety_margin: Safety margin for production (0.0 to 1.0)
            
        Returns:
            Dictionary with S_max prediction and component breakdown
        """
        
        # Get phase configuration
        config = self.phase_configs.get(phase, self.phase_configs['middle'])
        
        # Calculate components
        base_capacity = self.device.calculate_base_capacity(device_write_bw_mib_s, record_size_bytes)
        safety_factor = self.volatility.calculate_safety_factor(config['cv'], config['chain_compaction_risk'])
        context_factor = self.context.calculate_context_factor(phase)
        contention_factor = self.threads.calculate_contention_factor(total_background_threads)
        overhead_factor = self.compaction.calculate_overhead_factor(
            config['wa'], config['ra'], config['compaction_intensity']
        )
        
        # Calculate S_max
        smax_model = (base_capacity * safety_factor * context_factor * contention_factor) / overhead_factor
        smax_production = smax_model * production_safety_margin
        
        # Component breakdown
        components = {
            'base_capacity': base_capacity,
            'safety_factor': safety_factor,
            'context_factor': context_factor,
            'contention_factor': contention_factor,
            'overhead_factor': overhead_factor,
            'cv': config['cv'],
            'wa': config['wa'],
            'ra': config['ra'],
            'compaction_intensity': config['compaction_intensity'],
            'chain_compaction_risk': config['chain_compaction_risk']
        }
        
        return {
            'phase': phase,
            'smax_model': smax_model,
            'smax_production': smax_production,
            'production_safety_margin': production_safety_margin,
            'components': components,
            'model_version': self.model_version,
            'calculation_time': datetime.now().isoformat()
        }
    
    def validate_against_experimental_data(self) -> Dict[str, Any]:
        """Validate model against experimental data"""
        
        experimental_means = {
            'initial': 168047,
            'middle': 124767,
            'final': 110280
        }
        
        validation_results = {}
        
        for phase in ['initial', 'middle', 'final']:
            result = self.predict_s_max(phase)
            experimental = experimental_means[phase]
            
            ratio = result['smax_model'] / experimental
            mape = abs(result['smax_model'] - experimental) / experimental * 100
            
            validation_results[phase] = {
                'predicted': result['smax_model'],
                'experimental': experimental,
                'ratio': ratio,
                'mape': mape,
                'production_smax': result['smax_production']
            }
        
        return validation_results
    
    def sensitivity_analysis(self, phase: str = 'middle') -> Dict[str, Any]:
        """Perform sensitivity analysis on key parameters"""
        
        base_result = self.predict_s_max(phase)
        base_smax = base_result['smax_model']
        
        sensitivity = {}
        
        # CV sensitivity
        config = self.phase_configs[phase].copy()
        for cv_delta in [-0.1, -0.05, 0.05, 0.1]:
            config['cv'] = max(0.0, config['cv'] + cv_delta)
            safety = self.volatility.calculate_safety_factor(config['cv'], config['chain_compaction_risk'])
            smax = (base_result['components']['base_capacity'] * safety * 
                   base_result['components']['context_factor'] * 
                   base_result['components']['contention_factor']) / base_result['components']['overhead_factor']
            sensitivity[f'cv_{cv_delta:+.2f}'] = {
                'cv': config['cv'],
                'smax': smax,
                'change_pct': (smax - base_smax) / base_smax * 100
            }
        
        # WA sensitivity
        config = self.phase_configs[phase].copy()
        for wa_delta in [-0.5, -0.25, 0.25, 0.5]:
            config['wa'] = max(1.0, config['wa'] + wa_delta)
            overhead = self.compaction.calculate_overhead_factor(
                config['wa'], config['ra'], config['compaction_intensity']
            )
            smax = (base_result['components']['base_capacity'] * 
                   base_result['components']['safety_factor'] * 
                   base_result['components']['context_factor'] * 
                   base_result['components']['contention_factor']) / overhead
            sensitivity[f'wa_{wa_delta:+.2f}'] = {
                'wa': config['wa'],
                'smax': smax,
                'change_pct': (smax - base_smax) / base_smax * 100
            }
        
        return {
            'base_smax': base_smax,
            'phase': phase,
            'sensitivity': sensitivity
        }

def main():
    """Demonstrate V5.4 model usage"""
    
    print("=" * 80)
    print("V5.4 Phase-Optimized, Context-Integrated S_max Model")
    print("=" * 80)
    
    # Initialize model
    model = V54PhaseOptimizedSMax()
    
    # Predict S_max for all phases
    print("\nPhase-Specific S_max Predictions:")
    print("-" * 80)
    
    for phase in ['initial', 'middle', 'final']:
        result = model.predict_s_max(phase)
        
        print(f"\n{phase.upper()} Phase:")
        print(f"  Model S_max: {result['smax_model']:,.0f} QPS")
        print(f"  Production S_max: {result['smax_production']:,.0f} QPS")
        print(f"  Components:")
        comps = result['components']
        print(f"    - Base capacity: {comps['base_capacity']:,.0f}")
        print(f"    - Safety factor: {comps['safety_factor']:.3f}")
        print(f"    - Context factor: {comps['context_factor']:.3f}")
        print(f"    - Contention factor: {comps['contention_factor']:.3f}")
        print(f"    - Overhead factor: {comps['overhead_factor']:.3f}")
        print(f"    - CV: {comps['cv']:.3f}")
        print(f"    - WA: {comps['wa']:.2f}")
        print(f"    - RA: {comps['ra']:.2f}")
    
    # Validation
    print("\n" + "=" * 80)
    print("Validation Against Experimental Data:")
    print("-" * 80)
    
    validation = model.validate_against_experimental_data()
    
    print(f"{'Phase':<10} {'Predicted':<12} {'Experimental':<12} {'Ratio':<8} {'MAPE':<8}")
    print("-" * 50)
    
    for phase, data in validation.items():
        print(f"{phase:<10} {data['predicted']:>11,.0f} {data['experimental']:>11,.0f} "
              f"{data['ratio']:>7.2f} {data['mape']:>7.1f}%")
    
    # Sensitivity analysis
    print("\n" + "=" * 80)
    print("Sensitivity Analysis (Middle Phase):")
    print("-" * 80)
    
    sensitivity = model.sensitivity_analysis('middle')
    
    print("CV Sensitivity:")
    for key, data in sensitivity['sensitivity'].items():
        if key.startswith('cv_'):
            print(f"  CV {data['cv']:.3f}: S_max {data['smax']:,.0f} ({data['change_pct']:+.1f}%)")
    
    print("\nWA Sensitivity:")
    for key, data in sensitivity['sensitivity'].items():
        if key.startswith('wa_'):
            print(f"  WA {data['wa']:.2f}: S_max {data['smax']:,.0f} ({data['change_pct']:+.1f}%)")
    
    # Save results
    results = {
        'model_version': model.model_version,
        'predictions': {phase: model.predict_s_max(phase) for phase in ['initial', 'middle', 'final']},
        'validation': validation,
        'sensitivity': sensitivity
    }
    
    output_file = Path('model/v5_4_comprehensive_smax_results.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {output_file}")
    
    return results

if __name__ == '__main__':
    results = main()


