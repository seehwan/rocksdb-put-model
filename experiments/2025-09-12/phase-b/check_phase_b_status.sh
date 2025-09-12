#!/bin/bash

# Phase-B 상태 확인 스크립트
# 목적: 백그라운드 실행 중인 Phase-B 실험의 상태를 확인

PID_FILE="phase_b.pid"
LOG_FILE="phase_b_background.log"

echo "=== Phase-B 상태 확인 ==="
echo "확인 시간: $(date)"
echo ""

# PID 파일 확인
if [ ! -f "$PID_FILE" ]; then
    echo "❌ PID 파일이 없습니다. Phase-B가 실행되지 않았거나 완료되었습니다."
    exit 0
fi

PID=$(cat $PID_FILE)
echo "📋 PID: $PID"

# 프로세스 상태 확인
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Phase-B가 실행 중입니다!"
    
    # 프로세스 정보
    echo ""
    echo "📊 프로세스 정보:"
    ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
    
    # 로그 파일 확인
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "📄 최근 로그 (마지막 10줄):"
        echo "----------------------------------------"
        tail -10 $LOG_FILE
        echo "----------------------------------------"
        
        echo ""
        echo "📈 로그 파일 크기: $(du -h $LOG_FILE | cut -f1)"
        echo "📅 로그 파일 수정 시간: $(stat -c %y $LOG_FILE)"
    fi
    
    # RocksDB 데이터베이스 크기 확인
    if [ -d "/rocksdb/data" ]; then
        echo ""
        echo "💾 데이터베이스 크기:"
        du -sh /rocksdb/data 2>/dev/null || echo "데이터베이스 디렉토리에 접근할 수 없습니다."
    fi
    
    # LOG 파일 크기 확인
    if [ -f "/rocksdb/data/LOG" ]; then
        echo ""
        echo "📄 RocksDB LOG 파일 크기:"
        du -sh /rocksdb/data/LOG*
    fi
    
else
    echo "❌ Phase-B 프로세스가 실행되지 않습니다."
    
    # 로그 파일 확인
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "📄 마지막 로그 확인:"
        echo "----------------------------------------"
        tail -20 $LOG_FILE
        echo "----------------------------------------"
        
        # 완료 메시지 확인
        if grep -q "Phase-B 완료" $LOG_FILE; then
            echo ""
            echo "✅ Phase-B가 정상적으로 완료되었습니다!"
        else
            echo ""
            echo "⚠️ Phase-B가 비정상적으로 종료되었을 수 있습니다."
        fi
    fi
    
    # PID 파일 정리
    echo ""
    echo "🧹 PID 파일을 정리합니다."
    rm -f $PID_FILE
fi

echo ""
echo "🔍 유용한 명령어:"
echo "  전체 로그 보기: cat $LOG_FILE"
echo "  실시간 로그: tail -f $LOG_FILE"
echo "  프로세스 강제 종료: kill -9 $PID"
