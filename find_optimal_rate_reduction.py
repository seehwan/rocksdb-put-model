#!/usr/bin/env python3
"""
Find Optimal Rate Reduction Value

임의의 8%, 10%보다 실제 목표에 맞는 값을 찾기

목표:
1. CV를 acceptable level로 감소
2. Accuracy 최대화
3. Throughput loss 최소화
"""

import numpy as np


class OptimalRateReductionFinder:
    """최적 rate reduction 값 찾기"""
    
    def __init__(self):
        # 실제 측정 데이터
        self.initial_data = {
            'qps': 138769,
            'cv': 0.538,  # High volatility
            'accuracy': 75.0,
            'device_write_bw': 4116.6,
            'wa': 1.02,
            'ra': 0.1
        }
        
        # 목표 CV
        self.target_cv = 0.35  # Acceptable stability
        
        # CV-Rate 관계 모델 파라미터
        self.cv_reduction_factor = 0.70  # 경험적 값
    
    def cv_with_rate_reduction(self, rate_reduction: float) -> float:
        """
        Rate reduction에 따른 CV 계산
        
        Assumption: Linear relationship
        CV_new = CV_old * (1 - rate_reduction * factor)
        """
        cv_new = self.initial_data['cv'] * (1 - rate_reduction * self.cv_reduction_factor)
        return cv_new
    
    def find_reduction_for_target_cv(self) -> dict:
        """목표 CV를 달성하기 위한 rate reduction 계산"""
        
        print("=" * 80)
        print("🎯 Finding Optimal Rate Reduction for Target CV")
        print("=" * 80)
        
        current_cv = self.initial_data['cv']
        required_cv_reduction = (current_cv - self.target_cv) / current_cv
        
        # CV reduction = rate_reduction * cv_reduction_factor
        required_rate_reduction = required_cv_reduction / self.cv_reduction_factor
        
        print(f"\n📊 Target Analysis:")
        print(f"   Current CV: {current_cv:.3f}")
        print(f"   Target CV: {self.target_cv:.3f}")
        print(f"   Required CV reduction: {required_cv_reduction:.1%}")
        print(f"   Required rate reduction: {required_rate_reduction:.1%}")
        
        if required_rate_reduction > 1.0:
            print(f"\n⚠️  Warning: Required reduction ({required_rate_reduction:.1%}) > 100%")
            print(f"   Target CV is too ambitious!")
        
        return {
            'required_rate_reduction': required_rate_reduction,
            'resulting_cv': self.target_cv if required_rate_reduction <= 1.0 else 0.0
        }
    
    def analyze_cv_improvement(self) -> dict:
        """다양한 rate reduction 시나리오 분석"""
        
        print("\n" + "=" * 80)
        print("📊 CV Improvement Analysis")
        print("=" * 80)
        
        print(f"\n{'Reduction':<12} {'CV':<10} {'CV vs Target':<15} {'Status':<15}")
        print("-" * 80)
        
        results = []
        
        for reduction in np.arange(0.05, 0.25, 0.01):
            cv = self.cv_with_rate_reduction(reduction)
            diff_from_target = cv - self.target_cv
            status = "✅ Acceptable" if cv <= self.target_cv * 1.2 else "⚠️ Below target"
            
            print(f"{reduction*100:>9.1f}%   "
                  f"{cv:>7.3f}   "
                  f"{diff_from_target:>+6.3f}   "
                  f"{status:<15}")
            
            results.append({
                'reduction': reduction,
                'cv': cv,
                'diff_from_target': diff_from_target,
                'acceptable': cv <= self.target_cv * 1.2
            })
        
        # Acceptable reductions
        acceptable = [r for r in results if r['acceptable']]
        
        if acceptable:
            min_reduction = min(acceptable, key=lambda x: x['reduction'])
            
            print("\n✅ Minimum acceptable reduction:")
            print(f"   Reduction: {min_reduction['reduction']*100:.1f}%")
            print(f"   CV: {min_reduction['cv']:.3f}")
        
        return results
    
    def balance_throughput_vs_accuracy(self) -> dict:
        """Throughput loss vs Accuracy gain 균형 분석"""
        
        print("\n" + "=" * 80)
        print("⚖️  Throughput vs Accuracy Trade-off")
        print("=" * 80)
        
        # Estimate accuracy gain
        # Hypothesis: Accuracy gain is proportional to CV reduction
        base_accuracy = self.initial_data['accuracy']
        base_cv = self.initial_data['cv']
        
        print(f"\n{'Reduction':<12} {'CV':<10} {'Accuracy':<12} {'Efficiency':<12}")
        print("-" * 80)
        
        results = []
        
        for reduction in np.arange(0.05, 0.21, 0.02):
            cv = self.cv_with_rate_reduction(reduction)
            cv_reduction = (base_cv - cv) / base_cv
            
            # Estimate accuracy: 1% accuracy gain per 10% CV reduction
            accuracy_gain = cv_reduction * 10  # 10% CV reduction → 1% accuracy
            accuracy = base_accuracy + accuracy_gain
            
            # Efficiency = accuracy_gain / throughput_loss
            efficiency = accuracy_gain / reduction
            
            print(f"{reduction*100:>9.1f}%   "
                  f"{cv:>7.3f}   "
                  f"{accuracy:>9.1f}%   "
                  f"{efficiency:>9.1f}")
            
            results.append({
                'reduction': reduction,
                'cv': cv,
                'accuracy': accuracy,
                'efficiency': efficiency
            })
        
        # Find most efficient
        most_efficient = max(results, key=lambda x: x['efficiency'])
        
        print(f"\n✅ Most efficient reduction:")
        print(f"   Reduction: {most_efficient['reduction']*100:.1f}%")
        print(f"   CV: {most_efficient['cv']:.3f}")
        print(f"   Accuracy: {most_efficient['accuracy']:.1f}%")
        print(f"   Efficiency: {most_efficient['efficiency']:.2f}")
        
        return results, most_efficient
    
    def estimate_accuracy_model(self, cv: float) -> float:
        """CV → Accuracy 변환 모델"""
        
        base_cv = self.initial_data['cv']
        base_accuracy = self.initial_data['accuracy']
        
        # Linear model (first approximation)
        cv_reduction = (base_cv - cv) / base_cv
        
        # From observation: ~2% accuracy gain per 20% CV reduction
        accuracy_gain = cv_reduction * 10  # 10% accuracy per 100% CV reduction
        
        accuracy = base_accuracy + accuracy_gain
        accuracy = min(100, max(70, accuracy))  # Bounds
        
        return accuracy
    
    def find_optimal_by_accuracy_target(self, target_accuracy: float) -> dict:
        """목표 accuracy 달성을 위한 rate reduction"""
        
        print("\n" + "=" * 80)
        print("🎯 Finding Rate Reduction for Target Accuracy")
        print("=" * 80)
        
        base_accuracy = self.initial_data['accuracy']
        required_accuracy_gain = target_accuracy - base_accuracy
        
        print(f"\n📊 Target Analysis:")
        print(f"   Current accuracy: {base_accuracy:.1f}%")
        print(f"   Target accuracy: {target_accuracy:.1f}%")
        print(f"   Required gain: {required_accuracy_gain:+.1f}%")
        
        # Estimate required CV reduction
        # 1% accuracy gain per 20% CV reduction
        required_cv_reduction = required_accuracy_gain * 0.20
        
        current_cv = self.initial_data['cv']
        target_cv = current_cv * (1 - required_cv_reduction)
        
        # CV → Rate reduction
        required_rate_reduction = required_cv_reduction / self.cv_reduction_factor
        
        print(f"\n📈 Required:")
        print(f"   CV reduction: {required_cv_reduction:.1%}")
        print(f"   Target CV: {target_cv:.3f}")
        print(f"   Rate reduction: {required_rate_reduction:.1%}")
        
        return {
            'rate_reduction': required_rate_reduction,
            'target_cv': target_cv,
            'target_accuracy': target_accuracy
        }
    
    def comprehensive_analysis(self) -> dict:
        """종합 분석"""
        
        print("=" * 80)
        print("🔬 Comprehensive Rate Reduction Analysis")
        print("=" * 80)
        
        # 1. Target CV analysis
        target_cv_result = self.find_reduction_for_target_cv()
        
        # 2. Acceptable reductions
        cv_improvements = self.analyze_cv_improvement()
        acceptable = [r for r in cv_improvements if r['acceptable']]
        
        if acceptable:
            min_acceptable = min(acceptable, key=lambda x: x['reduction'])
            print(f"\n✅ Minimum for target: {min_acceptable['reduction']*100:.1f}%")
        
        # 3. Efficiency analysis
        efficiency_results, most_efficient = self.balance_throughput_vs_accuracy()
        
        print("\n" + "=" * 80)
        print("💡 RECOMMENDATION")
        print("=" * 80)
        
        print("\n종합 분석 결과:")
        print("-" * 80)
        print(f"1. Target CV (0.35) 달성: {target_cv_result['required_rate_reduction']*100:.1f}% reduction")
        print(f"   → 결과 CV: {target_cv_result['resulting_cv']:.3f}")
        
        if acceptable:
            print(f"\n2. Minimum acceptable ({self.target_cv * 1.2:.3f}):")
            print(f"   → {min_acceptable['reduction']*100:.1f}% reduction")
            print(f"   → CV: {min_acceptable['cv']:.3f}")
        
        print(f"\n3. Most efficient:")
        print(f"   → {most_efficient['reduction']*100:.1f}% reduction")
        print(f"   → CV: {most_efficient['cv']:.3f}")
        print(f"   → Accuracy: {most_efficient['accuracy']:.1f}%")
        
        # Final recommendation
        if acceptable:
            recommended = min_acceptable['reduction']
            reason = 'Minimum for acceptable stability'
        else:
            recommended = most_efficient['reduction']
            reason = 'Most efficient balance'
        
        print("\n✅ RECOMMENDED RATE REDUCTION:")
        print(f"   {recommended*100:.1f}%")
        print(f"   이유: {reason}")
        
        return {
            'recommended': recommended,
            'target_cv_result': target_cv_result,
            'efficiency': most_efficient,
            'min_acceptable': min_acceptable if acceptable else None
        }


def main():
    """Main analysis"""
    print("=" * 80)
    print("🚀 Optimal Rate Reduction Analysis")
    print("=" * 80)
    
    finder = OptimalRateReductionFinder()
    
    # Comprehensive analysis
    results = finder.comprehensive_analysis()
    
    # Additional analyses
    print("\n" + "=" * 80)
    print("📊 Additional Analyses")
    print("=" * 80)
    
    # Accuracy targets
    for target_acc in [76.0, 77.0, 78.0]:
        result = finder.find_optimal_by_accuracy_target(target_acc)
        print(f"\n{target_acc:.1f}% accuracy:")
        print(f"   Required reduction: {result['rate_reduction']*100:.1f}%")
        print(f"   Resulting CV: {result['target_cv']:.3f}")
    
    print("\n" + "=" * 80)
    print("✅ Analysis Complete!")
    print("=" * 80)
    
    final_reduction = results['recommended'] * 100
    print(f"\n💡 Recommended rate reduction: {final_reduction:.1f}%")
    print("   (Based on CV target, efficiency, and accuracy goals)")


if __name__ == "__main__":
    main()

