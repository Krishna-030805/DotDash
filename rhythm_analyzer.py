"""
Advanced Rhythm Analysis Module
================================
Provides sophisticated rhythm quality assessment using:
1. Tempo consistency analysis
2. Pattern accuracy scoring
3. Timing precision metrics
4. Beat variance detection

This replaces "Google ML Kit" with actual rhythm analysis algorithms.
"""

import numpy as np
from scipy import stats
from scipy.signal import find_peaks


class RhythmAnalyzer:
    """
    Analyzes the rhythmic quality of Morse code tapping patterns.
    """
    
    def __init__(self, ideal_dot_duration=0.15):
        """
        Initialize rhythm analyzer.
        
        Args:
            ideal_dot_duration (float): Expected dot duration in seconds
        """
        self.ideal_dot_duration = ideal_dot_duration
        self.ideal_dash_duration = ideal_dot_duration * 3
    
    def analyze_rhythm(self, presses, gaps, password_info):
        """
        Comprehensive rhythm analysis.
        
        Args:
            presses (list): Press durations
            gaps (list): Gap durations
            password_info (dict): Expected pattern information
        
        Returns:
            dict: Detailed rhythm analysis scores
        """
        if len(presses) == 0:
            return self._empty_score()
        
        # Convert to numpy arrays
        presses = np.array(presses)
        gaps = np.array(gaps) if len(gaps) > 0 else np.array([])
        
        # Calculate individual metrics
        tempo_consistency = self._analyze_tempo_consistency(presses, gaps)
        pattern_accuracy = self._analyze_pattern_accuracy(presses, password_info)
        timing_precision = self._analyze_timing_precision(presses)
        rhythm_stability = self._analyze_rhythm_stability(presses, gaps)
        dot_dash_separation = self._analyze_dot_dash_separation(presses)
        
        # Calculate overall score (weighted average)
        overall_score = (
            tempo_consistency * 0.25 +
            pattern_accuracy * 0.30 +
            timing_precision * 0.20 +
            rhythm_stability * 0.15 +
            dot_dash_separation * 0.10
        )
        
        return {
            'overall_score': overall_score,
            'tempo_consistency': tempo_consistency,
            'pattern_accuracy': pattern_accuracy,
            'timing_precision': timing_precision,
            'rhythm_stability': rhythm_stability,
            'dot_dash_separation': dot_dash_separation,
            'details': {
                'avg_press': float(np.mean(presses)),
                'std_press': float(np.std(presses)),
                'cv_press': float(np.std(presses) / np.mean(presses)) if np.mean(presses) > 0 else 0,
                'total_duration': float(np.sum(presses) + np.sum(gaps))
            }
        }
    
    def _analyze_tempo_consistency(self, presses, gaps):
        """
        Measure how consistent the tempo is throughout the pattern.
        Lower coefficient of variation = higher consistency.
        
        Returns:
            float: Score 0-1 (1 = perfectly consistent)
        """
        # Combine all timings
        if len(gaps) > 0:
            all_timings = np.concatenate([presses, gaps])
        else:
            all_timings = presses
        
        if len(all_timings) < 2:
            return 0.5
        
        # Calculate coefficient of variation
        mean_time = np.mean(all_timings)
        std_time = np.std(all_timings)
        
        if mean_time == 0:
            return 0.0
        
        cv = std_time / mean_time
        
        # Convert to 0-1 score (lower CV = higher score)
        # CV of 0.3 or less = perfect (1.0)
        # CV of 1.0 or more = poor (0.0)
        score = max(0, min(1, 1.0 - (cv - 0.3) / 0.7))
        
        return score
    
    def _analyze_pattern_accuracy(self, presses, password_info):
        """
        Check if the tapped pattern matches the expected Morse pattern.
        
        Returns:
            float: Score 0-1 (1 = perfect match)
        """
        expected_elements = password_info['total_elements']
        actual_elements = len(presses)
        
        # Check element count
        if actual_elements == 0:
            return 0.0
        
        count_accuracy = min(1.0, expected_elements / actual_elements) if actual_elements >= expected_elements else actual_elements / expected_elements
        
        # Estimate dot duration from shortest presses
        estimated_dot = np.percentile(presses, 25)
        
        if estimated_dot == 0:
            return count_accuracy * 0.5
        
        # Classify each press as dot or dash
        threshold = estimated_dot * 2.0
        dots = presses[presses < threshold]
        dashes = presses[presses >= threshold]
        
        # Calculate expected dot/dash counts from Morse pattern
        morse_pattern = password_info['morse_code'].replace(' ', '')
        expected_dots = morse_pattern.count('.')
        expected_dashes = morse_pattern.count('-')
        
        # Compare actual vs expected
        dot_accuracy = 1.0 - abs(len(dots) - expected_dots) / max(expected_dots, 1)
        dash_accuracy = 1.0 - abs(len(dashes) - expected_dashes) / max(expected_dashes, 1)
        
        # Weighted combination
        pattern_score = (
            count_accuracy * 0.4 +
            max(0, dot_accuracy) * 0.3 +
            max(0, dash_accuracy) * 0.3
        )
        
        return max(0, min(1, pattern_score))
    
    def _analyze_timing_precision(self, presses):
        """
        Measure the precision of individual tap durations.
        
        Returns:
            float: Score 0-1 (1 = very precise)
        """
        if len(presses) < 2:
            return 0.5
        
        # Estimate dot duration
        dot_duration = np.percentile(presses, 25)
        
        if dot_duration == 0:
            return 0.0
        
        # Classify dots and dashes
        threshold = dot_duration * 2.0
        dots = presses[presses < threshold]
        dashes = presses[presses >= threshold]
        
        # Calculate consistency within each category
        dot_consistency = 1.0 - (np.std(dots) / np.mean(dots)) if len(dots) > 1 and np.mean(dots) > 0 else 0.5
        dash_consistency = 1.0 - (np.std(dashes) / np.mean(dashes)) if len(dashes) > 1 and np.mean(dashes) > 0 else 0.5
        
        # Combine
        precision_score = (dot_consistency + dash_consistency) / 2
        
        return max(0, min(1, precision_score))
    
    def _analyze_rhythm_stability(self, presses, gaps):
        """
        Analyze the stability of rhythm over time (are they speeding up or slowing down?).
        
        Returns:
            float: Score 0-1 (1 = perfectly stable)
        """
        if len(presses) < 4:
            return 0.5
        
        # Split into first half and second half
        mid = len(presses) // 2
        first_half = presses[:mid]
        second_half = presses[mid:]
        
        mean_first = np.mean(first_half)
        mean_second = np.mean(second_half)
        
        if mean_first == 0:
            return 0.5
        
        # Calculate relative change
        relative_change = abs(mean_second - mean_first) / mean_first
        
        # Convert to score (less change = higher score)
        # 0% change = 1.0
        # 20% change = 0.5
        # 40%+ change = 0.0
        score = max(0, min(1, 1.0 - relative_change / 0.4))
        
        return score
    
    def _analyze_dot_dash_separation(self, presses):
        """
        Measure how well dots and dashes are distinguished.
        Ideally, there should be a clear bimodal distribution.
        
        Returns:
            float: Score 0-1 (1 = perfect separation)
        """
        if len(presses) < 3:
            return 0.5
        
        # Estimate dot duration
        dot_duration = np.percentile(presses, 25)
        
        if dot_duration == 0:
            return 0.0
        
        # Classify
        threshold = dot_duration * 2.0
        dots = presses[presses < threshold]
        dashes = presses[presses >= threshold]
        
        if len(dots) == 0 or len(dashes) == 0:
            # Only one type present
            return 0.7
        
        # Calculate separation ratio
        # Ideal: dashes should be ~3x longer than dots
        actual_ratio = np.mean(dashes) / np.mean(dots) if np.mean(dots) > 0 else 0
        ideal_ratio = 3.0
        
        # Score based on how close to ideal
        ratio_error = abs(actual_ratio - ideal_ratio) / ideal_ratio
        separation_score = max(0, min(1, 1.0 - ratio_error))
        
        return separation_score
    
    def _empty_score(self):
        """Return empty score when no data available."""
        return {
            'overall_score': 0.0,
            'tempo_consistency': 0.0,
            'pattern_accuracy': 0.0,
            'timing_precision': 0.0,
            'rhythm_stability': 0.0,
            'dot_dash_separation': 0.0,
            'details': {}
        }
    
    def get_feedback_message(self, score_dict):
        """
        Generate human-readable feedback based on scores.
        
        Args:
            score_dict (dict): Output from analyze_rhythm()
        
        Returns:
            str: Feedback message
        """
        overall = score_dict['overall_score']
        
        if overall >= 0.85:
            return "🌟 Excellent rhythm! Very consistent and accurate."
        elif overall >= 0.70:
            return "✅ Good rhythm. Minor inconsistencies detected."
        elif overall >= 0.55:
            return "⚠️  Moderate rhythm. Try to maintain steadier tempo."
        else:
            return "❌ Rhythm needs improvement. Focus on consistency."


# Testing module
if __name__ == "__main__":
    analyzer = RhythmAnalyzer()
    
    # Test with SOS pattern (... --- ...)
    test_presses = [0.1, 0.1, 0.1, 0.3, 0.3, 0.3, 0.1, 0.1, 0.1]
    test_gaps = [0.1, 0.1, 0.15, 0.1, 0.1, 0.15, 0.1, 0.1]
    
    password_info = {
        'morse_code': '... --- ...',
        'total_elements': 9
    }
    
    results = analyzer.analyze_rhythm(test_presses, test_gaps, password_info)
    
    print("Rhythm Analysis Results:")
    print(f"Overall Score: {results['overall_score']:.1%}")
    print(f"Tempo Consistency: {results['tempo_consistency']:.1%}")
    print(f"Pattern Accuracy: {results['pattern_accuracy']:.1%}")
    print(f"Timing Precision: {results['timing_precision']:.1%}")
    print(f"\nFeedback: {analyzer.get_feedback_message(results)}")