#!/bin/bash
# 2025-09-09 새로운 실험: 모든 Phase 실행 스크립트
# 실행일: 2025-09-09

echo "🚀 2025-09-09 새로운 실험 시작!"
echo "=================================="
echo ""

# 실험 시작 시간 기록
START_TIME=$(date)
echo "실험 시작 시간: $START_TIME"
echo ""

# Phase-A: 디바이스 캘리브레이션
echo "📊 Phase-A: 디바이스 캘리브레이션 시작"
echo "----------------------------------------"
chmod +x experiments/2025-09-09/phase-a/run_phase_a.sh
./experiments/2025-09-09/phase-a/run_phase_a.sh

if [ $? -eq 0 ]; then
    echo "✅ Phase-A 완료"
else
    echo "❌ Phase-A 실패"
    exit 1
fi
echo ""

# Phase-B: RocksDB 벤치마크
echo "🔧 Phase-B: RocksDB 벤치마크 시작"
echo "----------------------------------"
chmod +x experiments/2025-09-09/phase-b/run_phase_b.sh
./experiments/2025-09-09/phase-b/run_phase_b.sh

if [ $? -eq 0 ]; then
    echo "✅ Phase-B 완료"
else
    echo "❌ Phase-B 실패"
    exit 1
fi
echo ""

# Phase-C: Per-Level WAF 분석
echo "📈 Phase-C: Per-Level WAF 분석 시작"
echo "------------------------------------"
chmod +x experiments/2025-09-09/phase-c/run_phase_c.sh
./experiments/2025-09-09/phase-c/run_phase_c.sh

if [ $? -eq 0 ]; then
    echo "✅ Phase-C 완료"
else
    echo "❌ Phase-C 실패"
    exit 1
fi
echo ""

# Phase-D: v4 모델 검증
echo "🎯 Phase-D: v4 모델 검증 시작"
echo "------------------------------"
cd experiments/2025-09-09/phase-d
python3 v4_validation.py
cd /home/sslab/rocksdb-put-model

if [ $? -eq 0 ]; then
    echo "✅ Phase-D 완료"
else
    echo "❌ Phase-D 실패"
    exit 1
fi
echo ""

# Phase-E: 민감도 분석
echo "🔍 Phase-E: 민감도 분석 시작"
echo "-----------------------------"
cd experiments/2025-09-09/phase-e
python3 sensitivity_analysis.py
cd /home/sslab/rocksdb-put-model

if [ $? -eq 0 ]; then
    echo "✅ Phase-E 완료"
else
    echo "❌ Phase-E 실패"
    exit 1
fi
echo ""

# 실험 완료 시간 기록
END_TIME=$(date)
echo "🎉 2025-09-09 새로운 실험 완료!"
echo "=================================="
echo "실험 시작 시간: $START_TIME"
echo "실험 완료 시간: $END_TIME"
echo ""

# 결과 요약
echo "📊 실험 결과 요약"
echo "------------------"
echo "Phase-A: 디바이스 캘리브레이션 - experiments/2025-09-09/phase-a/"
echo "Phase-B: RocksDB 벤치마크 - experiments/2025-09-09/phase-b/"
echo "Phase-C: Per-Level WAF 분석 - experiments/2025-09-09/phase-c/"
echo "Phase-D: v4 모델 검증 - experiments/2025-09-09/phase-d/"
echo "Phase-E: 민감도 분석 - experiments/2025-09-09/phase-e/"
echo ""

echo "🔍 결과 확인을 위해 각 phase 디렉토리를 확인하세요."
