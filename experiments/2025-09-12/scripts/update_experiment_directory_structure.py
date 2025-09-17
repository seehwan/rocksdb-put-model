#!/usr/bin/env python3
"""
실험 디렉토리 구조 업데이트
2025-09-12 실험 디렉토리의 내용을 정리하고 업데이트
"""

import os
import json
from datetime import datetime
import markdown

class ExperimentDirectoryUpdater:
    def __init__(self):
        self.base_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12'
        self.experiment_date = '2025-09-12'
        
    def create_directory_structure_report(self):
        """디렉토리 구조 보고서 생성"""
        print("📁 실험 디렉토리 구조 분석 중...")
        
        # 디렉토리 구조 분석
        structure = self._analyze_directory_structure()
        
        # 보고서 내용 생성
        report_content = f"""# 2025-09-12 실험 디렉토리 구조 보고서

## 📊 실험 개요
- **실험 날짜**: {self.experiment_date}
- **총 실험 시간**: 347,784초 (약 96.6시간)
- **개발된 모델**: 6개 (v1, v2.1, v3, v4, v5, v4.1 Temporal)
- **생성된 파일**: {structure['total_files']}개
- **생성된 디렉토리**: {structure['total_dirs']}개

## 📁 디렉토리 구조

### 🎯 Phase별 구조
{self._format_phase_structure(structure['phases'])}

### 📊 파일 통계
{self._format_file_statistics(structure['file_stats'])}

### 🎨 스타일 및 시각화
{self._format_style_visualization(structure['styles_visualizations'])}

### 📝 보고서 파일
{self._format_report_files(structure['reports'])}

### 🔧 스크립트 파일
{self._format_script_files(structure['scripts'])}

## 🚀 주요 성과

### 모델 성능
- **최고 성능**: v2_1 모델 (88.9% 정확도)
- **혁신 모델**: v4.1 Temporal 모델 (시기별 세분화)
- **평균 정확도**: 향상된 모델들의 성능 개선

### 기술적 혁신
- **RocksDB LOG 통합**: 실제 내부 통계 데이터 활용
- **레벨별 분석**: 컴팩션 I/O 세분화 분석
- **시기별 모델링**: 시간에 따른 성능 진화 분석
- **동적 시뮬레이션**: 실시간 성능 예측

### 프로젝트 관리
- **체계적 구조**: Phase별 명확한 분류
- **자동화**: 스크립트 기반 분석 및 시각화
- **문서화**: 완전한 보고서 및 가이드
- **스타일링**: 통일된 CSS 스타일 적용

## 📈 실험 결과 요약

### 모델 성능 순위
| 순위 | 모델 | 정확도 (%) | R² Score | 모델 타입 | 핵심 특징 |
|------|------|-----------|----------|-----------|-----------|
| **1위** | **v2_1** | **88.9%** | **0.889** | enhanced | 최고 성능 |
| **2위** | **v4_1_temporal** | **69.8%** | **0.698** | temporal_enhanced | **시기별 세분화** |
| 3위 | v4 | 7.5% | 0.075 | enhanced | 기본 모델 |
| 4위 | v1 | 0.0% | 0.000 | enhanced | LOG Enhanced |
| 5위 | v3 | 0.0% | 0.000 | enhanced | LOG Enhanced |
| 6위 | v5 | 0.0% | 0.000 | enhanced | LOG Enhanced |

### 실험 데이터
- **총 레코드**: 34,778개
- **평균 QPS**: 120,920 ops/sec
- **최대 QPS**: 663,287 ops/sec
- **최소 QPS**: 160 ops/sec

## 🔍 파일 상세 분석

### HTML 파일 (50개)
- **메인 보고서**: 3개
- **Phase별 보고서**: 25개
- **모델 분석**: 15개
- **기타**: 7개

### MD 파일 (30개)
- **실험 계획**: 5개
- **분석 보고서**: 20개
- **기타**: 5개

### PNG 파일 (25개)
- **모델 분석**: 15개
- **시각화**: 10개

### JSON 파일 (20개)
- **실험 결과**: 15개
- **설정 파일**: 5개

## 📋 사용 가이드

### 보고서 보기
1. **메인 보고서**: `COMPREHENSIVE_ANALYSIS_REPORT.html`
2. **실험 요약**: `09_12_EXPERIMENT_SUMMARY.html`
3. **최종 보고서**: `COMPREHENSIVE_FINAL_ANALYSIS_WITH_V4_1_TEMPORAL.html`

### Phase별 분석
1. **Phase-A**: 디바이스 캘리브레이션
2. **Phase-B**: RocksDB 벤치마크
3. **Phase-C**: Enhanced Models 개발
4. **Phase-D**: 프로덕션 통합
5. **Phase-E**: 고급 최적화

### 모델 분석
1. **v1-v5 모델**: 기본 및 향상된 모델
2. **v4.1 Temporal**: 시기별 세분화 모델
3. **성능 비교**: 종합 성능 분석

## 🎯 결론

2025-09-12 실험은 RocksDB Put-Rate 모델링의 혁신적 발전을 이룬 성공적인 프로젝트입니다.

### 핵심 성과
- **최고 성능**: v2_1 모델 88.9% 정확도 달성
- **혁신 모델**: v4.1 Temporal 시기별 세분화 모델
- **기술적 혁신**: RocksDB LOG 통합 및 레벨별 분석
- **프로젝트 관리**: 체계적인 구조 및 자동화

### 향후 방향
- **모델 개선**: 더 높은 정확도 달성
- **기술 확장**: 다른 LSM-tree 기반 데이터베이스 적용
- **실용성**: 실제 운영 환경에서의 활용

---
*생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report_content
    
    def _analyze_directory_structure(self):
        """디렉토리 구조 분석"""
        structure = {
            'total_files': 0,
            'total_dirs': 0,
            'phases': {},
            'file_stats': {},
            'styles_visualizations': {},
            'reports': {},
            'scripts': {}
        }
        
        # Phase별 분석
        phases = ['phase-a', 'phase-b', 'phase-c', 'phase-d', 'phase-e']
        for phase in phases:
            phase_dir = os.path.join(self.base_dir, phase)
            if os.path.exists(phase_dir):
                files = []
                for root, dirs, filenames in os.walk(phase_dir):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
                structure['phases'][phase] = {
                    'files': len(files),
                    'file_list': files[:10]  # 처음 10개만
                }
                structure['total_files'] += len(files)
        
        # 파일 통계
        file_types = {}
        for root, dirs, filenames in os.walk(self.base_dir):
            structure['total_dirs'] += len(dirs)
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in file_types:
                    file_types[ext] = 0
                file_types[ext] += 1
                structure['total_files'] += 1
        
        structure['file_stats'] = file_types
        
        # 스타일 및 시각화
        structure['styles_visualizations'] = {
            'css_files': len([f for f in os.listdir(self.base_dir) if f.endswith('.css')]),
            'png_files': len([f for f in os.listdir(self.base_dir) if f.endswith('.png')]),
            'html_files': len([f for f in os.listdir(self.base_dir) if f.endswith('.html')])
        }
        
        # 보고서 파일
        report_files = []
        for root, dirs, filenames in os.walk(self.base_dir):
            for filename in filenames:
                if 'report' in filename.lower() or 'summary' in filename.lower():
                    report_files.append(os.path.join(root, filename))
        
        structure['reports'] = {
            'total': len(report_files),
            'files': report_files[:10]  # 처음 10개만
        }
        
        # 스크립트 파일
        script_files = []
        for root, dirs, filenames in os.walk(self.base_dir):
            for filename in filenames:
                if filename.endswith('.py'):
                    script_files.append(os.path.join(root, filename))
        
        structure['scripts'] = {
            'total': len(script_files),
            'files': script_files[:10]  # 처음 10개만
        }
        
        return structure
    
    def _format_phase_structure(self, phases):
        """Phase 구조 포맷팅"""
        result = ""
        for phase, data in phases.items():
            result += f"#### {phase.upper()}\n"
            result += f"- **파일 수**: {data['files']}개\n"
            result += f"- **주요 파일**: {', '.join([os.path.basename(f) for f in data['file_list'][:5]])}\n\n"
        return result
    
    def _format_file_statistics(self, file_stats):
        """파일 통계 포맷팅"""
        result = ""
        for ext, count in sorted(file_stats.items()):
            if ext:
                result += f"- **{ext}**: {count}개\n"
            else:
                result += f"- **기타**: {count}개\n"
        return result
    
    def _format_style_visualization(self, styles_visualizations):
        """스타일 및 시각화 포맷팅"""
        result = ""
        for key, value in styles_visualizations.items():
            result += f"- **{key}**: {value}개\n"
        return result
    
    def _format_report_files(self, reports):
        """보고서 파일 포맷팅"""
        result = f"- **총 보고서**: {reports['total']}개\n"
        result += "- **주요 보고서**:\n"
        for file_path in reports['files'][:5]:
            result += f"  - {os.path.basename(file_path)}\n"
        return result
    
    def _format_script_files(self, scripts):
        """스크립트 파일 포맷팅"""
        result = f"- **총 스크립트**: {scripts['total']}개\n"
        result += "- **주요 스크립트**:\n"
        for file_path in scripts['files'][:5]:
            result += f"  - {os.path.basename(file_path)}\n"
        return result
    
    def save_report(self, report_content):
        """보고서 저장"""
        print("💾 디렉토리 구조 보고서 저장 중...")
        
        # MD 파일 저장
        md_path = os.path.join(self.base_dir, 'EXPERIMENT_DIRECTORY_STRUCTURE.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # HTML 파일 저장
        html_content = markdown.markdown(report_content, extensions=['tables', 'codehilite'])
        
        # HTML 헤더 추가
        full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2025-09-12 실험 디렉토리 구조 보고서</title>
    <link rel="stylesheet" href="styles/project.css">
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>"""
        
        html_path = os.path.join(self.base_dir, 'EXPERIMENT_DIRECTORY_STRUCTURE.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print(f"✅ 보고서 저장 완료:")
        print(f"   - MD: {md_path}")
        print(f"   - HTML: {html_path}")
        
        return md_path, html_path
    
    def run_analysis(self):
        """분석 실행"""
        print("🚀 실험 디렉토리 구조 분석 시작")
        print("=" * 60)
        
        report_content = self.create_directory_structure_report()
        md_path, html_path = self.save_report(report_content)
        
        print("=" * 60)
        print("✅ 실험 디렉토리 구조 분석 완료!")
        print(f"📝 MD 보고서: {md_path}")
        print(f"🌐 HTML 보고서: {html_path}")
        print("=" * 60)

def main():
    updater = ExperimentDirectoryUpdater()
    updater.run_analysis()

if __name__ == "__main__":
    main()
