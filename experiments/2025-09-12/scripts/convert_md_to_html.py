#!/usr/bin/env python3
"""
MD 파일을 HTML로 변환하는 스크립트
"""

import os
import sys
import markdown
import json
from datetime import datetime

class MDToHTMLConverter:
    def __init__(self, base_dir="/home/sslab/rocksdb-put-model/experiments/2025-09-12"):
        self.base_dir = base_dir
        self.results_dir = os.path.join(base_dir, "final_analysis_results")
        
    def convert_md_to_html(self, md_file_path, html_file_path):
        """MD 파일을 HTML로 변환"""
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Markdown을 HTML로 변환
            html_content = markdown.markdown(md_content, extensions=['tables', 'codehilite', 'fenced_code'])
            
            # HTML 템플릿 생성
            full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RocksDB Put-Rate Model Comprehensive Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 10px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
        }}
        .success {{
            background-color: #d4edda;
            padding: 10px;
            border-left: 4px solid #28a745;
            margin: 10px 0;
        }}
        .info {{
            background-color: #d1ecf1;
            padding: 10px;
            border-left: 4px solid #17a2b8;
            margin: 10px 0;
        }}
        .warning {{
            background-color: #fff3cd;
            padding: 10px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
        <div class="footer">
            <p>Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>RocksDB Put-Rate Model Comprehensive Analysis</p>
        </div>
    </div>
</body>
</html>"""
            
            # HTML 파일 저장
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            print(f"✅ HTML 변환 완료: {os.path.basename(html_file_path)}")
            return True
            
        except Exception as e:
            print(f"❌ HTML 변환 실패: {e}")
            return False
    
    def find_all_md_files(self):
        """모든 MD 파일 찾기"""
        md_files = []
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
        
        return md_files
    
    def convert_all_md_files(self):
        """모든 MD 파일을 HTML로 변환"""
        print("📝 모든 MD 파일을 HTML로 변환 중...")
        
        md_files = self.find_all_md_files()
        converted_count = 0
        
        for md_file in md_files:
            # HTML 파일 경로 생성
            html_file = md_file.replace('.md', '.html')
            
            # 변환 실행
            if self.convert_md_to_html(md_file, html_file):
                converted_count += 1
        
        print(f"✅ 총 {converted_count}개 MD 파일을 HTML로 변환 완료")
        return converted_count

def main():
    converter = MDToHTMLConverter()
    converter.convert_all_md_files()

if __name__ == "__main__":
    main()
