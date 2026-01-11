"""
Optimized Feature Extractor - Reduced from 66 to 32 dimensions
===============================================================
Removes redundant features while maintaining discrimination power.

KEY OPTIMIZATION: Focus on most discriminative features:
1. Rhythm ratios (speed-invariant)
2. Statistical moments (captures distribution)
3. Temporal patterns (acceleration, consistency)
4. Morse-specific features (dot/dash distinction)

REMOVED:
- Excessive position-based features (40 → 8)
- Redundant statistical features
- Highly correlated features
"""

import numpy as np


class OptimizedFeatureExtractor:
    """
    Extract discriminative features with reduced dimensionality.
    Total features: 32 (down from 66)
    """
    
    def __init__(self, dot_dash_threshold_ratio=2.0):
        self.dot_dash_threshold = dot_dash_threshold_ratio
    
    def extract(self, presses, gaps):
        """
        Extract optimized 32-dimensional feature vector.
        
        Feature breakdown:
        - Key position features: 8 dimensions
        - Morse rhythm features: 8 dimensions
        - Statistical features: 10 dimensions
        - Temporal features: 6 dimensions
        
        Args:
            presses (list): Key press durations
            gaps (list): Gap durations
        
        Returns:
            np.array: 32-dimensional feature vector
        """
        presses = np.array(presses) if len(presses) > 0 else np.array([0.001])
        gaps = np.array(gaps) if len(gaps) > 0 else np.array([0.001])
        
        # Estimate base unit
        base_unit = self._estimate_dot_duration(presses)
        
        # Normalize by base unit (speed-invariant)
        norm_presses = presses / base_unit
        norm_gaps = gaps / base_unit
        
        # === 1. KEY POSITION FEATURES (8 dims) ===
        # Only extract critical positions: first 4, last 4
        # This captures start/end patterns while reducing dimensions
        position_features = self._extract_position_features(norm_presses, norm_gaps)
        
        # === 2. MORSE RHYTHM FEATURES (8 dims) ===
        morse_features = self._extract_morse_features(presses, gaps, base_unit)
        
        # === 3. STATISTICAL FEATURES (10 dims) ===
        statistical_features = self._extract_statistical_features(norm_presses, norm_gaps)
        
        # === 4. TEMPORAL FEATURES (6 dims) ===
        temporal_features = self._extract_temporal_features(presses, gaps)
        
        # Combine all features (total: 32)
        feature_vector = np.concatenate([
            position_features,      # 8
            morse_features,          # 8
            statistical_features,    # 10
            temporal_features        # 6
        ])
        
        return feature_vector
    
    def _estimate_dot_duration(self, presses):
        """Estimate base timing unit."""
        if len(presses) == 0:
            return 0.1
        return np.percentile(presses, 25)
    
    def _extract_position_features(self, norm_presses, norm_gaps):
        """
        Extract key position features (8 dimensions).
        Focus on first 4 and last 4 elements.
        """
        features = []
        
        # First 4 presses (or pad with median if fewer)
        median_press = np.median(norm_presses)
        for i in range(4):
            if i < len(norm_presses):
                features.append(norm_presses[i])
            else:
                features.append(median_press)
        
        # Last 4 presses (or pad with median)
        for i in range(-4, 0):
            if abs(i) <= len(norm_presses):
                features.append(norm_presses[i])
            else:
                features.append(median_press)
        
        return np.array(features)
    
    def _extract_morse_features(self, presses, gaps, base_unit):
        """
        Extract Morse-specific features (8 dimensions).
        """
        threshold = base_unit * self.dot_dash_threshold
        dots = presses[presses < threshold]
        dashes = presses[presses >= threshold]
        
        total_elements = len(presses)
        
        # Feature 1-2: Element counts (normalized)
        dot_ratio = len(dots) / total_elements if total_elements > 0 else 0
        dash_ratio = len(dashes) / total_elements if total_elements > 0 else 0
        
        # Feature 3-4: Average durations (normalized)
        avg_dot = np.mean(dots) / base_unit if len(dots) > 0 else 1.0
        avg_dash = np.mean(dashes) / base_unit if len(dashes) > 0 else 3.0
        
        # Feature 5-6: Consistency metrics
        cv_dots = np.std(dots) / np.mean(dots) if len(dots) > 1 and np.mean(dots) > 0 else 0
        cv_dashes = np.std(dashes) / np.mean(dashes) if len(dashes) > 1 and np.mean(dashes) > 0 else 0
        
        # Feature 7: Dash-to-dot ratio
        dash_dot_ratio = avg_dash / avg_dot if avg_dot > 0 else 3.0
        
        # Feature 8: Average gap (normalized)
        avg_gap = np.mean(gaps) / base_unit if len(gaps) > 0 else 1.0
        
        return np.array([
            dot_ratio, dash_ratio, avg_dot, avg_dash,
            cv_dots, cv_dashes, dash_dot_ratio, avg_gap
        ])
    
    def _extract_statistical_features(self, norm_presses, norm_gaps):
        """
        Extract statistical features (10 dimensions).
        """
        # Press statistics (5 features)
        press_mean = np.mean(norm_presses)
        press_std = np.std(norm_presses)
        press_median = np.median(norm_presses)
        press_iqr = np.percentile(norm_presses, 75) - np.percentile(norm_presses, 25)
        press_skew = self._calculate_skewness(norm_presses)
        
        # Gap statistics (4 features)
        gap_mean = np.mean(norm_gaps)
        gap_std = np.std(norm_gaps)
        gap_median = np.median(norm_gaps)
        gap_iqr = np.percentile(norm_gaps, 75) - np.percentile(norm_gaps, 25)
        
        # Interaction feature (1 feature)
        press_gap_ratio = press_mean / gap_mean if gap_mean > 0 else 1.0
        
        return np.array([
            press_mean, press_std, press_median, press_iqr, press_skew,
            gap_mean, gap_std, gap_median, gap_iqr,
            press_gap_ratio
        ])
    
    def _extract_temporal_features(self, presses, gaps):
        """
        Extract temporal dynamics features (6 dimensions).
        """
        # Feature 1: Total duration
        total_time = np.sum(presses) + np.sum(gaps)
        
        # Feature 2: Typing speed (elements per second)
        elements_per_second = len(presses) / total_time if total_time > 0 else 0
        
        # Feature 3: Rhythm stability
        all_timings = np.concatenate([presses, gaps])
        rhythm_stability = 1 / (1 + np.std(all_timings))
        
        # Feature 4: Acceleration (speed change over time)
        if len(presses) > 3:
            mid = len(presses) // 2
            first_half_avg = np.mean(presses[:mid])
            second_half_avg = np.mean(presses[mid:])
            acceleration = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
        else:
            acceleration = 0
        
        # Feature 5: Press duration trend (linear regression slope)
        if len(presses) > 2:
            x = np.arange(len(presses))
            slope = np.polyfit(x, presses, 1)[0]
        else:
            slope = 0
        
        # Feature 6: Gap duration trend
        if len(gaps) > 2:
            x = np.arange(len(gaps))
            gap_slope = np.polyfit(x, gaps, 1)[0]
        else:
            gap_slope = 0
        
        return np.array([
            total_time,
            elements_per_second,
            rhythm_stability,
            acceleration,
            slope,
            gap_slope
        ])
    
    def _calculate_skewness(self, data):
        """Calculate skewness (measure of asymmetry)."""
        if len(data) < 3:
            return 0
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return 0
        
        skew = np.mean(((data - mean) / std) ** 3)
        return skew


# Testing
if __name__ == "__main__":
    extractor = OptimizedFeatureExtractor()
    
    # Test with SOS pattern
    test_presses = [0.1, 0.1, 0.1, 0.3, 0.3, 0.3, 0.1, 0.1, 0.1]
    test_gaps = [0.1, 0.1, 0.15, 0.1, 0.1, 0.15, 0.1, 0.1]
    
    features = extractor.extract(test_presses, test_gaps)
    
    print(f"Optimized Feature Vector Dimension: {len(features)}")
    print(f"Features: {features}")
    print("\nFeature breakdown:")
    print(f"  Position features (0-7): {features[:8]}")
    print(f"  Morse features (8-15): {features[8:16]}")
    print(f"  Statistical features (16-25): {features[16:26]}")
    print(f"  Temporal features (26-31): {features[26:32]}")