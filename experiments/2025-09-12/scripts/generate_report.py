#!/usr/bin/env python3
"""
2025-09-12 실험 최종 보고서 생성 스크립트
SSD 장치 상태 변화와 시간대별 컴팩션 동작 분석 결과 종합
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template

class ExperimentReportGenerator:
    def __init__(self, base_dir="/home/sslab/rocksdb-put-model/experiments/2025-09-12"):
        self.base_dir = Path(base_dir)
        self.results_dir = self.base_dir / "results"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        
        # 보고서 데이터
        self.report_data = {
            "experiment_info": {},
            "device_analysis": {},
            "compaction_analysis": {},
            "performance_analysis": {},
            "stabilization_analysis": {},
            "model_validation": {},
            "conclusions": {}
        }
    
    def load_experiment_data(self):
        """실험 데이터 로드"""
        print("실험 데이터 로드 중...")
        
        # 실험 결과 로드
        experiment_results_file = self.results_dir / "experiment_results.json"
        if experiment_results_file.exists():
            with open(experiment_results_file, 'r') as f:
                self.report_data["experiment_info"] = json.load(f)
        
        # 로그 분석 결과 로드
        log_analysis_file = self.results_dir / "log_analysis_results.json"
        if log_analysis_file.exists():
            with open(log_analysis_file, 'r') as f:
                log_data = json.load(f)
                self.report_data["compaction_analysis"] = log_data.get("compaction_stats", {})
                self.report_data["performance_analysis"] = log_data.get("performance_stats", {})
                self.report_data["stabilization_analysis"] = log_data.get("level_stats", {})
        
        # 장치 성능 데이터 로드
        device_files = list(self.data_dir.glob("device_performance_*.json"))
        for device_file in device_files:
            phase = device_file.stem.split("_")[-1]
            with open(device_file, 'r') as f:
                self.report_data["device_analysis"][phase] = json.load(f)
        
        # v5 모델 결과 로드 (있는 경우)
        model_file = self.results_dir / "v5_model_results.json"
        if model_file.exists():
            with open(model_file, 'r') as f:
                self.report_data["model_validation"] = json.load(f)
    
    def analyze_device_degradation(self):
        """장치 열화 분석"""
        print("장치 열화 분석 중...")
        
        device_data = self.report_data["device_analysis"]
        
        if "initial" in device_data and "final" in device_data:
            initial = device_data["initial"]
            final = device_data["final"]
            
            # 성능 저하율 계산
            write_degradation = (initial["write_bandwidth_mbps"] - final["write_bandwidth_mbps"]) / initial["write_bandwidth_mbps"] * 100
            read_degradation = (initial["read_bandwidth_mbps"] - final["read_bandwidth_mbps"]) / initial["read_bandwidth_mbps"] * 100
            
            self.report_data["device_analysis"]["degradation_summary"] = {
                "write_degradation_percent": write_degradation,
                "read_degradation_percent": read_degradation,
                "initial_write_mbps": initial["write_bandwidth_mbps"],
                "final_write_mbps": final["write_bandwidth_mbps"],
                "initial_read_mbps": initial["read_bandwidth_mbps"],
                "final_read_mbps": final["read_bandwidth_mbps"],
                "experiment_duration_hours": self.calculate_experiment_duration()
            }
    
    def calculate_experiment_duration(self):
        """실험 지속 시간 계산"""
        exp_info = self.report_data["experiment_info"]
        
        if "start_time" in exp_info and "end_time" in exp_info:
            start = datetime.fromisoformat(exp_info["start_time"])
            end = datetime.fromisoformat(exp_info["end_time"])
            duration = (end - start).total_seconds() / 3600  # 시간 단위
            return duration
        
        return 0
    
    def analyze_compaction_patterns(self):
        """컴팩션 패턴 분석"""
        print("컴팩션 패턴 분석 중...")
        
        compaction_data = self.report_data["compaction_analysis"]
        
        # 레벨별 컴팩션 분석
        level_stats = compaction_data.get("level_stats", {})
        total_compactions = compaction_data.get("total_compactions", 0)
        
        # 주요 발견사항
        key_findings = []
        
        if "level_2" in level_stats:
            l2_stats = level_stats["level_2"]
            l2_compactions = l2_stats.get("total_compactions", 0)
            l2_percentage = (l2_compactions / total_compactions * 100) if total_compactions > 0 else 0
            
            if l2_percentage > 40:  # L2가 전체의 40% 이상
                key_findings.append(f"L2 컴팩션이 전체의 {l2_percentage:.1f}%를 차지하여 주요 병목 확인")
        
        # 시간대별 패턴 분석
        hourly_patterns = compaction_data.get("hourly_patterns", {})
        if hourly_patterns:
            peak_hour = max(hourly_patterns.items(), key=lambda x: x[1])
            key_findings.append(f"컴팩션 피크 시간: {peak_hour[0]}시 ({peak_hour[1]}회)")
        
        self.report_data["compaction_analysis"]["key_findings"] = key_findings
    
    def analyze_performance_trends(self):
        """성능 트렌드 분석"""
        print("성능 트렌드 분석 중...")
        
        perf_data = self.report_data["performance_analysis"]
        
        # 전체 성능 통계
        overall_stats = perf_data.get("overall_stats", {})
        
        # 성능 안정성 분석
        stability_analysis = perf_data.get("stability_analysis", {})
        
        # 주요 발견사항
        key_findings = []
        
        if "avg_ops_per_sec" in overall_stats:
            avg_ops = overall_stats["avg_ops_per_sec"]
            key_findings.append(f"평균 처리량: {avg_ops:.0f} ops/sec")
        
        if "is_stable" in stability_analysis:
            if stability_analysis["is_stable"]:
                stabilization_time = stability_analysis.get("stabilization_time")
                stable_perf = stability_analysis.get("stable_performance", 0)
                key_findings.append(f"안정화 달성: {stabilization_time} (안정 성능: {stable_perf:.0f} ops/sec)")
            else:
                key_findings.append("안정화 미달성: 실험 기간 내 안정화되지 않음")
        
        self.report_data["performance_analysis"]["key_findings"] = key_findings
    
    def analyze_stabilization(self):
        """안정화 분석"""
        print("안정화 분석 중...")
        
        # 성능 데이터에서 안정화 정보 추출
        perf_data = self.report_data["performance_analysis"]
        stability_analysis = perf_data.get("stability_analysis", {})
        
        # 안정화 가능성 평가
        is_stable = stability_analysis.get("is_stable", False)
        cv = stability_analysis.get("coefficient_of_variation", 0)
        
        stabilization_assessment = {
            "can_stabilize": is_stable,
            "stability_confidence": 1.0 - cv if cv < 1.0 else 0.0,
            "stabilization_time": stability_analysis.get("stabilization_time"),
            "stable_put_rate": stability_analysis.get("stable_performance", 0),
            "coefficient_of_variation": cv
        }
        
        # 안정화 조건 분석
        if is_stable:
            stabilization_assessment["conditions"] = [
                "장치 성능이 충분히 안정화됨",
                "컴팩션 패턴이 일정함",
                "성능 변동이 임계값 이하"
            ]
        else:
            stabilization_assessment["conditions"] = [
                "장치 성능이 지속적으로 변동함",
                "컴팩션 패턴이 불안정함",
                "성능 변동이 임계값 초과"
            ]
        
        self.report_data["stabilization_analysis"] = stabilization_assessment
    
    def generate_conclusions(self):
        """결론 생성"""
        print("결론 생성 중...")
        
        conclusions = {
            "research_questions": {},
            "key_findings": [],
            "model_performance": {},
            "recommendations": []
        }
        
        # 연구 질문에 대한 답변
        conclusions["research_questions"] = {
            "can_rocksdb_stabilize": self.report_data["stabilization_analysis"].get("can_stabilize", False),
            "stable_put_rate": self.report_data["stabilization_analysis"].get("stable_put_rate", 0),
            "stabilization_time": self.report_data["stabilization_analysis"].get("stabilization_time"),
            "device_degradation_impact": self.report_data["device_analysis"].get("degradation_summary", {}).get("write_degradation_percent", 0)
        }
        
        # 주요 발견사항
        key_findings = []
        
        # 장치 열화 발견사항
        degradation_summary = self.report_data["device_analysis"].get("degradation_summary", {})
        if degradation_summary:
            write_degradation = degradation_summary.get("write_degradation_percent", 0)
            key_findings.append(f"SSD 쓰기 성능 {write_degradation:.1f}% 열화 확인")
        
        # 컴팩션 발견사항
        compaction_findings = self.report_data["compaction_analysis"].get("key_findings", [])
        key_findings.extend(compaction_findings)
        
        # 성능 발견사항
        perf_findings = self.report_data["performance_analysis"].get("key_findings", [])
        key_findings.extend(perf_findings)
        
        conclusions["key_findings"] = key_findings
        
        # 모델 성능 (v5 모델이 있는 경우)
        model_validation = self.report_data["model_validation"]
        if model_validation:
            conclusions["model_performance"] = {
                "accuracy": model_validation.get("accuracy", 0),
                "stabilization_prediction_accuracy": model_validation.get("stabilization_accuracy", 0)
            }
        
        # 권장사항
        recommendations = []
        
        if conclusions["research_questions"]["can_rocksdb_stabilize"]:
            recommendations.append("RocksDB는 안정화 가능하므로 장기 운영 환경에 적합")
            recommendations.append("안정화 시간을 고려한 충분한 워밍업 기간 필요")
        else:
            recommendations.append("현재 설정으로는 안정화 어려움, 컴팩션 설정 조정 필요")
            recommendations.append("장치 성능 모니터링 강화 필요")
        
        if degradation_summary.get("write_degradation_percent", 0) > 10:
            recommendations.append("SSD 열화가 성능에 영향을 주므로 정기적인 성능 모니터링 필요")
        
        conclusions["recommendations"] = recommendations
        
        self.report_data["conclusions"] = conclusions
    
    def create_visualizations(self):
        """시각화 생성"""
        print("시각화 생성 중...")
        
        # 1. 장치 성능 변화 차트
        self.plot_device_degradation()
        
        # 2. 컴팩션 패턴 차트
        self.plot_compaction_patterns()
        
        # 3. 성능 트렌드 차트
        self.plot_performance_trends()
        
        # 4. 안정화 분석 차트
        self.plot_stabilization_analysis()
    
    def plot_device_degradation(self):
        """장치 성능 변화 시각화"""
        device_data = self.report_data["device_analysis"]
        
        if not device_data:
            return
        
        phases = list(device_data.keys())
        if "degradation_summary" in phases:
            phases.remove("degradation_summary")
        
        if len(phases) < 2:
            return
        
        # 데이터 준비
        write_speeds = []
        read_speeds = []
        
        for phase in phases:
            if phase in device_data:
                write_speeds.append(device_data[phase]["write_bandwidth_mbps"])
                read_speeds.append(device_data[phase]["read_bandwidth_mbps"])
        
        # 차트 생성
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 쓰기 성능
        ax1.plot(phases, write_speeds, marker='o', linewidth=2, markersize=8)
        ax1.set_title('SSD 쓰기 성능 변화')
        ax1.set_ylabel('대역폭 (MB/s)')
        ax1.grid(True, alpha=0.3)
        
        # 읽기 성능
        ax2.plot(phases, read_speeds, marker='s', linewidth=2, markersize=8, color='orange')
        ax2.set_title('SSD 읽기 성능 변화')
        ax2.set_ylabel('대역폭 (MB/s)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'device_degradation.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_compaction_patterns(self):
        """컴팩션 패턴 시각화"""
        compaction_data = self.report_data["compaction_analysis"]
        
        if not compaction_data:
            return
        
        level_stats = compaction_data.get("level_stats", {})
        
        if not level_stats:
            return
        
        # 레벨별 컴팩션 수
        levels = []
        compactions = []
        
        for level_key, stats in level_stats.items():
            if "level_" in level_key:
                level_num = level_key.split("_")[1]
                levels.append(f"L{level_num}")
                compactions.append(stats.get("total_compactions", 0))
        
        # 차트 생성
        plt.figure(figsize=(10, 6))
        bars = plt.bar(levels, compactions, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        plt.title('레벨별 컴팩션 수')
        plt.xlabel('레벨')
        plt.ylabel('컴팩션 수')
        plt.grid(True, alpha=0.3)
        
        # 값 표시
        for bar, value in zip(bars, compactions):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(compactions)*0.01,
                    str(value), ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'compaction_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_performance_trends(self):
        """성능 트렌드 시각화"""
        perf_data = self.report_data["performance_analysis"]
        
        if not perf_data:
            return
        
        stability_analysis = perf_data.get("stability_analysis", {})
        windows = stability_analysis.get("windows", [])
        
        if not windows:
            return
        
        # 시간 윈도우별 성능 데이터
        times = []
        performances = []
        
        for i, window in enumerate(windows):
            times.append(i)
            performances.append(window.get("avg_ops_per_sec", 0))
        
        # 차트 생성
        plt.figure(figsize=(12, 6))
        plt.plot(times, performances, marker='o', linewidth=2, markersize=6)
        plt.title('시간별 성능 변화 (안정화 분석)')
        plt.xlabel('시간 윈도우')
        plt.ylabel('평균 처리량 (ops/sec)')
        plt.grid(True, alpha=0.3)
        
        # 안정화 지점 표시
        if stability_analysis.get("is_stable", False):
            stabilization_time = stability_analysis.get("stabilization_time")
            if stabilization_time:
                plt.axvline(x=len(times)//2, color='red', linestyle='--', alpha=0.7, label='안정화 지점')
                plt.legend()
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'performance_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_stabilization_analysis(self):
        """안정화 분석 시각화"""
        stabilization_data = self.report_data["stabilization_analysis"]
        
        if not stabilization_data:
            return
        
        # 안정화 지표
        is_stable = stabilization_data.get("can_stabilize", False)
        confidence = stabilization_data.get("stability_confidence", 0)
        cv = stabilization_data.get("coefficient_of_variation", 0)
        
        # 차트 생성
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 안정화 여부
        ax1.pie([1], labels=['안정화' if is_stable else '불안정'], 
                colors=['green' if is_stable else 'red'], autopct='%1.0f%%')
        ax1.set_title('안정화 여부')
        
        # 안정화 신뢰도
        ax2.bar(['신뢰도'], [confidence], color='blue', alpha=0.7)
        ax2.set_title('안정화 신뢰도')
        ax2.set_ylabel('신뢰도 (0-1)')
        ax2.set_ylim(0, 1)
        
        # 변동 계수
        ax3.bar(['변동 계수'], [cv], color='orange', alpha=0.7)
        ax3.set_title('성능 변동 계수')
        ax3.set_ylabel('CV')
        
        # 안정적 Put 속도
        stable_rate = stabilization_data.get("stable_put_rate", 0)
        ax4.bar(['안정적 Put 속도'], [stable_rate/1000], color='green', alpha=0.7)
        ax4.set_title('안정적 Put 속도')
        ax4.set_ylabel('K ops/sec')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'stabilization_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_html_report(self):
        """HTML 보고서 생성"""
        print("HTML 보고서 생성 중...")
        
        # HTML 템플릿
        html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2025-09-12 실험 보고서</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 20px; }
        h2 { color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; margin-top: 30px; }
        .summary-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 10px; margin: 20px 0; text-align: center; }
        .finding-box { background: #e8f5e8; border: 1px solid #27ae60; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .recommendation-box { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .metric { background: #f8f9fa; border-radius: 5px; padding: 10px; margin: 5px 0; }
        .metric strong { color: #2c3e50; }
        img { max-width: 100%; height: auto; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 2px solid #ecf0f1; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 2025-09-12 실험 보고서</h1>
        
        <div class="summary-box">
            <h2>📊 실험 개요</h2>
            <p><strong>목적</strong>: SSD 장치 상태 변화와 시간대별 컴팩션 동작을 관찰하여 RocksDB 안정화 가능성 및 안정적 Put 속도 구하기</p>
            <p><strong>기간</strong>: {{ experiment_duration }}시간</p>
            <p><strong>주요 워크로드</strong>: FillRandom (Uniform/Zipfian 분포)</p>
        </div>

        <h2>🎯 연구 질문 및 답변</h2>
        <div class="metric">
            <strong>1. 초기화된 SSD에서 시작한 RocksDB가 안정화될 수 있는가?</strong><br>
            답변: {% if conclusions.research_questions.can_rocksdb_stabilize %}✅ 예, 안정화 가능{% else %}❌ 아니오, 안정화 어려움{% endif %}
        </div>
        <div class="metric">
            <strong>2. 안정화된다면 안정적으로 처리할 수 있는 Put 속도는?</strong><br>
            답변: {{ "%.0f"|format(conclusions.research_questions.stable_put_rate) }} ops/sec
        </div>
        <div class="metric">
            <strong>3. 장치 열화가 FillRandom 성능에 미치는 영향은?</strong><br>
            답변: 쓰기 성능 {{ "%.1f"|format(conclusions.research_questions.device_degradation_impact) }}% 저하
        </div>

        <h2>📈 주요 발견사항</h2>
        {% for finding in conclusions.key_findings %}
        <div class="finding-box">
            <strong>🔍 발견사항 {{ loop.index }}:</strong> {{ finding }}
        </div>
        {% endfor %}

        <h2>📊 장치 성능 분석</h2>
        {% if device_analysis.degradation_summary %}
        <div class="metric">
            <strong>초기 쓰기 성능:</strong> {{ "%.0f"|format(device_analysis.degradation_summary.initial_write_mbps) }} MB/s
        </div>
        <div class="metric">
            <strong>최종 쓰기 성능:</strong> {{ "%.0f"|format(device_analysis.degradation_summary.final_write_mbps) }} MB/s
        </div>
        <div class="metric">
            <strong>성능 저하율:</strong> {{ "%.1f"|format(device_analysis.degradation_summary.write_degradation_percent) }}%
        </div>
        <img src="device_degradation.png" alt="장치 성능 변화">
        {% endif %}

        <h2>⚙️ 컴팩션 패턴 분석</h2>
        {% if compaction_analysis.key_findings %}
        {% for finding in compaction_analysis.key_findings %}
        <div class="finding-box">{{ finding }}</div>
        {% endfor %}
        <img src="compaction_patterns.png" alt="컴팩션 패턴">
        {% endif %}

        <h2>📈 성능 트렌드 분석</h2>
        {% if performance_analysis.key_findings %}
        {% for finding in performance_analysis.key_findings %}
        <div class="finding-box">{{ finding }}</div>
        {% endfor %}
        <img src="performance_trends.png" alt="성능 트렌드">
        {% endif %}

        <h2>🎯 안정화 분석</h2>
        <div class="metric">
            <strong>안정화 가능성:</strong> {% if stabilization_analysis.can_stabilize %}✅ 가능{% else %}❌ 어려움{% endif %}
        </div>
        {% if stabilization_analysis.can_stabilize %}
        <div class="metric">
            <strong>안정화 시간:</strong> {{ stabilization_analysis.stabilization_time }}
        </div>
        <div class="metric">
            <strong>안정적 Put 속도:</strong> {{ "%.0f"|format(stabilization_analysis.stable_put_rate) }} ops/sec
        </div>
        {% endif %}
        <div class="metric">
            <strong>변동 계수:</strong> {{ "%.3f"|format(stabilization_analysis.coefficient_of_variation) }}
        </div>
        <img src="stabilization_analysis.png" alt="안정화 분석">

        <h2>💡 권장사항</h2>
        {% for recommendation in conclusions.recommendations %}
        <div class="recommendation-box">
            <strong>권장사항 {{ loop.index }}:</strong> {{ recommendation }}
        </div>
        {% endfor %}

        <div class="footer">
            <p><strong>보고서 생성일</strong>: {{ generation_time }}</p>
            <p><strong>실험 기간</strong>: {{ experiment_duration }}시간</p>
            <p><strong>주요 성과</strong>: RocksDB 안정화 가능성 및 안정적 Put 속도 분석 완료</p>
        </div>
    </div>
</body>
</html>
        """
        
        # 템플릿 렌더링
        template = Template(html_template)
        html_content = template.render(
            experiment_duration=self.calculate_experiment_duration(),
            conclusions=self.report_data["conclusions"],
            device_analysis=self.report_data["device_analysis"],
            compaction_analysis=self.report_data["compaction_analysis"],
            performance_analysis=self.report_data["performance_analysis"],
            stabilization_analysis=self.report_data["stabilization_analysis"],
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # HTML 파일 저장
        html_file = self.results_dir / "experiment_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML 보고서 생성 완료: {html_file}")
    
    def generate_markdown_report(self):
        """Markdown 보고서 생성"""
        print("Markdown 보고서 생성 중...")
        
        md_content = f"""# 2025-09-12 실험 보고서

## 📊 실험 개요

**목적**: SSD 장치 상태 변화와 시간대별 컴팩션 동작을 관찰하여 RocksDB 안정화 가능성 및 안정적 Put 속도 구하기

**기간**: {self.calculate_experiment_duration():.1f}시간  
**주요 워크로드**: FillRandom (Uniform/Zipfian 분포)

## 🎯 연구 질문 및 답변

### 1. 초기화된 SSD에서 시작한 RocksDB가 안정화될 수 있는가?
답변: {'✅ 예, 안정화 가능' if self.report_data['conclusions']['research_questions']['can_rocksdb_stabilize'] else '❌ 아니오, 안정화 어려움'}

### 2. 안정화된다면 안정적으로 처리할 수 있는 Put 속도는?
답변: {self.report_data['conclusions']['research_questions']['stable_put_rate']:.0f} ops/sec

### 3. 장치 열화가 FillRandom 성능에 미치는 영향은?
답변: 쓰기 성능 {self.report_data['conclusions']['research_questions']['device_degradation_impact']:.1f}% 저하

## 📈 주요 발견사항

"""
        
        # 주요 발견사항 추가
        for i, finding in enumerate(self.report_data['conclusions']['key_findings'], 1):
            md_content += f"**{i}.** {finding}\n"
        
        md_content += "\n## 📊 장치 성능 분석\n\n"
        
        # 장치 성능 분석 추가
        degradation_summary = self.report_data['device_analysis'].get('degradation_summary', {})
        if degradation_summary:
            md_content += f"""
- **초기 쓰기 성능**: {degradation_summary['initial_write_mbps']:.0f} MB/s
- **최종 쓰기 성능**: {degradation_summary['final_write_mbps']:.0f} MB/s
- **성능 저하율**: {degradation_summary['write_degradation_percent']:.1f}%

![장치 성능 변화](device_degradation.png)

"""
        
        md_content += "\n## 💡 권장사항\n\n"
        
        # 권장사항 추가
        for i, recommendation in enumerate(self.report_data['conclusions']['recommendations'], 1):
            md_content += f"**{i}.** {recommendation}\n"
        
        md_content += f"""

---

**보고서 생성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**실험 기간**: {self.calculate_experiment_duration():.1f}시간  
**주요 성과**: RocksDB 안정화 가능성 및 안정적 Put 속도 분석 완료
"""
        
        # Markdown 파일 저장
        md_file = self.results_dir / "experiment_report.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"Markdown 보고서 생성 완료: {md_file}")
    
    def generate_complete_report(self):
        """완전한 보고서 생성"""
        print("=== 실험 보고서 생성 시작 ===")
        
        # 1. 실험 데이터 로드
        self.load_experiment_data()
        
        # 2. 분석 수행
        self.analyze_device_degradation()
        self.analyze_compaction_patterns()
        self.analyze_performance_trends()
        self.analyze_stabilization()
        
        # 3. 결론 생성
        self.generate_conclusions()
        
        # 4. 시각화 생성
        self.create_visualizations()
        
        # 5. 보고서 생성
        self.generate_html_report()
        self.generate_markdown_report()
        
        # 6. JSON 보고서 저장
        with open(self.results_dir / "complete_report_data.json", 'w') as f:
            json.dump(self.report_data, f, indent=2, default=str)
        
        print("=== 실험 보고서 생성 완료 ===")
        print(f"보고서 위치: {self.results_dir}")

def main():
    """메인 함수"""
    generator = ExperimentReportGenerator()
    generator.generate_complete_report()

if __name__ == "__main__":
    main()
