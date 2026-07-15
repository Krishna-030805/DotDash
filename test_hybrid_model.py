import numpy as np
from optimized_feature_extractor import OptimizedFeatureExtractor
from enrollment import Enrollment
from matcher import Matcher

def run_test():
    print("Testing Hybrid DTW + SVM Biometric Model...\n")
    
    # 1. Create Enrollment session
    enroll = Enrollment(min_samples=3, max_samples=5)
    
    # Mock data
    # Let's say user taps "..." (3 dots)
    base_presses = [0.1, 0.1, 0.1]
    base_gaps = [0.1, 0.1]
    
    extractor = OptimizedFeatureExtractor()
    
    for i in range(3):
        # Slightly vary the presses and gaps
        presses = [p + np.random.uniform(-0.01, 0.01) for p in base_presses]
        gaps = [g + np.random.uniform(-0.01, 0.01) for g in base_gaps]
        
        feature_vec = extractor.extract(presses, gaps)
        
        # Perfect mock metrics
        metrics = {
            "timing_precision": 0.95,
            "tempo_consistency": 0.95,
            "pattern_accuracy": 1.0,
            "outlier_ratio": 0.0
        }
        
        enroll.add(feature_vec, metrics, raw_sequence=(presses, gaps))
        
    print("Enrollment complete. Building profile...")
    profile = enroll.build_profile()
    
    print(f"Profile built! SVM Model included: {'svm_model_b64' in profile}")
    print(f"Raw sequences included: {'raw_sequences' in profile}")
    
    matcher = Matcher()
    
    # 2. Test with a genuine login (similar timing)
    print("\n--- Testing Genuine Login ---")
    gen_presses = [0.105, 0.095, 0.102]
    gen_gaps = [0.098, 0.101]
    gen_vec = extractor.extract(gen_presses, gen_gaps)
    
    results = matcher.authenticate_with_multiple_metrics(gen_vec, profile, test_raw_seq=(gen_presses, gen_gaps))
    print(f"Final Decision: {'ACCEPTED' if results['final_decision'] else 'REJECTED'}")
    print(f"Votes: {results['votes']}")
    print(f"DTW Accepted: {results.get('dtw', {}).get('accepted')}")
    print(f"SVM Accepted: {results.get('svm', {}).get('accepted')}")
    
    # 3. Test with an imposter login (very different timing)
    print("\n--- Testing Imposter Login ---")
    imp_presses = [0.3, 0.2, 0.4] # Much slower
    imp_gaps = [0.3, 0.25]
    imp_vec = extractor.extract(imp_presses, imp_gaps)
    
    imp_results = matcher.authenticate_with_multiple_metrics(imp_vec, profile, test_raw_seq=(imp_presses, imp_gaps))
    print(f"Final Decision: {'ACCEPTED' if imp_results['final_decision'] else 'REJECTED'}")
    print(f"Votes: {imp_results['votes']}")
    print(f"DTW Accepted: {imp_results.get('dtw', {}).get('accepted')}")
    print(f"SVM Accepted: {imp_results.get('svm', {}).get('accepted')}")

if __name__ == "__main__":
    run_test()
