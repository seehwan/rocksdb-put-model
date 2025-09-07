#!/bin/bash
# Phase-B: RocksDB Benchmark 실행 스크립트

echo "=== Phase-B: RocksDB Benchmark (2025-09-08) ==="
echo "RocksDB 성능 측정을 시작합니다."
echo "주의: 이 테스트는 8-10시간 소요될 수 있습니다."
echo

read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "실행을 취소했습니다."
    exit 1
fi

cd phase-b
python3 rocksdb_benchmark.py

echo
echo "Phase-B 완료! 결과를 확인하세요."
