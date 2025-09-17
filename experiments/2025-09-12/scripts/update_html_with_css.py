#!/usr/bin/env python3
"""
HTML 파일들을 프로젝트 CSS로 업데이트
모든 HTML 파일에 통일된 CSS 스타일 적용
"""

import os
import re
from pathlib import Path

class HTMLCSSUpdater:
    def __init__(self):
        self.base_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12'
        self.css_file = os.path.join(self.base_dir, 'styles', 'project.css')
        self.html_files = []
        
    def find_html_files(self):
        """HTML 파일들 찾기"""
        print("📁 HTML 파일들 검색 중...")
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.html'):
                    html_path = os.path.join(root, file)
                    self.html_files.append(html_path)
        
        print(f"✅ {len(self.html_files)} 개의 HTML 파일 발견")
        return self.html_files
    
    def read_css_content(self):
        """CSS 파일 내용 읽기"""
        try:
            with open(self.css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            print("✅ CSS 파일 로드 완료")
            return css_content
        except Exception as e:
            print(f"❌ CSS 파일 로드 실패: {e}")
            return None
    
    def update_html_file(self, html_path, css_content):
        """개별 HTML 파일 업데이트"""
        try:
            # HTML 파일 읽기
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 기존 <style> 태그 제거
            html_content = re.sub(r'<style>.*?</style>', '', html_content, flags=re.DOTALL)
            
            # CSS 링크 추가 또는 업데이트
            css_link = f'<link rel="stylesheet" href="{self.get_relative_css_path(html_path)}">'
            
            # <head> 태그 찾기
            head_match = re.search(r'<head>', html_content, re.IGNORECASE)
            if head_match:
                # <head> 태그 다음에 CSS 링크 추가
                insert_pos = head_match.end()
                html_content = html_content[:insert_pos] + f'\n    {css_link}\n' + html_content[insert_pos:]
            else:
                # <head> 태그가 없으면 <html> 태그 다음에 추가
                html_match = re.search(r'<html[^>]*>', html_content, re.IGNORECASE)
                if html_match:
                    insert_pos = html_match.end()
                    html_content = html_content[:insert_pos] + f'\n<head>\n    {css_link}\n</head>\n' + html_content[insert_pos:]
                else:
                    # HTML 태그도 없으면 맨 앞에 추가
                    html_content = f'<!DOCTYPE html>\n<html>\n<head>\n    {css_link}\n</head>\n<body>\n{html_content}\n</body>\n</html>'
            
            # 컨테이너 div 추가 (body 내용을 감싸기)
            if '<div class="container">' not in html_content:
                # <body> 태그 다음에 컨테이너 div 추가
                body_match = re.search(r'<body[^>]*>', html_content, re.IGNORECASE)
                if body_match:
                    insert_pos = body_match.end()
                    html_content = html_content[:insert_pos] + '\n    <div class="container">\n' + html_content[insert_pos:]
                    
                    # </body> 태그 전에 컨테이너 div 닫기
                    body_close_match = re.search(r'</body>', html_content, re.IGNORECASE)
                    if body_close_match:
                        insert_pos = body_close_match.start()
                        html_content = html_content[:insert_pos] + '    </div>\n' + html_content[insert_pos:]
            
            # 특별한 클래스 추가
            html_content = self.add_special_classes(html_content)
            
            # HTML 파일 저장
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ {html_path} 업데이트 완료")
            return True
            
        except Exception as e:
            print(f"❌ {html_path} 업데이트 실패: {e}")
            return False
    
    def get_relative_css_path(self, html_path):
        """HTML 파일에서 CSS 파일까지의 상대 경로 계산"""
        html_dir = os.path.dirname(html_path)
        css_dir = os.path.dirname(self.css_file)
        
        # 상대 경로 계산
        try:
            relative_path = os.path.relpath(self.css_file, html_dir)
            return relative_path
        except:
            # 상대 경로 계산 실패시 절대 경로 사용
            return self.css_file
    
    def add_special_classes(self, html_content):
        """특별한 클래스 추가"""
        # 테이블 행에 순위 클래스 추가
        html_content = re.sub(
            r'<tr[^>]*>.*?<td[^>]*>(\d+)</td>.*?</tr>',
            lambda m: self.add_rank_class(m.group(0), m.group(1)),
            html_content,
            flags=re.DOTALL
        )
        
        # 성능 지표에 클래스 추가
        html_content = re.sub(
            r'(\d+\.?\d*%)',
            lambda m: self.add_performance_class(m.group(1)),
            html_content
        )
        
        # Phase 표시에 클래스 추가
        html_content = re.sub(
            r'Phase-([A-E])',
            lambda m: f'<span class="phase-indicator phase-{m.group(1).lower()}">Phase-{m.group(1)}</span>',
            html_content
        )
        
        return html_content
    
    def add_rank_class(self, tr_content, rank):
        """순위에 따른 클래스 추가"""
        rank_num = int(rank)
        if rank_num == 1:
            return tr_content.replace('<tr', '<tr class="rank-1"')
        elif rank_num == 2:
            return tr_content.replace('<tr', '<tr class="rank-2"')
        elif rank_num == 3:
            return tr_content.replace('<tr', '<tr class="rank-3"')
        return tr_content
    
    def add_performance_class(self, percentage):
        """성능 지표에 클래스 추가"""
        try:
            value = float(percentage.replace('%', ''))
            if value >= 80:
                return f'<span class="performance-excellent">{percentage}</span>'
            elif value >= 60:
                return f'<span class="performance-good">{percentage}</span>'
            elif value >= 40:
                return f'<span class="performance-fair">{percentage}</span>'
            else:
                return f'<span class="performance-poor">{percentage}</span>'
        except:
            return percentage
    
    def update_all_html_files(self):
        """모든 HTML 파일 업데이트"""
        print("🚀 HTML 파일 CSS 업데이트 시작")
        print("=" * 60)
        
        # HTML 파일들 찾기
        self.find_html_files()
        
        # CSS 내용 읽기
        css_content = self.read_css_content()
        if not css_content:
            print("❌ CSS 파일을 읽을 수 없습니다.")
            return
        
        # 각 HTML 파일 업데이트
        success_count = 0
        for html_path in self.html_files:
            if self.update_html_file(html_path, css_content):
                success_count += 1
        
        print("=" * 60)
        print(f"✅ HTML 파일 CSS 업데이트 완료!")
        print(f"📊 총 {len(self.html_files)} 개 파일 중 {success_count} 개 성공")
        print(f"📁 CSS 파일: {self.css_file}")
        print("=" * 60)
    
    def create_css_link_file(self):
        """CSS 링크 파일 생성"""
        css_link_content = f"""/* CSS Link for HTML Files */
/* This file contains the relative path to project.css */

/* To use this CSS in HTML files, add the following line in the <head> section: */
/* <link rel="stylesheet" href="styles/project.css"> */

/* Or use the relative path from your HTML file location to this CSS file */
"""
        
        css_link_file = os.path.join(self.base_dir, 'styles', 'css_link.txt')
        with open(css_link_file, 'w', encoding='utf-8') as f:
            f.write(css_link_content)
        
        print(f"✅ CSS 링크 파일 생성: {css_link_file}")

def main():
    updater = HTMLCSSUpdater()
    updater.update_all_html_files()
    updater.create_css_link_file()

if __name__ == "__main__":
    main()
