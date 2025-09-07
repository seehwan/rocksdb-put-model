#!/usr/bin/env python3
"""
Phase-C: LOG 파일에서 WAF 분석
RocksDB LOG 파일에서 실제 Write Amplification Factor를 추출합니다.
"""

import re
import json
import os
from pathlib import Path

class LogWAFAnalyzer:
    """LOG 파일 WAF 분석기"""
    
    def __init__(self, log_path: str = "/rocksdb/data/LOG"):
        """초기화"""
        self.log_path = log_path
        self.results = {}
        
    def parse_log_file(self):
        """LOG 파일 파싱"""
        print("📖 LOG 파일 파싱 중...")
        
        if not os.path.exists(self.log_path):
            print(f"❌ LOG 파일을 찾을 수 없습니다: {self.log_path}")
            return False
            
        # 통계 데이터 추출을 위한 정규식 패턴들
        patterns = {
            'compaction_read_bytes': r'compaction read bytes: ([\d,]+)',
            'compaction_write_bytes': r'compaction write bytes: ([\d,]+)',
            'flush_write_bytes': r'flush write bytes: ([\d,]+)',
            'bytes_written': r'bytes written: ([\d,]+)',
            'bytes_read': r'bytes read: ([\d,]+)',
            'user_bytes_written': r'user bytes written: ([\d,]+)',
            'compaction_count': r'compaction count: ([\d,]+)',
            'flush_count': r'flush count: ([\d,]+)',
            'stall_count': r'stall count: ([\d,]+)',
            'stall_micros': r'stall micros: ([\d,]+)',
            'bytes_compressed_from': r'bytes compressed from: ([\d,]+)',
            'bytes_compressed_to': r'bytes compressed to: ([\d,]+)'
        }
        
        # 파일 읽기
        try:
            with open(self.log_path, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ LOG 파일 읽기 실패: {e}")
            return False
            
        # 통계 데이터 추출
        stats = {}
        for key, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                # 가장 최근 값 사용 (마지막 매치)
                value_str = matches[-1].replace(',', '')
                try:
                    stats[key] = int(value_str)
                except ValueError:
                    stats[key] = 0
            else:
                stats[key] = 0
                
        self.results['log_statistics'] = stats
        print(f"✅ 통계 데이터 추출 완료: {len(stats)}개 항목")
        
        return True
        
    def calculate_waf_from_log(self):
        """LOG 데이터로부터 WAF 계산"""
        print("📊 LOG 데이터로부터 WAF 계산 중...")
        
        stats = self.results['log_statistics']
        
        # 기본 데이터
        user_bytes = stats.get('user_bytes_written', 0)
        compaction_read = stats.get('compaction_read_bytes', 0)
        compaction_write = stats.get('compaction_write_bytes', 0)
        flush_write = stats.get('flush_write_bytes', 0)
        total_write = stats.get('bytes_written', 0)
        
        print(f"📈 기본 통계:")
        print(f"  사용자 데이터: {user_bytes/1024/1024/1024:.2f} GB")
        print(f"  Compaction 읽기: {compaction_read/1024/1024/1024:.2f} GB")
        print(f"  Compaction 쓰기: {compaction_write/1024/1024/1024:.2f} GB")
        print(f"  Flush 쓰기: {flush_write/1024/1024/1024:.2f} GB")
        print(f"  총 쓰기: {total_write/1024/1024/1024:.2f} GB")
        
        # WAF 계산 방법들
        waf_calculations = {}
        
        # 방법 1: (Compaction Write + Flush Write) / User Bytes
        if user_bytes > 0:
            waf_calculations['method1_compaction_flush'] = (compaction_write + flush_write) / user_bytes
        else:
            waf_calculations['method1_compaction_flush'] = 0
            
        # 방법 2: Total Write / User Bytes
        if user_bytes > 0:
            waf_calculations['method2_total_write'] = total_write / user_bytes
        else:
            waf_calculations['method2_total_write'] = 0
            
        # 방법 3: Compaction Write / User Bytes (Flush 제외)
        if user_bytes > 0:
            waf_calculations['method3_compaction_only'] = compaction_write / user_bytes
        else:
            waf_calculations['method3_compaction_only'] = 0
            
        # Read Amplification
        if user_bytes > 0:
            ra = compaction_read / user_bytes
        else:
            ra = 0
            
        # 압축률
        compressed_from = stats.get('bytes_compressed_from', 0)
        compressed_to = stats.get('bytes_compressed_to', 0)
        if compressed_from > 0:
            compression_ratio = compressed_to / compressed_from
        else:
            compression_ratio = 1.0
            
        # 결과 저장
        self.results['waf_calculations'] = waf_calculations
        self.results['read_amplification'] = ra
        self.results['compression_ratio'] = compression_ratio
        
        print(f"\n📊 WAF 계산 결과:")
        print(f"  방법 1 (Compaction+Flush): {waf_calculations['method1_compaction_flush']:.3f}")
        print(f"  방법 2 (Total Write): {waf_calculations['method2_total_write']:.3f}")
        print(f"  방법 3 (Compaction만): {waf_calculations['method3_compaction_only']:.3f}")
        print(f"  Read Amplification: {ra:.3f}")
        print(f"  압축률: {compression_ratio:.3f}")
        
        # 권장 WAF 선택 (가장 보수적인 값)
        recommended_waf = max(waf_calculations.values()) if waf_calculations.values() else 0
        self.results['recommended_waf'] = recommended_waf
        
        print(f"\n🎯 권장 WAF: {recommended_waf:.3f}")
        
        return True
        
    def save_results(self):
        """결과 저장"""
        output_file = Path("log_waf_results.json")
        
        # 실험 정보 추가
        experiment_data = {
            "experiment_info": {
                "date": "2025-09-08",
                "phase": "Phase-C",
                "test_type": "LOG WAF Analysis",
                "log_file": self.log_path,
                "timestamp": "2025-09-07 16:55:00"
            },
            "log_statistics": self.results.get('log_statistics', {}),
            "waf_calculations": self.results.get('waf_calculations', {}),
            "read_amplification": self.results.get('read_amplification', 0),
            "compression_ratio": self.results.get('compression_ratio', 1.0),
            "recommended_waf": self.results.get('recommended_waf', 0)
        }
        
        with open(output_file, 'w') as f:
            json.dump(experiment_data, f, indent=2)
            
        print(f"\n💾 결과 저장: {output_file}")
        print("✅ LOG WAF 분석 완료!")
        
    def run_analysis(self):
        """전체 분석 실행"""
        print("=== Phase-C: LOG WAF Analysis (2025-09-08) ===")
        print(f"LOG 파일: {self.log_path}")
        print()
        
        if not self.parse_log_file():
            return False
            
        if not self.calculate_waf_from_log():
            return False
            
        self.save_results()
        return True

def main():
    """메인 함수"""
    analyzer = LogWAFAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
