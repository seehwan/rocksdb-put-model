#!/usr/bin/env python3
"""
Calculate Nominal WA/RA from Actual Experimental Data
실측 데이터에서 nominal 값 추출
"""

import numpy as np
import json
from pathlib import Path

# 실측 데이터 (Phase-B, Phase-C)
PHASE_B_DATA = {
    'wa_statistics': 1.02,  # RocksDB STATISTICS
    'wa_log': 2.87,         # RocksDB LOG
    'compaction_read_gb': 13439.09,
    'compaction_write_gb': 11804.86,
    'flush_write_gb': 1751.57,
    'user_write_gb': 3051.76
}

PHASE_C_DATA = {
    'wa_log': 2.87,
    'level_data': {
        'L0': {'wa': 0.0, 'write_gb': 1670.1},
        'L1': {'wa': 0.0, 'write_gb': 1036.0},
        'L2': {'wa': 22.6, 'write_gb': 3968.1},
        'L3': {'wa': 0.9, 'write_gb': 2096.4}
    }
}

def calculate_nominal_wa_ra():
    """실측 데이터에서 nominal WA/RA 추출"""
    
    print("=" * 80)
    print("📊 Calculate Nominal WA/RA from Experimental Data")
    print("=" * 80)
    
    # 1. Overall WA (Phase-B)
    overall_wa = (PHASE_B_DATA['flush_write_gb'] + PHASE_B_DATA['compaction_write_gb']) / PHASE_B_DATA['user_write_gb']
    
    print("\n1. Overall WA Calculation:")
    print(f"   Flush: {PHASE_B_DATA['flush_write_gb']:.2f} GB")
    print(f"   Compaction Write: {PHASE_B_DATA['compaction_write_gb']:.2f} GB")
    print(f"   User Write: {PHASE_B_DATA['user_write_gb']:.2f} GB")
    print(f"   Overall WA: {overall_wa:.2f}")
    
    # 2. RA (Phase-B)
    overall_ra = PHASE_B_DATA['compaction_read_gb'] / PHASE_B_DATA['user_write_gb']
    
    print(f"\n2. Overall RA Calculation:")
    print(f"   Compaction Read: {PHASE_B_DATA['compaction_read_gb']:.2f} GB")
    print(f"   Overall RA: {overall_ra:.2f}")
    
    # 3. Phase-specific nominal (initial estimation)
    # Initial phase는 아직 데이터가 부족
    # 하지만 이론적으로 계산 가능
    
    nominal_wa_ra = {
        'initial': {
            'wa': PHASE_B_DATA['wa_statistics'],  # 1.02 (early phase는 STATISTICS가 더 적합)
            'ra': 0.1,  # 이론적 추정
            'rationale': 'Early phase has minimal compaction'
        },
        'middle': {
            'wa': PHASE_B_DATA['wa_log'],  # 2.87 (LOG 기준)
            'ra': overall_ra,  # 4.41 (실측값)
            'rationale': 'Phase-B represents middle phase'
        },
        'final': {
            'wa': overall_wa,  # 4.45 (calculated)
            'ra': overall_ra,  # 4.41 (same)
            'rationale': 'Overall WA represents mature phase'
        }
    }
    
    print("\n3. Phase-Specific Nominal Values:")
    print("-" * 80)
    for phase, values in nominal_wa_ra.items():
        print(f"\n{phase.upper()} Phase:")
        print(f"   WA: {values['wa']:.2f}")
        print(f"   RA: {values['ra']:.2f}")
        print(f"   Rationale: {values['rationale']}")
    
    # 4. Recommended model values
    print("\n" + "=" * 80)
    print("📋 Recommended Nominal Values for Model")
    print("=" * 80)
    
    print("""
# For model implementation:

NOMINAL_WA_RA = {
    'initial': {'wa': 1.02, 'ra': 0.1},   # From STATISTICS (early phase)
    'middle': {'wa': 2.87, 'ra': 4.41},   # From LOG (middle phase)
    'final': {'wa': 4.45, 'ra': 4.41}     # Calculated (mature phase)
}

# But model currently uses:
CURRENT_MODEL = {
    'initial': {'wa': 1.2, 'ra': 0.1},    # Slightly higher
    'middle': {'wa': 2.5, 'ra': 0.8},     # Lower
    'final': {'wa': 3.5, 'ra': 0.8}      # Lower
}

# Difference:
# - WA: Actual is higher (2.87 vs 2.5, 4.45 vs 3.5)
# - RA: Actual is MUCH higher (4.41 vs 0.8!)
""")
    
    # 5. Pilot run strategy
    print("\n" + "=" * 80)
    print("💡 Pilot Run Strategy")
    print("=" * 80)
    
    print("""
# Strategy 1: Short Pilot Run
# Run: db_bench --benchmarks=fillrandom --num=1000000
# Measure: wa, ra from first minute
# Use as nominal for initial phase

# Strategy 2: Iterative Nominal Update
# 1. Start with current nominal (1.2, 0.1)
# 2. Run short pilot (1M records)
# 3. Measure actual WA/RA
# 4. Update nominal = (old × 0.7 + measured × 0.3)
# 5. Continue refining

# Strategy 3: Historical Data (current approach)
# Use measured values from Phase-B, Phase-C
# Most reliable
""")
    
    return nominal_wa_ra

def update_model_with_data_driven_nominals():
    """Data-driven nominal 값으로 모델 업데이트"""
    
    print("\n" + "=" * 80)
    print("🔧 Update Model Configuration")
    print("=" * 80)
    
    # Actual measured values
    actual_values = {
        'initial': {'wa': 1.02, 'ra': 0.1, 'source': 'STATISTICS'},
        'middle': {'wa': 2.87, 'ra': 4.41, 'source': 'LOG + calculated'},
        'final': {'wa': 4.45, 'ra': 4.41, 'source': 'Calculated'}
    }
    
    print("\n📊 Actual Measured Values:")
    for phase, values in actual_values.items():
        print(f"  {phase}: WA={values['wa']:.2f}, RA={values['ra']:.2f} ({values['source']})")
    
    print("\n⚠️  Note: RA values are MUCH higher than current nominal!")
    print("    Current model uses 0.8, but actual is 4.41")
    print("    This may need model recalibration")
    
    print("\n✅ Recommendation:")
    print("    1. Use actual measured values for nominal")
    print("    2. Test with pilot run to validate")
    print("    3. Iteratively refine")

if __name__ == "__main__":
    nominal = calculate_nominal_wa_ra()
    update_model_with_data_driven_nominals()

