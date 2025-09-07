#!/bin/bash
# Phase-C: WAF Analysis 실행 스크립트

echo "=== Phase-C: WAF Analysis (2025-09-08) ==="
echo "Write Amplification 분석을 시작합니다."
echo

cd phase-c
python3 manual_waf_analysis.py

echo
echo "Phase-C 완료! 결과를 확인하세요."
