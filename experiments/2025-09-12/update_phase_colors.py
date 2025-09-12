#!/usr/bin/env python3
"""
Phase별 색상을 추가하는 스크립트
"""

import os
from pathlib import Path

def update_phase_colors():
    """Phase별 색상 스타일 추가"""
    
    phase_colors = {
        'phase-c': ('#27ae60', '#229954', '컴팩션 분석'),
        'phase-d': ('#9b59b6', '#8e44ad', '모델 검증'),
        'phase-e': ('#e67e22', '#d35400', '결과 종합'),
        'phase-f': ('#34495e', '#2c3e50', '보고서 생성')
    }
    
    for phase, (color, gradient_color, title) in phase_colors.items():
        phase_file = Path(f"{phase}/PHASE_{phase[-1].upper()}_PLAN.html")
        
        if phase_file.exists():
            # 현재 파일 읽기
            with open(phase_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # CSS 링크 수정
            content = content.replace('href="styles.css"', 'href="../styles.css"')
            
            # 색상 스타일 추가
            color_style = f"""
    <style>
        .achievement-card, .contribution-card {{
            border-left-color: {color} !important;
        }}
        .header {{
            background: linear-gradient(135deg, {color} 0%, {gradient_color} 100%) !important;
        }}
        h1 {{
            color: {color} !important;
            border-bottom-color: {color} !important;
        }}
        h2 {{
            border-left-color: {color} !important;
        }}
        .link-card {{
            border-left-color: {color} !important;
        }}
        .section-header {{
            background: {color} !important;
        }}
        .footer {{
            border-top-color: {color} !important;
        }}
    </style>"""
            
            # </head> 태그 앞에 스타일 추가
            content = content.replace('</head>', f'{color_style}\n</head>')
            
            # 제목 수정
            content = content.replace(f'Phase-{phase[-1].upper()}: FillRandom 성능 분석 및 컴팩션 모니터링', f'Phase-{phase[-1].upper()}: {title}')
            
            # 파일 저장
            with open(phase_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Updated {phase_file} with color {color}")

if __name__ == "__main__":
    update_phase_colors()
