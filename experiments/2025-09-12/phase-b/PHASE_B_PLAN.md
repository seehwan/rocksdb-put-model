# Phase-B: 다중 환경 검증

## 🎯 목표
다양한 시스템 환경에서의 모델 일반화 성능 검증

## 📊 실험 설계

### 1. 다양한 SSD 모델 실험

#### 1.1 SATA SSD (Samsung 870 EVO)
- **인터페이스**: SATA 6Gbps
- **용량**: 1TB
- **성능**: 순차 읽기 560MB/s, 순차 쓰기 530MB/s
- **특성**: 안정적이고 경제적인 선택

#### 1.2 NVMe SSD (Samsung 980 PRO)
- **인터페이스**: PCIe 4.0 x4
- **용량**: 2TB
- **성능**: 순차 읽기 7,000MB/s, 순차 쓰기 5,000MB/s
- **특성**: 고성능 NVMe SSD

#### 1.3 QLC SSD (Intel 670p)
- **인터페이스**: PCIe 3.0 x4
- **용량**: 2TB
- **성능**: 순차 읽기 3,500MB/s, 순차 쓰기 2,700MB/s
- **특성**: 대용량 저비용 QLC 플래시

### 2. 다양한 시스템 구성 실험

#### 2.1 CPU 구성
- **Intel i5-12600K**: 10 cores, 16 threads
- **Intel i7-12700K**: 12 cores, 20 threads
- **Intel i9-12900K**: 16 cores, 24 threads

#### 2.2 메모리 구성
- **16GB**: 기본 구성
- **32GB**: 중간 구성
- **64GB**: 고성능 구성

#### 2.3 OS 구성
- **Ubuntu 20.04 LTS**: 안정적 버전
- **Ubuntu 22.04 LTS**: 최신 버전

### 3. 다양한 RocksDB 설정 실험

#### 3.1 기본 설정
- **level0_file_num_compaction_trigger**: 4
- **max_bytes_for_level_base**: 256MB
- **max_background_compactions**: 4

#### 3.2 고성능 설정
- **level0_file_num_compaction_trigger**: 8
- **max_bytes_for_level_base**: 1GB
- **max_background_compactions**: 8

#### 3.3 메모리 최적화 설정
- **level0_file_num_compaction_trigger**: 2
- **max_bytes_for_level_base**: 128MB
- **max_background_compactions**: 2

## 🔧 실험 환경

### 하드웨어 환경
- **CPU**: Intel i9-12900K (16 cores, 24 threads)
- **Memory**: 64GB DDR4-3200
- **Storage**: 다양한 SSD 모델
- **OS**: Ubuntu 22.04 LTS

### 소프트웨어 환경
- **RocksDB**: Version 8.0.0
- **Python**: 3.10+
- **모니터링**: Prometheus + Grafana
- **벤치마크**: db_bench

## 📋 실험 절차

### Day 1: SSD 모델별 실험
1. **SATA SSD 실험**
   - 기본 성능 측정
   - FillRandom 성능 측정
   - 컴팩션 성능 측정

2. **NVMe SSD 실험**
   - 기본 성능 측정
   - FillRandom 성능 측정
   - 컴팩션 성능 측정

3. **QLC SSD 실험**
   - 기본 성능 측정
   - FillRandom 성능 측정
   - 컴팩션 성능 측정

### Day 2: 시스템 구성별 실험
1. **CPU 구성별 실험**
   - i5-12600K 실험
   - i7-12700K 실험
   - i9-12900K 실험

2. **메모리 구성별 실험**
   - 16GB 메모리 실험
   - 32GB 메모리 실험
   - 64GB 메모리 실험

3. **OS 구성별 실험**
   - Ubuntu 20.04 실험
   - Ubuntu 22.04 실험

### Day 3: RocksDB 설정별 실험
1. **기본 설정 실험**
   - 기본 설정으로 성능 측정
   - 다양한 워크로드 테스트
   - 리소스 사용량 측정

2. **고성능 설정 실험**
   - 고성능 설정으로 성능 측정
   - 다양한 워크로드 테스트
   - 리소스 사용량 측정

3. **메모리 최적화 설정 실험**
   - 메모리 최적화 설정으로 성능 측정
   - 다양한 워크로드 테스트
   - 리소스 사용량 측정

### Day 4: 종합 분석
1. **환경별 성능 비교**
   - SSD 모델별 성능 비교
   - 시스템 구성별 성능 비교
   - RocksDB 설정별 성능 비교

2. **모델 일반화 성능 평가**
   - Phase-A 모델의 환경별 성능
   - 일반화 성능 지표 계산
   - 환경별 최적화 방안 도출

### Day 5: 결과 정리 및 보고서 작성
1. **데이터 분석**
   - 수집된 데이터 종합 분석
   - 성능 패턴 분석
   - 환경별 특성 분석

2. **보고서 작성**
   - 실험 결과 정리
   - 모델 일반화 성능 평가
   - 환경별 최적 설정 가이드

## 📊 예상 결과

### 1. 환경별 성능 특성
- **SSD 모델별 특성**: 각 SSD의 성능 특성 파악
- **시스템 구성별 특성**: CPU, 메모리 영향 분석
- **RocksDB 설정별 특성**: 설정에 따른 성능 변화

### 2. 모델 일반화 성능
- **환경별 정확도**: 각 환경에서의 모델 정확도
- **일반화 지표**: 전체 환경에서의 일반화 성능
- **환경별 최적화**: 환경별 모델 파라미터 튜닝

### 3. 환경별 최적 설정
- **SSD별 최적 설정**: 각 SSD에 최적화된 설정
- **시스템별 최적 설정**: 시스템 구성에 따른 최적 설정
- **워크로드별 최적 설정**: 워크로드에 따른 최적 설정

## 🎯 성공 지표

### 정량적 지표
- **환경별 모델 정확도**: 90% 이상
- **일반화 성능**: 85% 이상
- **환경별 최적화 효과**: 10% 이상 성능 향상

### 정성적 지표
- **모델 안정성**: 다양한 환경에서 일관된 성능
- **모델 해석가능성**: 환경별 특성 명확성
- **실용성**: 실제 운영 환경 적용 가능성

## 📁 출력 파일

### 실험 데이터
- `ssd_model_performance.json`: SSD 모델별 성능 데이터
- `system_config_performance.json`: 시스템 구성별 성능 데이터
- `rocksdb_config_performance.json`: RocksDB 설정별 성능 데이터

### 모델 파일
- `environment_specific_models.json`: 환경별 특화 모델
- `generalized_model.json`: 일반화 모델
- `optimization_guide.json`: 환경별 최적화 가이드

### 보고서
- `phase_b_report.md`: Phase-B 실험 보고서
- `phase_b_report.html`: Phase-B 실험 보고서 (HTML)
- `phase_b_visualizations/`: 시각화 파일들

---

**Phase 시작일**: 2025-09-19  
**예상 완료일**: 2025-09-23  
**총 기간**: 5일  
**주요 목표**: 다중 환경 검증 및 일반화 성능 평가
