#!/usr/bin/env python3
"""
README.md를 HTML로 변환
프로젝트 루트의 README.md를 HTML로 변환하여 통일된 CSS 스타일 적용
"""

import os
import markdown
from datetime import datetime

def convert_readme_to_html():
    """README.md를 HTML로 변환"""
    print("🔄 README.md를 HTML로 변환 중...")
    
    # README.md 파일 경로
    readme_md_path = '/home/sslab/rocksdb-put-model/README.md'
    readme_html_path = '/home/sslab/rocksdb-put-model/README.html'
    
    try:
        # README.md 파일 읽기
        with open(readme_md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Markdown을 HTML로 변환
        html_content = markdown.markdown(md_content, extensions=['tables', 'codehilite', 'toc'])
        
        # HTML 헤더 추가
        full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RocksDB Put-Rate Model</title>
    <link rel="stylesheet" href="styles/project.css">
    <style>
        /* 추가 스타일링 */
        .toc {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .toc h2 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        
        .toc ul {{
            margin: 0;
            padding-left: 20px;
        }}
        
        .toc li {{
            margin: 5px 0;
        }}
        
        .toc a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        .toc a:hover {{
            color: #2980b9;
            text-decoration: underline;
        }}
        
        /* 코드 블록 스타일링 */
        pre {{
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #e74c3c;
            font-size: 0.9em;
        }}
        
        /* 테이블 스타일링 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            font-weight: bold;
            padding: 15px 12px;
            text-align: left;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
            transition: background-color 0.3s ease;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        tr:nth-child(even):hover {{
            background-color: #e8f4f8;
        }}
        
        /* 순위별 색상 */
        .rank-1 {{
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .rank-2 {{
            background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .rank-3 {{
            background: linear-gradient(135deg, #cd7f32, #daa520);
            font-weight: bold;
            color: white;
        }}
        
        /* 성능 지표 색상 */
        .performance-excellent {{
            color: #27ae60;
            font-weight: bold;
            background-color: #d5f4e6;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        .performance-good {{
            color: #2980b9;
            font-weight: bold;
            background-color: #d6eaf8;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        .performance-fair {{
            color: #f39c12;
            font-weight: bold;
            background-color: #fef9e7;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        .performance-poor {{
            color: #e74c3c;
            font-weight: bold;
            background-color: #fadbd8;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        /* Phase 표시 */
        .phase-indicator {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 5px;
        }}
        
        .phase-a {{
            background-color: #e8f4f8;
            color: #2980b9;
            border: 2px solid #3498db;
        }}
        
        .phase-b {{
            background-color: #d5f4e6;
            color: #27ae60;
            border: 2px solid #2ecc71;
        }}
        
        .phase-c {{
            background-color: #fef9e7;
            color: #f39c12;
            border: 2px solid #f1c40f;
        }}
        
        .phase-d {{
            background-color: #fadbd8;
            color: #e74c3c;
            border: 2px solid #e67e22;
        }}
        
        .phase-e {{
            background-color: #e8daef;
            color: #8e44ad;
            border: 2px solid #9b59b6;
        }}
        
        /* 모델 타입 표시 */
        .model-enhanced {{
            background-color: #d6eaf8;
            color: #2980b9;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .model-temporal {{
            background-color: #e8daef;
            color: #8e44ad;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .model-standard {{
            background-color: #ecf0f1;
            color: #7f8c8d;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        /* 반응형 디자인 */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
            
            table {{
                font-size: 0.9em;
            }}
            
            th, td {{
                padding: 8px 6px;
            }}
        }}
        
        /* 인쇄 스타일 */
        @media print {{
            body {{
                background-color: white;
                color: black;
            }}
            
            .container {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}
            
            table {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}
            
            .rank-1, .rank-2, .rank-3 {{
                background: none;
                color: black;
                font-weight: bold;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
        
        <hr style="margin: 40px 0; border: none; border-top: 2px solid #ecf0f1;">
        
        <div style="text-align: center; color: #7f8c8d; font-size: 0.9em;">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>RocksDB Put-Rate Model Project</p>
        </div>
    </div>
</body>
</html>"""
        
        # HTML 파일 저장
        with open(readme_html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print(f"✅ README.html 생성 완료: {readme_html_path}")
        return True
        
    except Exception as e:
        print(f"❌ README.html 생성 실패: {e}")
        return False

def main():
    convert_readme_to_html()

if __name__ == "__main__":
    main()
