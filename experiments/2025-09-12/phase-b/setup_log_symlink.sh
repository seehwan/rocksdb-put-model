#!/bin/bash

# LOG 파일 심볼릭 링크 설정 스크립트
# 목적: LOG 파일을 실험 디렉토리에 생성하고 I/O 부하를 줄임

echo "=== LOG 파일 심볼릭 링크 설정 ==="
echo "설정 시간: $(date)"
echo ""

# 현재 디렉토리 확인
CURRENT_DIR=$(pwd)
LOG_DIR="$CURRENT_DIR/logs"
ROCKSDB_LOG_PATH="/rocksdb/data/LOG"

echo "📁 현재 디렉토리: $CURRENT_DIR"
echo "📁 LOG 디렉토리: $LOG_DIR"
echo "🔗 링크 대상: $ROCKSDB_LOG_PATH"

# LOG 디렉토리 생성
if [ ! -d "$LOG_DIR" ]; then
    echo "📁 LOG 디렉토리 생성: $LOG_DIR"
    mkdir -p "$LOG_DIR"
else
    echo "✅ LOG 디렉토리 이미 존재: $LOG_DIR"
fi

# 기존 링크 확인 및 제거
if [ -L "$ROCKSDB_LOG_PATH" ]; then
    echo "🔗 기존 심볼릭 링크 발견, 제거합니다."
    rm "$ROCKSDB_LOG_PATH"
fi

# 심볼릭 링크 생성
echo "🔗 심볼릭 링크 생성: $ROCKSDB_LOG_PATH -> $LOG_DIR/LOG"
ln -sf "$LOG_DIR/LOG" "$ROCKSDB_LOG_PATH"

# 링크 확인
if [ -L "$ROCKSDB_LOG_PATH" ]; then
    echo "✅ 심볼릭 링크 생성 성공!"
    echo "📋 링크 정보:"
    ls -la "$ROCKSDB_LOG_PATH"
    
    # 링크 대상 확인
    TARGET=$(readlink "$ROCKSDB_LOG_PATH")
    echo "🎯 링크 대상: $TARGET"
    
    if [ -f "$TARGET" ] || [ ! -e "$TARGET" ]; then
        echo "✅ 링크 대상 경로 정상"
    else
        echo "⚠️ 링크 대상에 접근할 수 없습니다: $TARGET"
    fi
else
    echo "❌ 심볼릭 링크 생성 실패!"
    echo "📋 디렉토리 상태 확인:"
    ls -la /rocksdb/data/
    exit 1
fi

echo ""
echo "🎯 LOG 파일 설정 완료!"
echo "📄 RocksDB는 이제 $LOG_DIR/LOG 파일에 로그를 기록합니다."
echo "💡 이렇게 하면 데이터 디스크에 I/O 부하를 주지 않고 로그를 수집할 수 있습니다."

echo ""
echo "🔍 확인 명령어:"
echo "  링크 상태: ls -la $ROCKSDB_LOG_PATH"
echo "  LOG 파일: ls -la $LOG_DIR/"
echo "  실시간 로그: tail -f $LOG_DIR/LOG"
