#!/usr/bin/env python3
"""
Phase-B 로그에서 레벨별 컴팩션 통계 추출
시기별 레벨별 RA/WA 변화 패턴 분석
"""

import re
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import os

class LevelWiseCompactionExtractor:
    """레벨별 컴팩션 통계 추출기"""
    
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.compaction_events = []
        self.level_stats = defaultdict(lambda: defaultdict(int))
        self.temporal_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
    def extract_compaction_events(self):
        """로그에서 컴팩션 이벤트 추출"""
        print(f"📊 로그 파일 분석 중: {self.log_file_path}")
        
        # 컴팩션 패턴들 (실제 로그 형식에 맞게 수정)
        patterns = {
            'flush': r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d{6})\s+(\d+)\s+.*Level-0 flush table #(\d+): (\d+) bytes OK',
            'compaction_start': r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d{6})\s+(\d+)\s+.*Started (\w+) compaction from level-(\d+) to level-(\d+)',
            'compaction_finish': r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d{6})\s+(\d+)\s+.*(\w+) compaction from level-(\d+) to level-(\d+) finished: (\d+) bytes',
            'level_summary': r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d{6})\s+(\d+)\s+.*Level summary: files\[([^\]]+)\]'
        }
        
        with open(self.log_file_path, 'r') as f:
            for line_num, line in enumerate(f):
                # Flush 이벤트
                flush_match = re.search(patterns['flush'], line)
                if flush_match:
                    timestamp, thread_id, table_id, bytes_str = flush_match.groups()
                    self.compaction_events.append({
                        'timestamp': timestamp,
                        'thread_id': int(thread_id),
                        'level': 0,
                        'type': 'flush',
                        'table_id': int(table_id),
                        'bytes': int(bytes_str),
                        'line_num': line_num
                    })
                
                # Compaction 완료 이벤트
                compaction_match = re.search(patterns['compaction_finish'], line)
                if compaction_match:
                    timestamp, thread_id, compaction_type, from_level, to_level, bytes_str = compaction_match.groups()
                    self.compaction_events.append({
                        'timestamp': timestamp,
                        'thread_id': int(thread_id),
                        'level': int(to_level),
                        'type': 'compaction',
                        'compaction_type': compaction_type,
                        'from_level': int(from_level),
                        'to_level': int(to_level),
                        'bytes': int(bytes_str),
                        'line_num': line_num
                    })
        
        print(f"✅ 총 {len(self.compaction_events)}개의 컴팩션 이벤트 추출 완료")
        return self.compaction_events
    
    def analyze_level_wise_stats(self):
        """레벨별 통계 분석"""
        print("📊 레벨별 컴팩션 통계 분석 중...")
        
        # 레벨별 기본 통계
        for event in self.compaction_events:
            level = event['level']
            event_type = event['type']
            bytes_size = event['bytes']
            
            self.level_stats[level][f'{event_type}_count'] += 1
            self.level_stats[level][f'{event_type}_bytes'] += bytes_size
            
            # 시간대별 분석 (시간대별로 그룹화)
            timestamp = event['timestamp']
            hour_key = timestamp[:13]  # YYYY/MM/DD-HH
            
            self.temporal_stats[hour_key][level][f'{event_type}_count'] += 1
            self.temporal_stats[hour_key][level][f'{event_type}_bytes'] += bytes_size
        
        # 레벨별 RA/WA 계산
        level_amplification = {}
        for level in sorted(self.level_stats.keys()):
            stats = self.level_stats[level]
            
            # Write Amplification (WA)
            flush_bytes = stats.get('flush_bytes', 0)
            compaction_bytes = stats.get('compaction_bytes', 0)
            total_write_bytes = flush_bytes + compaction_bytes
            
            wa = total_write_bytes / flush_bytes if flush_bytes > 0 else 0
            
            # Read Amplification (RA) - compaction read bytes / user write bytes
            # FillRandom에서는 user write ≈ flush bytes
            ra = compaction_bytes / flush_bytes if flush_bytes > 0 else 0
            
            level_amplification[level] = {
                'write_amplification': wa,
                'read_amplification': ra,
                'flush_count': stats.get('flush_count', 0),
                'compaction_count': stats.get('compaction_count', 0),
                'flush_bytes': flush_bytes,
                'compaction_bytes': compaction_bytes,
                'total_bytes': total_write_bytes
            }
        
        return level_amplification
    
    def analyze_temporal_amplification(self):
        """시기별 레벨별 RA/WA 분석"""
        print("📊 시기별 레벨별 RA/WA 분석 중...")
        
        # 시간순으로 정렬
        sorted_hours = sorted(self.temporal_stats.keys())
        
        # 시기별 분할 (실제 성능 기반)
        total_hours = len(sorted_hours)
        initial_hours = int(total_hours * 0.1)  # 처음 10%
        middle_hours = int(total_hours * 0.3)   # 중간 30%
        final_hours = total_hours - initial_hours - middle_hours  # 나머지 60%
        
        phases = {
            'initial': sorted_hours[:initial_hours],
            'middle': sorted_hours[initial_hours:initial_hours + middle_hours],
            'final': sorted_hours[initial_hours + middle_hours:]
        }
        
        temporal_amplification = {}
        
        for phase_name, hour_list in phases.items():
            phase_amplification = {}
            
            for level in [0, 1, 2, 3, 4, 5, 6]:  # L0-L6
                phase_flush_bytes = 0
                phase_compaction_bytes = 0
                phase_flush_count = 0
                phase_compaction_count = 0
                
                for hour in hour_list:
                    if hour in self.temporal_stats and level in self.temporal_stats[hour]:
                        hour_stats = self.temporal_stats[hour][level]
                        phase_flush_bytes += hour_stats.get('flush_bytes', 0)
                        phase_compaction_bytes += hour_stats.get('compaction_bytes', 0)
                        phase_flush_count += hour_stats.get('flush_count', 0)
                        phase_compaction_count += hour_stats.get('compaction_count', 0)
                
                # RA/WA 계산
                wa = (phase_flush_bytes + phase_compaction_bytes) / phase_flush_bytes if phase_flush_bytes > 0 else 0
                ra = phase_compaction_bytes / phase_flush_bytes if phase_flush_bytes > 0 else 0
                
                phase_amplification[level] = {
                    'write_amplification': wa,
                    'read_amplification': ra,
                    'flush_count': phase_flush_count,
                    'compaction_count': phase_compaction_count,
                    'flush_bytes': phase_flush_bytes,
                    'compaction_bytes': phase_compaction_bytes,
                    'io_intensity': phase_compaction_count / max(1, len(hour_list))  # 시간당 컴팩션 수
                }
            
            temporal_amplification[phase_name] = phase_amplification
        
        return temporal_amplification
    
    def generate_enhanced_v4_2_model(self, level_amplification, temporal_amplification):
        """개선된 v4.2 모델 생성"""
        print("🚀 시기별 레벨별 RA/WA를 반영한 v4.2 모델 생성 중...")
        
        enhanced_model = {
            'model_version': 'v4.2_enhanced_level_wise',
            'creation_time': datetime.now().isoformat(),
            'level_wise_amplification': level_amplification,
            'temporal_level_amplification': temporal_amplification,
            'enhanced_predictions': {}
        }
        
        # 시기별 예측 모델 생성
        for phase_name, phase_data in temporal_amplification.items():
            phase_predictions = {}
            
            # 레벨별 성능 영향도 계산
            level_io_impact = {}
            total_wa = 0
            total_ra = 0
            
            for level, level_data in phase_data.items():
                wa = level_data['write_amplification']
                ra = level_data['read_amplification']
                io_intensity = level_data['io_intensity']
                
                # 레벨별 I/O 영향도 (레벨이 깊을수록 영향 증가)
                impact_factor = 1.0 + (level * 0.2)  # 레벨별 영향 증가
                io_impact = (wa + ra) * io_intensity * impact_factor
                
                level_io_impact[level] = {
                    'write_amplification': wa,
                    'read_amplification': ra,
                    'io_impact': io_impact,
                    'impact_factor': impact_factor,
                    'io_intensity': io_intensity
                }
                
                total_wa += wa
                total_ra += ra
            
            # 시기별 전체 성능 예측
            avg_wa = total_wa / len(phase_data) if phase_data else 1.0
            avg_ra = total_ra / len(phase_data) if phase_data else 0.0
            
            # 시기별 성능 인자
            if phase_name == 'initial':
                performance_factor = 0.3  # 초기: 낮은 성능
                stability_factor = 0.2
                io_contention = 0.6
            elif phase_name == 'middle':
                performance_factor = 0.6  # 중기: 중간 성능
                stability_factor = 0.5
                io_contention = 0.8
            else:  # final
                performance_factor = 0.9  # 후기: 높은 성능
                stability_factor = 0.8
                io_contention = 0.9
            
            phase_predictions = {
                'level_wise_impact': level_io_impact,
                'overall_amplification': {
                    'avg_write_amplification': avg_wa,
                    'avg_read_amplification': avg_ra,
                    'performance_factor': performance_factor,
                    'stability_factor': stability_factor,
                    'io_contention': io_contention
                },
                'predicted_s_max': self._calculate_enhanced_s_max(
                    avg_wa, avg_ra, performance_factor, stability_factor
                )
            }
            
            enhanced_model['enhanced_predictions'][phase_name] = phase_predictions
        
        return enhanced_model
    
    def _calculate_enhanced_s_max(self, wa, ra, performance_factor, stability_factor):
        """개선된 S_max 계산"""
        # 기본 대역폭 (Phase-A 데이터 기반)
        base_write_bw = 1074.8  # MB/s (degraded state)
        base_read_bw = 1166.1   # MB/s
        
        # RA/WA를 고려한 조정
        adjusted_write_bw = base_write_bw / (1 + wa * 0.1)  # WA 영향
        adjusted_read_bw = base_read_bw / (1 + ra * 0.05)   # RA 영향
        
        # 성능 인자 적용
        effective_write_bw = adjusted_write_bw * performance_factor * stability_factor
        
        # S_max 계산 (16KB key + 1KB value)
        s_max = (effective_write_bw * 1024 * 1024) / (16 + 1024)  # ops/sec
        
        return s_max
    
    def save_results(self, enhanced_model, output_dir="results"):
        """결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON 결과 저장
        json_file = os.path.join(output_dir, "v4_2_enhanced_level_wise_model.json")
        with open(json_file, 'w') as f:
            json.dump(enhanced_model, f, indent=2)
        
        # 마크다운 리포트 생성
        report_file = os.path.join(output_dir, "v4_2_enhanced_level_wise_report.md")
        self._generate_report(enhanced_model, report_file)
        
        print(f"✅ 결과 저장 완료:")
        print(f"   - JSON: {json_file}")
        print(f"   - Report: {report_file}")
    
    def _generate_report(self, enhanced_model, report_file):
        """마크다운 리포트 생성"""
        with open(report_file, 'w') as f:
            f.write("# V4.2 Enhanced Level-Wise Model Report\n\n")
            f.write(f"**생성 시간**: {enhanced_model['creation_time']}\n\n")
            
            # 레벨별 기본 통계
            f.write("## 레벨별 기본 통계\n\n")
            for level, data in enhanced_model['level_wise_amplification'].items():
                f.write(f"### Level {level}\n")
                f.write(f"- **Write Amplification**: {data['write_amplification']:.3f}\n")
                f.write(f"- **Read Amplification**: {data['read_amplification']:.3f}\n")
                f.write(f"- **Flush Count**: {data['flush_count']:,}\n")
                f.write(f"- **Compaction Count**: {data['compaction_count']:,}\n")
                f.write(f"- **Total Bytes**: {data['total_bytes']:,} bytes\n\n")
            
            # 시기별 분석
            f.write("## 시기별 레벨별 RA/WA 분석\n\n")
            for phase_name, phase_data in enhanced_model['temporal_level_amplification'].items():
                f.write(f"### {phase_name.title()} Phase\n")
                for level, data in phase_data.items():
                    f.write(f"**Level {level}**:\n")
                    f.write(f"- WA: {data['write_amplification']:.3f}\n")
                    f.write(f"- RA: {data['read_amplification']:.3f}\n")
                    f.write(f"- I/O Intensity: {data['io_intensity']:.2f}\n")
                f.write("\n")
            
            # 예측 결과
            f.write("## 향상된 예측 결과\n\n")
            for phase_name, predictions in enhanced_model['enhanced_predictions'].items():
                f.write(f"### {phase_name.title()} Phase Predictions\n")
                overall = predictions['overall_amplification']
                f.write(f"- **예측 S_max**: {predictions['predicted_s_max']:,.0f} ops/sec\n")
                f.write(f"- **평균 WA**: {overall['avg_write_amplification']:.3f}\n")
                f.write(f"- **평균 RA**: {overall['avg_read_amplification']:.3f}\n")
                f.write(f"- **성능 인자**: {overall['performance_factor']:.2f}\n")
                f.write(f"- **안정성 인자**: {overall['stability_factor']:.2f}\n")
                f.write(f"- **I/O 경합**: {overall['io_contention']:.2f}\n\n")

def main():
    """메인 실행 함수"""
    print("🚀 V4.2 Enhanced Level-Wise Model 생성 시작")
    print("=" * 60)
    
    # 로그 파일 경로
    log_file = "/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/rocksdb_log_phase_b.log"
    
    if not os.path.exists(log_file):
        print(f"❌ 로그 파일을 찾을 수 없습니다: {log_file}")
        return
    
    # 추출기 생성 및 실행
    extractor = LevelWiseCompactionExtractor(log_file)
    
    # 1. 컴팩션 이벤트 추출
    extractor.extract_compaction_events()
    
    # 2. 레벨별 통계 분석
    level_amplification = extractor.analyze_level_wise_stats()
    
    # 3. 시기별 분석
    temporal_amplification = extractor.analyze_temporal_amplification()
    
    # 4. 향상된 모델 생성
    enhanced_model = extractor.generate_enhanced_v4_2_model(level_amplification, temporal_amplification)
    
    # 5. 결과 저장
    extractor.save_results(enhanced_model)
    
    print("\n✅ V4.2 Enhanced Level-Wise Model 생성 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
