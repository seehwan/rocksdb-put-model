#!/bin/bash
# 2025-09-08 실험 전체 실행 스크립트

echo "=== RocksDB Put Model 실험 (2025-09-08) ==="
echo "전체 실험을 순차적으로 실행합니다."
echo

# 실행 순서
phases=("A" "B" "C" "D" "E")

for phase in "${phases[@]}"; do
    echo "=========================================="
    echo "Phase-$phase 실행 중..."
    echo "=========================================="
    
    if [ -f "run_phase_${phase,,}.sh" ]; then
        chmod +x "run_phase_${phase,,}.sh"
        "./run_phase_${phase,,}.sh"
        
        if [ $? -eq 0 ]; then
            echo "✅ Phase-$phase 완료"
        else
            echo "❌ Phase-$phase 실패"
            echo "실험을 중단합니다."
            exit 1
        fi
    else
        echo "⚠️  Phase-$phase 스크립트를 찾을 수 없습니다."
    fi
    
    echo
done

echo "🎉 모든 Phase가 성공적으로 완료되었습니다!"
echo "결과를 확인하세요."
