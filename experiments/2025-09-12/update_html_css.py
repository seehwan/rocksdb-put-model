#!/usr/bin/env python3
"""
HTML 파일들을 프로젝트 CSS를 사용하도록 수정하는 스크립트
"""

import os
import re
from pathlib import Path

def update_html_file(file_path):
    """HTML 파일을 프로젝트 CSS를 사용하도록 수정"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # <style> 태그를 <link rel="stylesheet" href="styles.css">로 교체
        style_pattern = r'<style>.*?</style>'
        new_content = re.sub(style_pattern, '<link rel="stylesheet" href="styles.css">', content, flags=re.DOTALL)
        
        # 클래스명을 프로젝트 CSS에 맞게 변경
        class_replacements = {
            'research-questions': 'achievement-grid',
            'question-card': 'achievement-card',
            'experiment-grid': 'contribution-grid',
            'experiment-card': 'contribution-card',
            'hero-box': 'header',
            'highlight-box': 'info-box',
            'warning-box': 'warning-box',
            'error-box': 'warning-box',
            'code-block': 'code-block',
            'directory-structure': 'file-tree',
            'timeline': 'toc',
            'timeline-item': 'toc',
            'timeline-content': 'toc',
            'process-flow': 'link-grid',
            'flow-step': 'link-card',
            'execution-flow': 'link-grid',
            'flow-card': 'link-card',
            'key-features': 'achievement-grid',
            'feature-card': 'achievement-card',
            'overview-grid': 'achievement-grid',
            'overview-card': 'achievement-card',
            'step-box': 'highlight-box',
            'logging-config': 'info-box'
        }
        
        for old_class, new_class in class_replacements.items():
            new_content = new_content.replace(f'class="{old_class}"', f'class="{new_class}"')
            new_content = new_content.replace(f"class='{old_class}'", f"class='{new_class}'")
        
        # h4를 h3로 변경 (achievement-card와 contribution-card의 경우)
        new_content = re.sub(r'<h4>([^<]+)</h4>', r'<h3>\1</h3>', new_content)
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Updated: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """메인 함수"""
    base_dir = Path("/home/sslab/rocksdb-put-model/experiments/2025-09-12")
    
    # HTML 파일 찾기
    html_files = list(base_dir.rglob("*.html"))
    
    print(f"Found {len(html_files)} HTML files")
    
    success_count = 0
    for html_file in html_files:
        if update_html_file(html_file):
            success_count += 1
    
    print(f"Successfully updated {success_count}/{len(html_files)} files")

if __name__ == "__main__":
    main()
