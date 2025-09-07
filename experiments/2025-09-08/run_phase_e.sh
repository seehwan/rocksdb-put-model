#!/bin/bash
# Phase-E: Sensitivity Analysis 실행 스크립트

echo "=== Phase-E: Sensitivity Analysis (2025-09-08) ==="
echo "v4 모델 민감도 분석을 시작합니다."
echo

cd phase-e
python3 sensitivity_analysis.py

echo
echo "Phase-E 완료! 결과를 확인하세요."
