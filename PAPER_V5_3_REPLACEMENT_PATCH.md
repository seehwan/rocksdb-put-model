# 논문 V5.3 완전 교체 작업 계획

## 📍 현재 상황

- **Section 4**: Line 252-503 (252 lines)
- **내용**: v1, v2, v3 상세 설명
- **교체**: V5.3 모델로 완전 교체

## 🎯 작업 계획

### Step 1: 기존 내용 확인

Section 4의 범위:
- Line 252: `\section{Dynamic Put-Rate Model}`
- Line 257-296: Model Evolution (v1-v3)
- Line 297-454: Core Mathematical Framework
- Line 455-503: Model Simulation Algorithm

### Step 2: 교체할 내용

**삭제할 섹션**:
- Line 255-296: v1, v2, v3 진화 설명
- Line 349-454: v3의 상세 수식 (일부 유지 가능)

**유지할 부분**:
- Notation and symbol definitions (일부)
- Algorithm structure (V5.3으로 대체)

**새로 추가**:
- V5.3 Core Philosophy
- V5.3 Mathematical Framework
- V5.3 Algorithm
- V5.3 Validation Results

### Step 3: 파일 수정

**방식 선택**:
1. 직접 search_replace로 큰 블록 교체
2. 새 파일 생성 후 manual merge
3. Interactive 수정 (사용자 확인 후)

## ⚠️ 주의사항

1. **LaTeX 구조 유지**: `\section`, `\subsection` 등 레이블 확인
2. **참조 유지**: 다른 섹션에서 Section 4를 참조하는 부분 확인
3. **Figure/Table 레이블**: 기존 그래프 레이블 확인
4. **Abstract 수정**: V5.3 언급 추가 필요
5. **Conclusion 수정**: V5.3 결과 반영 필요

## 🚀 실행 옵션

**Option A**: 전체 Section 4 삭제 후 V5.3 내용으로 교체
- 장점: 깔끔함, 일관성
- 단점: 한 번에 큰 변경

**Option B**: 단계별 수정 (권장)
1. Section 4.1 (Model Evolution) 삭제
2. Section 4.2 추가 (V5.3 Core)
3. Section 4.3 추가 (V5.3 Algorithm)
4. 기존 4.3 삭제
5. 점진적 테스트

어떤 방식으로 진행할까요?

