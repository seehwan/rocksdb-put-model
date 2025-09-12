#!/usr/bin/env python3
"""
Phase 파일들에 링크를 추가하는 스크립트
"""

from pathlib import Path

def add_links_to_phase_file(phase_file, phase_name, phase_title, phase_description):
    """Phase 파일에 링크 섹션 추가"""
    
    # Phase별 이전/다음 Phase 설정
    phase_sequence = {
        'phase-c': {'prev': 'phase-b', 'next': 'phase-d', 'prev_title': 'FillRandom 성능 분석', 'next_title': '모델 검증'},
        'phase-d': {'prev': 'phase-c', 'next': 'phase-e', 'prev_title': '컴팩션 분석', 'next_title': '결과 종합'},
        'phase-e': {'prev': 'phase-d', 'next': 'phase-f', 'prev_title': '모델 검증', 'next_title': '보고서 생성'},
        'phase-f': {'prev': 'phase-e', 'next': None, 'prev_title': '결과 종합', 'next_title': None}
    }
    
    try:
        with open(phase_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 링크 섹션 생성
        links_section = f"""
        <div class="section">
            <div class="section-header">📁 관련 파일 및 링크</div>
            <div class="section-content">
                <div class="link-grid">
                    <a href="../README.html" class="link-card">
                        <h4>📖 실험 개요</h4>
                        <p>전체 실험 개요 및 목표</p>
                    </a>
                    <a href="../ENHANCED_EXPERIMENT_PLAN.html" class="link-card">
                        <h4>🚀 향상된 실험 계획서</h4>
                        <p>상세한 실험 설계 및 계획서</p>
                    </a>
                    <a href="../EXECUTION_GUIDE.html" class="link-card">
                        <h4>📋 실행 가이드</h4>
                        <p>단계별 실험 실행 방법</p>
                    </a>
                    <a href="../phase-a/PHASE_A_PLAN.html" class="link-card">
                        <h4>🔧 Phase-A</h4>
                        <p>Device Envelope 모델 구축</p>
                    </a>
                    <a href="../phase-b/PHASE_B_PLAN.html" class="link-card">
                        <h4>📊 Phase-B</h4>
                        <p>FillRandom 성능 분석</p>
                    </a>"""
        
        # 이전/다음 Phase 링크 추가
        if phase_name in phase_sequence:
            prev_phase = phase_sequence[phase_name]['prev']
            next_phase = phase_sequence[phase_name]['next']
            prev_title = phase_sequence[phase_name]['prev_title']
            next_title = phase_sequence[phase_name]['next_title']
            
            if prev_phase:
                links_section += f"""
                    <a href="../{prev_phase}/PHASE_{prev_phase[-1].upper()}_PLAN.html" class="link-card">
                        <h4>⬅️ 이전 Phase</h4>
                        <p>{prev_title}</p>
                    </a>"""
            
            if next_phase:
                links_section += f"""
                    <a href="../{next_phase}/PHASE_{next_phase[-1].upper()}_PLAN.html" class="link-card">
                        <h4>다음 Phase ➡️</h4>
                        <p>{next_title}</p>
                    </a>"""
        
        # 실행 스크립트 링크 추가
        links_section += f"""
                    <a href="../scripts/run_phase_a.py" class="link-card">
                        <h4>🔧 Phase-A 실행</h4>
                        <p>Device Envelope 모델 구축 스크립트</p>
                    </a>
                    <a href="../scripts/run_phase_b.py" class="link-card">
                        <h4>📊 Phase-B 실행</h4>
                        <p>FillRandom 성능 분석 스크립트</p>
                    </a>
                </div>
            </div>
        </div>"""
        
        # footer 앞에 링크 섹션 추가
        content = content.replace('<div class="footer">', f'{links_section}\n\n        <div class="footer">')
        
        # 파일 저장
        with open(phase_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Added links to {phase_file}")
        return True
        
    except Exception as e:
        print(f"Error adding links to {phase_file}: {e}")
        return False

def main():
    """메인 함수"""
    base_dir = Path("/home/sslab/rocksdb-put-model/experiments/2025-09-12")
    
    # Phase별 설정
    phases = {
        'phase-c': ('Phase-C', '컴팩션 분석', 'Phase-B에서 수집된 로그를 기반으로 컴팩션 패턴을 상세히 분석하고, 레벨별 컴팩션 동작과 성능에 미치는 영향을 분석'),
        'phase-d': ('Phase-D', '모델 검증', '개발된 모델의 정확성과 신뢰성을 검증하고, 다양한 조건에서의 성능을 평가'),
        'phase-e': ('Phase-E', '결과 종합', '모든 실험 결과를 종합하여 최종 분석 및 결론을 도출'),
        'phase-f': ('Phase-F', '보고서 생성', '실험 결과를 바탕으로 최종 보고서 및 문서를 생성')
    }
    
    success_count = 0
    for phase, (title, short_desc, description) in phases.items():
        phase_file = base_dir / phase / f"PHASE_{phase[-1].lower()}_PLAN.html"
        
        if phase_file.exists():
            if add_links_to_phase_file(phase_file, phase, title, description):
                success_count += 1
        else:
            print(f"File not found: {phase_file}")
    
    print(f"Successfully added links to {success_count} phase files")

if __name__ == "__main__":
    main()
