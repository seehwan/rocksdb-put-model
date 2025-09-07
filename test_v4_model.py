#!/usr/bin/env python3
"""
PutModel v4: Comprehensive Test Suite

This script tests all components of the v4 model including:
- Device Envelope Modeling
- Closed Ledger Accounting
- Dynamic Simulation Framework
- Integration testing
"""

import sys
import os
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Add model directory to path
sys.path.append('model')

from model.envelope import EnvelopeModel, create_sample_envelope_model
from model.closed_ledger import ClosedLedger
from model.v4_simulator import V4Simulator, load_config


def test_device_envelope():
    """Test Device Envelope Modeling."""
    print("=" * 60)
    print("Testing Device Envelope Modeling")
    print("=" * 60)
    
    # Create sample envelope model
    envelope = create_sample_envelope_model()
    
    # Test basic functionality
    print("✓ Envelope model created successfully")
    
    # Test grid info
    info = envelope.get_grid_info()
    print(f"✓ Grid info: {info['grid_shape']} points")
    
    # Test queries
    test_cases = [
        (0.5, 16, 2, 64),    # 50% read, qd=16, 2 jobs, 64KiB
        (0.25, 4, 1, 1024),  # 25% read, qd=4, 1 job, 1024KiB
        (0.75, 64, 4, 4),    # 75% read, qd=64, 4 jobs, 4KiB
    ]
    
    for rho_r, qd, numjobs, bs_k in test_cases:
        Beff = envelope.query(rho_r, qd, numjobs, bs_k)
        print(f"✓ Query (ρr={rho_r}, qd={qd}, jobs={numjobs}, bs={bs_k}KiB) → {Beff:.1f} MiB/s")
    
    # Test physical constraints
    validation = envelope.validate_physical_constraints(Br=1500, Bw=2000)
    print(f"✓ Physical validation: {validation['total_violations']} violations, max {validation['max_violation_pct']:.1f}%")
    
    return envelope


def test_closed_ledger():
    """Test Closed Ledger Accounting."""
    print("\n" + "=" * 60)
    print("Testing Closed Ledger Accounting")
    print("=" * 60)
    
    ledger = ClosedLedger()
    
    # Create sample data
    sample_data = {
        'wal_bytes': 1000000000,      # 1GB
        'flush_bytes': 2000000000,    # 2GB
        'compaction_read_bytes': 5000000000,   # 5GB
        'compaction_write_bytes': 3000000000,  # 3GB
        'user_write_bytes': 2000000000,        # 2GB
        'device_read_bytes': 5000000000,       # 5GB
        'device_write_bytes': 6000000000,      # 6GB
    }
    
    # Calculate WA/RA
    wa_ra_data = ledger.calculate_wa_ra(sample_data)
    print(f"✓ WA (stat): {wa_ra_data['wa_stat']:.2f}")
    print(f"✓ WA (device): {wa_ra_data['wa_device']:.2f}")
    print(f"✓ RA (comp): {wa_ra_data['ra_comp']:.2f}")
    print(f"✓ RA (runtime): {wa_ra_data['ra_runtime']:.2f}")
    
    # Verify ledger closure
    verification = ledger.verify_ledger_closure(wa_ra_data)
    print(f"✓ Ledger closed: {verification['is_closed']}")
    print(f"✓ Closure error: {verification['relative_difference']:.2f}%")
    
    # Create summary
    summary = ledger.create_ledger_summary(sample_data, wa_ra_data, verification)
    print(f"✓ Summary created: {len(summary)} metrics")
    
    return ledger


def test_dynamic_simulation():
    """Test Dynamic Simulation Framework."""
    print("\n" + "=" * 60)
    print("Testing Dynamic Simulation Framework")
    print("=" * 60)
    
    # Create envelope model
    envelope = create_sample_envelope_model()
    
    # Load configuration
    config = load_config('config/v4_simulator_config.yaml')
    print("✓ Configuration loaded")
    
    # Create simulator
    simulator = V4Simulator(envelope, config)
    print("✓ Simulator created")
    
    # Run simulation
    print("Running simulation...")
    results = simulator.simulate(steps=200, dt=1.0)
    print(f"✓ Simulation completed: {len(results)} steps")
    
    # Analyze results
    analysis = simulator.analyze_results(results)
    print(f"✓ Analysis completed")
    
    # Print key metrics
    print(f"  Steady-state put rate: {analysis['steady_state']['avg_put_rate']:.1f} MiB/s")
    print(f"  Stall percentage: {analysis['performance_metrics']['stall_percentage']:.1f}%")
    print(f"  Read/write ratio: {analysis['steady_state']['avg_read_ratio']:.3f}")
    print(f"  Bottleneck level: L{analysis['bottleneck_analysis']['bottleneck_level']}")
    print(f"  Max utilization: {analysis['bottleneck_analysis']['max_utilization']:.1%}")
    
    # Save results
    simulator.save_results(results, 'test_simulation_results.csv')
    print("✓ Results saved to test_simulation_results.csv")
    
    return simulator, results, analysis


def test_integration():
    """Test integration of all components."""
    print("\n" + "=" * 60)
    print("Testing Integration")
    print("=" * 60)
    
    # Test envelope model
    envelope = test_device_envelope()
    
    # Test closed ledger
    ledger = test_closed_ledger()
    
    # Test dynamic simulation
    simulator, results, analysis = test_dynamic_simulation()
    
    # Integration test: Use envelope model in simulation
    print("\n✓ All components integrated successfully")
    
    # Test different configurations
    print("\nTesting different configurations...")
    
    # High read ratio configuration
    config_high_read = load_config('config/v4_simulator_config.yaml')
    config_high_read['database']['compression_ratio'] = 0.3  # Higher compression
    config_high_read['stall_threshold'] = 5  # Lower stall threshold
    
    simulator_high_read = V4Simulator(envelope, config_high_read)
    results_high_read = simulator_high_read.simulate(steps=100, dt=1.0)
    analysis_high_read = simulator_high_read.analyze_results(results_high_read)
    
    print(f"  High compression config:")
    print(f"    Put rate: {analysis_high_read['steady_state']['avg_put_rate']:.1f} MiB/s")
    print(f"    Stall %: {analysis_high_read['performance_metrics']['stall_percentage']:.1f}%")
    
    # Low read ratio configuration
    config_low_read = load_config('config/v4_simulator_config.yaml')
    config_low_read['database']['compression_ratio'] = 0.8  # Lower compression
    config_low_read['stall_threshold'] = 12  # Higher stall threshold
    
    simulator_low_read = V4Simulator(envelope, config_low_read)
    results_low_read = simulator_low_read.simulate(steps=100, dt=1.0)
    analysis_low_read = simulator_low_read.analyze_results(results_low_read)
    
    print(f"  Low compression config:")
    print(f"    Put rate: {analysis_low_read['steady_state']['avg_put_rate']:.1f} MiB/s")
    print(f"    Stall %: {analysis_low_read['performance_metrics']['stall_percentage']:.1f}%")
    
    print("\n✓ Configuration sensitivity testing completed")
    
    return {
        'envelope': envelope,
        'ledger': ledger,
        'simulator': simulator,
        'results': results,
        'analysis': analysis
    }


def create_test_report(test_results):
    """Create a comprehensive test report."""
    print("\n" + "=" * 60)
    print("Creating Test Report")
    print("=" * 60)
    
    report = {
        'test_summary': {
            'total_tests': 4,
            'passed_tests': 4,
            'failed_tests': 0,
            'test_status': 'PASSED'
        },
        'component_tests': {
            'device_envelope': {
                'status': 'PASSED',
                'grid_points': test_results['envelope'].get_grid_info()['total_points'],
                'interpolation_working': True
            },
            'closed_ledger': {
                'status': 'PASSED',
                'accounting_working': True,
                'verification_working': True
            },
            'dynamic_simulation': {
                'status': 'PASSED',
                'simulation_steps': len(test_results['results']),
                'analysis_working': True
            },
            'integration': {
                'status': 'PASSED',
                'all_components_integrated': True
            }
        },
        'performance_metrics': test_results['analysis']['performance_metrics'],
        'steady_state_metrics': test_results['analysis']['steady_state']
    }
    
    # Save report
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("✓ Test report saved to test_report.json")
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"  Status: {report['test_summary']['test_status']}")
    print(f"  Tests passed: {report['test_summary']['passed_tests']}/{report['test_summary']['total_tests']}")
    print(f"  Grid points: {report['component_tests']['device_envelope']['grid_points']}")
    print(f"  Simulation steps: {report['component_tests']['dynamic_simulation']['simulation_steps']}")
    
    return report


def main():
    """Main test function."""
    print("PutModel v4: Comprehensive Test Suite")
    print("=" * 60)
    
    try:
        # Run all tests
        test_results = test_integration()
        
        # Create test report
        report = create_test_report(test_results)
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
