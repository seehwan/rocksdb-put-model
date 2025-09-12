#!/bin/bash

# Phase-B 중단 스크립트
# 목적: 실행 중인 Phase-B 실험을 안전하게 중단

PID_FILE="phase_b.pid"
LOG_FILE="phase_b_background.log"

echo "=== Phase-B 중단 스크립트 ==="
echo "중단 시간: $(date)"
echo ""

# PID 파일 확인
if [ ! -f "$PID_FILE" ]; then
    echo "❌ PID 파일이 없습니다. Phase-B가 실행되지 않았거나 이미 완료되었습니다."
    exit 0
fi

PID=$(cat $PID_FILE)
echo "📋 PID: $PID"

# 프로세스 상태 확인
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Phase-B 프로세스가 실행 중입니다."
    
    # 프로세스 정보 출력
    echo ""
    echo "📊 프로세스 정보:"
    ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
    
    echo ""
    echo "⚠️ Phase-B를 중단하시겠습니까? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        echo "🛑 Phase-B를 중단합니다..."
        
        # SIGTERM으로 정상 종료 시도
        kill $PID
        echo "SIGTERM 신호를 보냈습니다. 프로세스가 정상 종료될 때까지 기다립니다..."
        
        # 10초 대기
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "✅ 프로세스가 정상적으로 종료되었습니다."
                break
            fi
            echo "대기 중... ($i/10)"
            sleep 1
        done
        
        # 여전히 실행 중이면 SIGKILL
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️ 프로세스가 정상 종료되지 않았습니다. 강제 종료합니다."
            kill -9 $PID
            sleep 2
            
            if ps -p $PID > /dev/null 2>&1; then
                echo "❌ 프로세스 종료에 실패했습니다."
            else
                echo "✅ 프로세스가 강제 종료되었습니다."
            fi
        fi
        
        # PID 파일 삭제
        rm -f $PID_FILE
        echo "🧹 PID 파일을 삭제했습니다."
        
        # 로그에 중단 기록
        echo "" >> $LOG_FILE
        echo "=== Phase-B 수동 중단 ===" >> $LOG_FILE
        echo "중단 시간: $(date)" >> $LOG_FILE
        echo "중단자: $(whoami)" >> $LOG_FILE
        
    else
        echo "❌ 중단을 취소했습니다."
        exit 0
    fi
    
else
    echo "❌ Phase-B 프로세스가 실행되지 않습니다."
    
    # PID 파일 정리
    echo "🧹 PID 파일을 정리합니다."
    rm -f $PID_FILE
fi

echo ""
echo "📄 현재 상태:"
echo "  PID 파일: $([ -f "$PID_FILE" ] && echo "존재" || echo "없음")"
echo "  로그 파일: $([ -f "$LOG_FILE" ] && echo "존재 ($(du -h $LOG_FILE | cut -f1))" || echo "없음")"

echo ""
echo "✅ Phase-B 중단 완료!"
