#!/bin/bash
# Phase-A: Device Calibration 실행 스크립트

echo "=== Phase-A: Device Calibration (2025-09-08) ==="
echo "디바이스 I/O 성능 측정을 시작합니다."
echo

cd phase-a
python3 device_calibration.py

echo
echo "Phase-A 완료! 결과를 확인하세요."
