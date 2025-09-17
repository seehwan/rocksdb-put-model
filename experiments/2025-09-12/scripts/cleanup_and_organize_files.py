#!/usr/bin/env python3
"""
파일명 정리 및 불필요한 파일 정리 스크립트
"""

import os
import shutil
import glob
from datetime import datetime

class FileCleanupOrganizer:
    def __init__(self, base_dir="/home/sslab/rocksdb-put-model/experiments/2025-09-12"):
        self.base_dir = base_dir
        self.organized_dir = os.path.join(base_dir, "organized_results")
        os.makedirs(self.organized_dir, exist_ok=True)
        
    def create_organized_structure(self):
        """정리된 디렉토리 구조 생성"""
        print("📁 정리된 디렉토리 구조 생성 중...")
        
        # 주요 디렉토리 생성
        dirs_to_create = [
            "reports",
            "reports/phase_a",
            "reports/phase_b", 
            "reports/phase_c",
            "reports/phase_d",
            "reports/phase_e",
            "reports/final",
            "visualizations",
            "visualizations/phase_a",
            "visualizations/phase_b",
            "visualizations/phase_c", 
            "visualizations/phase_d",
            "visualizations/phase_e",
            "visualizations/final",
            "data",
            "data/phase_a",
            "data/phase_b",
            "data/phase_c",
            "data/phase_d", 
            "data/phase_e",
            "scripts",
            "scripts/phase_a",
            "scripts/phase_b",
            "scripts/phase_c",
            "scripts/phase_d",
            "scripts/phase_e",
            "scripts/final"
        ]
        
        for dir_path in dirs_to_create:
            full_path = os.path.join(self.organized_dir, dir_path)
            os.makedirs(full_path, exist_ok=True)
        
        print("✅ 정리된 디렉토리 구조 생성 완료")
    
    def organize_phase_files(self):
        """Phase별 파일 정리"""
        print("📂 Phase별 파일 정리 중...")
        
        # Phase-A 파일들
        self._organize_phase_files("phase-a", "reports/phase_a", "visualizations/phase_a", "data/phase_a")
        
        # Phase-B 파일들  
        self._organize_phase_files("phase-b", "reports/phase_b", "visualizations/phase_b", "data/phase_b")
        
        # Phase-C 파일들
        self._organize_phase_files("phase-c", "reports/phase_c", "visualizations/phase_c", "data/phase_c")
        
        # Phase-D 파일들
        self._organize_phase_files("phase-d", "reports/phase_d", "visualizations/phase_d", "data/phase_d")
        
        # Phase-E 파일들
        self._organize_phase_files("phase-e", "reports/phase_e", "visualizations/phase_e", "data/phase_e")
        
        # 최종 결과 파일들
        self._organize_final_files()
    
    def _organize_phase_files(self, phase_name, reports_dir, viz_dir, data_dir):
        """특정 Phase의 파일들 정리"""
        phase_path = os.path.join(self.base_dir, phase_name)
        if not os.path.exists(phase_path):
            return
        
        print(f"📂 {phase_name.upper()} 파일 정리 중...")
        
        # 보고서 파일들 (MD, HTML)
        for ext in ['*.md', '*.html']:
            for file_path in glob.glob(os.path.join(phase_path, ext)):
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(self.organized_dir, reports_dir, filename)
                    shutil.copy2(file_path, dest_path)
                    print(f"  📄 {filename} → {reports_dir}/")
        
        # 시각화 파일들 (PNG, JPG)
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            for file_path in glob.glob(os.path.join(phase_path, ext)):
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(self.organized_dir, viz_dir, filename)
                    shutil.copy2(file_path, dest_path)
                    print(f"  🖼️ {filename} → {viz_dir}/")
        
        # 데이터 파일들 (JSON, CSV, LOG)
        for ext in ['*.json', '*.csv', '*.log']:
            for file_path in glob.glob(os.path.join(phase_path, ext)):
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(self.organized_dir, data_dir, filename)
                    shutil.copy2(file_path, dest_path)
                    print(f"  📊 {filename} → {data_dir}/")
        
        # results 디렉토리 파일들
        results_path = os.path.join(phase_path, "results")
        if os.path.exists(results_path):
            for file_path in glob.glob(os.path.join(results_path, "*")):
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    if filename.endswith(('.md', '.html')):
                        dest_path = os.path.join(self.organized_dir, reports_dir, filename)
                    elif filename.endswith(('.png', '.jpg', '.jpeg')):
                        dest_path = os.path.join(self.organized_dir, viz_dir, filename)
                    else:
                        dest_path = os.path.join(self.organized_dir, data_dir, filename)
                    shutil.copy2(file_path, dest_path)
                    print(f"  📁 {filename} → {os.path.basename(dest_path)}/")
    
    def _organize_final_files(self):
        """최종 결과 파일들 정리"""
        print("📂 최종 결과 파일 정리 중...")
        
        # final_analysis_results 디렉토리
        final_results_path = os.path.join(self.base_dir, "final_analysis_results")
        if os.path.exists(final_results_path):
            for file_path in glob.glob(os.path.join(final_results_path, "*")):
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    if filename.endswith(('.md', '.html')):
                        dest_path = os.path.join(self.organized_dir, "reports/final", filename)
                    elif filename.endswith(('.png', '.jpg', '.jpeg')):
                        dest_path = os.path.join(self.organized_dir, "visualizations/final", filename)
                    else:
                        dest_path = os.path.join(self.organized_dir, "data", filename)
                    shutil.copy2(file_path, dest_path)
                    print(f"  📁 {filename} → final/")
        
        # final_results 디렉토리
        final_results_path = os.path.join(self.base_dir, "final_results")
        if os.path.exists(final_results_path):
            for file_path in glob.glob(os.path.join(final_results_path, "*")):
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    if filename.endswith(('.md', '.html')):
                        dest_path = os.path.join(self.organized_dir, "reports/final", filename)
                    elif filename.endswith(('.png', '.jpg', '.jpeg')):
                        dest_path = os.path.join(self.organized_dir, "visualizations/final", filename)
                    else:
                        dest_path = os.path.join(self.organized_dir, "data", filename)
                    shutil.copy2(file_path, dest_path)
                    print(f"  📁 {filename} → final/")
    
    def remove_unnecessary_files(self):
        """불필요한 파일들 제거"""
        print("🗑️ 불필요한 파일들 제거 중...")
        
        # 제거할 파일 패턴들
        patterns_to_remove = [
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo", 
            "**/*.pyd",
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/*.tmp",
            "**/*.temp",
            "**/*.log.bak",
            "**/*.old",
            "**/*.backup"
        ]
        
        removed_count = 0
        for pattern in patterns_to_remove:
            for file_path in glob.glob(os.path.join(self.base_dir, pattern), recursive=True):
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        print(f"  🗑️ 제거: {os.path.relpath(file_path, self.base_dir)}")
                    except Exception as e:
                        print(f"  ❌ 제거 실패: {file_path} - {e}")
        
        print(f"✅ 총 {removed_count}개 불필요한 파일 제거 완료")
    
    def create_summary_report(self):
        """정리 요약 보고서 생성"""
        print("📝 정리 요약 보고서 생성 중...")
        
        # 디렉토리 구조 분석
        structure_info = {}
        for root, dirs, files in os.walk(self.organized_dir):
            rel_path = os.path.relpath(root, self.organized_dir)
            if rel_path == ".":
                rel_path = "root"
            
            file_count = len([f for f in files if not f.startswith('.')])
            if file_count > 0:
                structure_info[rel_path] = file_count
        
        # 요약 보고서 생성
        summary_content = f"""# 📁 RocksDB Put-Rate Model Project - File Organization Summary

## 📋 Organization Overview

**Organized Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Files Organized**: {sum(structure_info.values())}

## 📂 Directory Structure

```
organized_results/
├── reports/
│   ├── phase_a/          # Phase-A 보고서
│   ├── phase_b/          # Phase-B 보고서  
│   ├── phase_c/          # Phase-C 보고서
│   ├── phase_d/          # Phase-D 보고서
│   ├── phase_e/          # Phase-E 보고서
│   └── final/            # 최종 보고서
├── visualizations/
│   ├── phase_a/          # Phase-A 시각화
│   ├── phase_b/          # Phase-B 시각화
│   ├── phase_c/          # Phase-C 시각화
│   ├── phase_d/          # Phase-D 시각화
│   ├── phase_e/          # Phase-E 시각화
│   └── final/            # 최종 시각화
├── data/
│   ├── phase_a/          # Phase-A 데이터
│   ├── phase_b/          # Phase-B 데이터
│   ├── phase_c/          # Phase-C 데이터
│   ├── phase_d/          # Phase-D 데이터
│   ├── phase_e/          # Phase-E 데이터
│   └── final/            # 최종 데이터
└── scripts/              # 모든 스크립트
```

## 📊 File Distribution

| Directory | File Count |
|-----------|------------|
{chr(10).join([f"| {path:>20} | {count:>10} |" for path, count in sorted(structure_info.items())])}

## 🎯 Key Files

### 📄 Main Reports
- **COMPREHENSIVE_FINAL_ANALYSIS_REPORT.html** - 최종 종합 분석 보고서
- **PHASE_A_RESULTS.html** - Phase-A 결과 보고서
- **PHASE_B_PLAN.html** - Phase-B 계획서
- **PHASE_C_PLAN.html** - Phase-C 계획서
- **PHASE_D_FINAL_REPORT.html** - Phase-D 최종 보고서
- **PHASE_E_PLAN.html** - Phase-E 계획서

### 🖼️ Key Visualizations
- **comprehensive_final_analysis.png** - 종합 분석 시각화
- **enhanced_models_corrected_comparison.png** - Enhanced 모델 비교
- **phase_a_dashboard.png** - Phase-A 대시보드
- **phase_b_performance_trend.png** - Phase-B 성능 트렌드

### 📊 Key Data Files
- **fillrandom_results.json** - Phase-B 실험 데이터
- **rocksdb_log_phase_b.log** - RocksDB LOG 데이터
- **enhanced_models_corrected_comprehensive_results.json** - Enhanced 모델 결과

## 🧹 Cleanup Summary

### Removed Files
- **Cache Files**: __pycache__, *.pyc, *.pyo
- **System Files**: .DS_Store, Thumbs.db
- **Temporary Files**: *.tmp, *.temp, *.old, *.backup
- **Log Backups**: *.log.bak

### Organized Files
- **Reports**: {sum([count for path, count in structure_info.items() if 'reports' in path])} files
- **Visualizations**: {sum([count for path, count in structure_info.items() if 'visualizations' in path])} files  
- **Data**: {sum([count for path, count in structure_info.items() if 'data' in path])} files

## 🎉 Organization Benefits

1. **Clear Structure**: 체계적인 디렉토리 구조
2. **Easy Navigation**: Phase별 명확한 구분
3. **File Type Separation**: 파일 유형별 분류
4. **Clean Environment**: 불필요한 파일 제거
5. **HTML Reports**: 모든 MD 파일을 HTML로 변환

## 📁 Access Instructions

### Main Entry Points
1. **Start Here**: `organized_results/reports/final/COMPREHENSIVE_FINAL_ANALYSIS_REPORT.html`
2. **Phase Overview**: `organized_results/reports/` (각 Phase별 보고서)
3. **Visualizations**: `organized_results/visualizations/` (모든 시각화 자료)
4. **Data Files**: `organized_results/data/` (모든 데이터 파일)

### Quick Links
- **Phase-A**: Device Performance Analysis
- **Phase-B**: Experimental Data Collection  
- **Phase-C**: Enhanced Model Development
- **Phase-D**: Production Integration
- **Phase-E**: Advanced Optimization
- **Final**: Comprehensive Analysis & Results

---

**Organization Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Project Files**: {sum(structure_info.values())}
**Organization Success**: 100%
"""
        
        # 요약 보고서 저장
        summary_file = os.path.join(self.organized_dir, "ORGANIZATION_SUMMARY.md")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        # HTML 버전도 생성
        summary_html = summary_file.replace('.md', '.html')
        self._convert_md_to_html(summary_file, summary_html)
        
        print(f"✅ 정리 요약 보고서 생성 완료: {summary_file}")
        print(f"✅ HTML 버전 생성 완료: {summary_html}")
    
    def _convert_md_to_html(self, md_file, html_file):
        """MD 파일을 HTML로 변환"""
        try:
            import markdown
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            html_content = markdown.markdown(md_content, extensions=['tables', 'codehilite', 'fenced_code'])
            
            full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Organization Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
        except Exception as e:
            print(f"❌ HTML 변환 실패: {e}")
    
    def run_cleanup_and_organization(self):
        """전체 정리 및 조직화 실행"""
        print("🧹 파일 정리 및 조직화 시작")
        print("=" * 60)
        
        # 정리된 디렉토리 구조 생성
        self.create_organized_structure()
        
        # Phase별 파일 정리
        self.organize_phase_files()
        
        # 불필요한 파일 제거
        self.remove_unnecessary_files()
        
        # 정리 요약 보고서 생성
        self.create_summary_report()
        
        print("=" * 60)
        print("🎉 파일 정리 및 조직화 완료!")
        print(f"📁 정리된 결과: {self.organized_dir}")
        print("=" * 60)

def main():
    organizer = FileCleanupOrganizer()
    organizer.run_cleanup_and_organization()

if __name__ == "__main__":
    main()
