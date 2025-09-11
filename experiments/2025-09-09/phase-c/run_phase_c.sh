#!/bin/bash
# Phase-C: Per-Level WAF 분석 실행 스크립트
# 실행일: 2025-09-05

echo "=== Phase-C: Per-Level WAF 분석 시작 ==="
echo "LOG 파일: /rocksdb/data/LOG"
echo "결과 디렉토리: experiments/2025-09-09/phase-c/phase-c-results/"
echo ""

# 결과 디렉토리 생성
mkdir -p experiments/2025-09-09/phase-c/phase-c-results

# 1. WAF 분석 실행
echo "1. WAF 분석 실행 중..."
python3 scripts/waf_analyzer.py --log /rocksdb/data/LOG \
  --user-mb 1000 --out-dir experiments/2025-09-09/phase-c/phase-c-results --plot

# 2. Per-Level Breakdown 실행
echo "2. Per-Level Breakdown 실행 중..."
python3 scripts/per_level_breakdown.py --log /rocksdb/data/LOG \
  --output-dir experiments/2025-09-09/phase-c/phase-c-results

# 3. 결과 확인
echo "3. 결과 확인..."
echo "생성된 파일들:"
ls -la experiments/2025-09-09/phase-c/phase-c-results/

echo ""
echo "=== Phase-C 완료 ==="
echo "결과 파일 위치: experiments/2025-09-09/phase-c/phase-c-results/"
