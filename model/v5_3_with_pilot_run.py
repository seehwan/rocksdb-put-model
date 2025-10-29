#!/usr/bin/env python3
"""
V5.3 with Pilot Run Integration
Pilot run으로 nominal 값을 환경 특화
"""

import numpy as np
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.v5_3_wa_ra_enhanced import V5_3Enhanced


@dataclass
class PilotRunResult:
    """Pilot run 결과"""
    wa_measured: float
    ra_measured: float
    phase: str
    duration_seconds: float
    records_written: int
    accuracy: Optional[float] = None


@dataclass
class PilotEnhancedResult:
    """Pilot-enhanced 예측 결과"""
    predicted_s_max: float
    phase: str
    base_prediction: float
    wa_used: float
    ra_used: float
    source: str  # 'fixed', 'pilot', 'historical'
    pilot_result: Optional[PilotRunResult] = None


class V5_3WithPilotRun:
    """
    V5.3 with Pilot Run Integration
    
    핵심 기능:
    1. Short pilot run으로 WA/RA 측정
    2. Environment-specific nominal 설정
    3. More accurate predictions
    """
    
    def __init__(self):
        self.model_version = "v5_3_pilot_integrated"
        self.creation_time = datetime.now().isoformat()
        
        # Base enhanced model
        self.v5_3_enhanced = V5_3Enhanced()
        
        # Pilot run results storage
        self.pilot_nominals = {
            'initial': None,
            'middle': None,
            'final': None
        }
        
        # Pilot run configuration
        self.pilot_config = {
            'initial': {
                'num_records': 1_000_000,   # 1M records (~1GB)
                'duration_max': 60,          # 최대 60초
                'acceptable_duration': 30   # 30초 이내
            },
            'middle': {
                'num_records': 5_000_000,   # 5M records
                'duration_max': 300,        # 최대 5분
                'acceptable_duration': 120  # 2분 이내
            },
            'final': {
                'num_records': 10_000_000,  # 10M records
                'duration_max': 600,        # 최대 10분
                'acceptable_duration': 300  # 5분 이내
            }
        }
    
    def run_pilot_benchmark(self, 
                           phase: str,
                           db_path: str,
                           wal_dir: str) -> PilotRunResult:
        """Execute pilot benchmark and measure WA/RA"""
        
        import subprocess
        import json
        import time
        
        config = self.pilot_config[phase]
        
        print(f"Pilot run for {phase} phase:")
        print(f"  Records: {config['num_records']:,}")
        print(f"  Max duration: {config['duration_max']}s")
        
        # Run db_bench
        start_time = time.time()
        
        cmd = [
            'db_bench',
            '--benchmarks=fillrandom',
            f'--num={config["num_records"]}',
            '--value_size=1024',
            '--threads=8',
            f'--db={db_path}',
            f'--wal_dir={wal_dir}',
            '--statistics',
            '--statistics_print_interval=1'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config['duration_max'],
                cwd='/tmp'
            )
            
            duration = time.time() - start_time
            
            # Parse WA/RA from statistics
            wa, ra = self._parse_wa_ra_from_output(result.stdout)
            
            return PilotRunResult(
                wa_measured=wa,
                ra_measured=ra,
                phase=phase,
                duration_seconds=duration,
                records_written=config['num_records']
            )
            
        except subprocess.TimeoutExpired:
            print(f"⚠️  Pilot run timeout ({config['duration_max']}s)")
            return None
        except Exception as e:
            print(f"❌ Pilot run failed: {e}")
            return None
    
    def _parse_wa_ra_from_output(self, output: str) -> Tuple[float, float]:
        """Parse WA/RA from db_bench output"""
        
        import re
        
        # Extract WA from statistics
        wa_match = re.search(r'COMPACT_WRITE_BYTES.*?(\d+)', output)
        flush_match = re.search(r'FLUSH_BYTES_WRITTEN.*?(\d+)', output)
        user_match = re.search(r'Bytes_written.*?(\d+)', output)
        
        # Calculate WA
        compaction_write = int(wa_match.group(1)) if wa_match else 0
        flush_write = int(flush_match.group(1)) if flush_match else 0
        user_write = int(user_match.group(1)) if user_match else 0
        
        if user_write > 0:
            wa = (compaction_write + flush_write) / user_write
        else:
            wa = 1.0
        
        # Extract RA (compaction read / user write)
        ra_match = re.search(r'COMPACT_READ_BYTES.*?(\d+)', output)
        
        if ra_match and user_write > 0:
            ra = int(ra_match.group(1)) / user_write
        else:
            ra = 0.0
        
        return wa, ra
    
    def update_nominal_from_pilot(self, phase: str, pilot_result: PilotRunResult):
        """Update nominal from pilot run"""
        
        self.pilot_nominals[phase] = {
            'wa': pilot_result.wa_measured,
            'ra': pilot_result.ra_measured,
            'timestamp': datetime.now().isoformat(),
            'duration': pilot_result.duration_seconds
        }
        
        print(f"✅ Updated {phase} phase nominal:")
        print(f"   WA: {pilot_result.wa_measured:.2f}")
        print(f"   RA: {pilot_result.ra_measured:.2f}")
        print(f"   Duration: {pilot_result.duration_seconds:.1f}s")
    
    def predict_s_max(self,
                     device_write_bw: float,
                     phase: str,
                     context: Optional[Dict] = None,
                     use_pilot_nominal: bool = True) -> PilotEnhancedResult:
        """Predict with optional pilot run nominal"""
        
        if context is None:
            context = {}
        
        # 1. Determine WA/RA source
        if use_pilot_nominal and self.pilot_nominals[phase]:
            # Use pilot run nominal
            wa = self.pilot_nominals[phase]['wa']
            ra = self.pilot_nominals[phase]['ra']
            source = 'pilot'
            pilot_result = PilotRunResult(
                wa_measured=wa,
                ra_measured=ra,
                phase=phase,
                duration_seconds=self.pilot_nominals[phase]['duration']
            )
        elif 'wa' in context and 'ra' in context:
            # Use provided values
            wa = context['wa']
            ra = context['ra']
            source = 'provided'
            pilot_result = None
        else:
            # Use fixed nominal from base model
            wa = self.v5_3_enhanced.wa_ra_params[phase]['nominal_wa']
            ra = self.v5_3_enhanced.wa_ra_params[phase]['nominal_ra']
            source = 'fixed'
            pilot_result = None
        
        # 2. Base prediction
        base_result = self.v5_3_enhanced.predict_s_max(
            device_write_bw, phase, context
        )
        base_pred = base_result.predicted_s_max
        
        # 3. WA/RA adjustment
        wa_adj, ra_adj, combined = self.v5_3_enhanced._calculate_adjustment(phase, wa, ra)
        
        # 4. Apply
        final_pred = base_pred * combined
        
        return PilotEnhancedResult(
            predicted_s_max=final_pred,
            phase=phase,
            base_prediction=base_pred,
            wa_used=wa,
            ra_used=ra,
            source=source,
            pilot_result=pilot_result
        )
    
    def get_model_info(self) -> Dict:
        """Model information"""
        return {
            'model_name': 'V5.3 with Pilot Run',
            'version': self.model_version,
            'creation_time': self.creation_time,
            'base_model': 'V5.3 Enhanced',
            'enhancement': 'Pilot run for environment-specific nominal values',
            'pilot_configs': self.pilot_config,
            'pilot_nominals': self.pilot_nominals
        }


def main():
    """Pilot run integration demo"""
    print("=" * 80)
    print("🚀 V5.3 with Pilot Run Integration")
    print("=" * 80)
    
    model = V5_3WithPilotRun()
    
    info = model.get_model_info()
    print(f"\n📋 Model: {info['model_name']}")
    print(f"Version: {info['version']}")
    print(f"Base: {info['base_model']}")
    print(f"Enhancement: {info['enhancement']}")
    
    print("\n🎯 Pilot Run Strategy:")
    print("  1. Short benchmark run")
    print("  2. Measure WA/RA")
    print("  3. Update nominal")
    print("  4. Use for accurate prediction")
    
    print("\n💡 Usage:")
    print("  # Step 1: Run pilot")
    print("  pilot_result = model.run_pilot_benchmark('initial', '/db', '/wal')")
    print("  ")
    print("  # Step 2: Update nominal")
    print("  model.update_nominal_from_pilot('initial', pilot_result)")
    print("  ")
    print("  # Step 3: Predict with pilot nominal")
    print("  result = model.predict_s_max(bw, 'initial', {}, use_pilot_nominal=True)")
    
    print("\n" + "=" * 80)
    print("✅ Pilot Run Integration Complete!")
    print("=" * 80)
    print("\nNote: Pilot run requires actual RocksDB setup.")
    print("In production, integrate with real db_bench execution.")


if __name__ == "__main__":
    main()

