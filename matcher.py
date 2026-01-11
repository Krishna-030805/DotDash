"""
Final Matcher Module - Tuned for Human Variability
==================================================
Key "Endgame" Features:
1. Minimum Threshold Floor: Prevents "Overfitting" (being punished for being too good during enrollment).
2. Tolerance Multiplier: Adds a 20% buffer to all checks.
3. Database Auto-Fix: Automatically handles 'mean' vs 'mean_vector' mismatches.
"""

import numpy as np
from scipy.spatial.distance import mahalanobis

class Matcher:
    # --- TUNING KNOBS ---
    # Increase this if it is still too strict. (2.5 is a good "Human" baseline)
    MIN_THRESHOLD = 2.5  
    
    # Multiplier to relax the strictness (1.2 = 20% more lenient)
    TOLERANCE_MULTIPLIER = 1.2 

    def __init__(self, threshold=None, metric='euclidean', use_dynamic_threshold=True):
        self.threshold = threshold
        self.metric = metric
        self.use_dynamic_threshold = use_dynamic_threshold

    def _normalize_profile(self, profile):
        """Auto-fixes database key mismatches (mean vs mean_vector)."""
        normalized = profile.copy()
        
        # FIX: Ensure 'mean' exists and is a numpy array
        if 'mean' not in normalized and 'mean_vector' in normalized:
            normalized['mean'] = np.array(normalized['mean_vector'])
        elif 'mean' in normalized:
             normalized['mean'] = np.array(normalized['mean'])

        # FIX: Ensure 'std' exists and is a numpy array
        if 'std' not in normalized:
            if 'std_vector' in normalized:
                normalized['std'] = np.array(normalized['std_vector'])
            elif 'std_dev' in normalized:
                normalized['std'] = np.array(normalized['std_dev'])
        elif 'std' in normalized:
            normalized['std'] = np.array(normalized['std'])

        # FIX: Covariance Matrix
        if 'cov_matrix' in normalized:
            normalized['cov_matrix'] = np.array(normalized['cov_matrix'])
            
        return normalized

    def authenticate(self, test_vector, profile):
        """
        Authenticate with 'Human Tolerance' logic.
        """
        # 1. Fix Keys
        profile = self._normalize_profile(profile)
        
        if 'mean' not in profile:
            # Fallback for empty profiles to prevent crashing
            return 999.0, False, {'distance': 999.0, 'threshold': 0.0, 'confidence': 1.0}

        # 2. Calculate Base Threshold
        if self.use_dynamic_threshold and 'recommended_threshold' in profile:
            base_threshold = float(profile['recommended_threshold'])
        else:
            base_threshold = self.threshold if self.threshold is not None else 2.0

        # 3. APPLY ENDGAME FIX: The Floor & Multiplier
        # We ensure the threshold is NEVER smaller than MIN_THRESHOLD
        effective_threshold = max(base_threshold, self.MIN_THRESHOLD)
        
        # We give an extra buffer multiplier
        effective_threshold *= self.TOLERANCE_MULTIPLIER

        # 4. Calculate Distance
        if self.metric == 'euclidean':
            distance = self._euclidean_distance(test_vector, profile)
        elif self.metric == 'manhattan':
            distance = self._manhattan_distance(test_vector, profile)
        elif self.metric == 'mahalanobis':
            distance = self._mahalanobis_distance(test_vector, profile)
        else:
            distance = self._euclidean_distance(test_vector, profile)

        # 5. Decision
        accepted = distance < effective_threshold

        # 6. Confidence Calculation
        confidence = self._calculate_confidence(distance, effective_threshold)

        details = {
            'distance': distance,
            'threshold': effective_threshold,
            'margin': effective_threshold - distance,
            'confidence': confidence,
            'metric': self.metric
        }

        return distance, accepted, details

    def _euclidean_distance(self, test_vector, profile):
        mean_vector = profile['mean']
        test_vector = np.array(test_vector)
        # Using linalg.norm is standard for Euclidean
        return np.linalg.norm(test_vector - mean_vector)

    def _manhattan_distance(self, test_vector, profile):
        mean_vector = profile['mean']
        test_vector = np.array(test_vector)
        # Sum of absolute differences (often better for outlier rejection)
        return np.sum(np.abs(test_vector - mean_vector))

    def _mahalanobis_distance(self, test_vector, profile):
        mean_vector = profile['mean']
        cov_matrix = profile.get('cov_matrix')
        test_vector = np.array(test_vector)

        # Safety Fallback: If covariance is missing or wrong shape, use Euclidean
        if cov_matrix is None or len(cov_matrix) != len(test_vector):
            return self._euclidean_distance(test_vector, profile)

        try:
            # Stronger regularization (1e-4) to prevent math errors
            cov_matrix_reg = cov_matrix + np.eye(cov_matrix.shape[0]) * 1e-4
            cov_inv = np.linalg.inv(cov_matrix_reg)
            diff = test_vector - mean_vector
            distance = np.sqrt(diff.T @ cov_inv @ diff)
            return distance
        except Exception:
            return self._euclidean_distance(test_vector, profile)

    def _calculate_confidence(self, distance, threshold):
        if threshold == 0: return 0.0
        
        if distance < threshold:
            # Accepted logic
            ratio = distance / threshold
            return 1.0 - ratio
        else:
            # Rejected logic
            ratio = threshold / distance
            return 1.0 - ratio

    def authenticate_with_multiple_metrics(self, test_vector, profile):
        """Robust authentication with voting."""
        profile = self._normalize_profile(profile)
        
        results = {}
        # We prioritize Euclidean and Manhattan for reliability
        metrics = ['euclidean', 'manhattan', 'mahalanobis']

        # 1. Collect results for each metric
        for metric in metrics:
            original_metric = self.metric
            self.metric = metric
            
            # This calls the updated authenticate() with the new thresholds
            distance, accepted, details = self.authenticate(test_vector, profile)
            
            results[metric] = {
                'distance': distance,
                'accepted': accepted,
                'confidence': details['confidence']
            }
            self.metric = original_metric

        # 2. Calculate Statistics (BEFORE adding non-dict items to 'results')
        # We explicitly look at the 'metrics' keys only to avoid errors
        confidence_values = [results[m]['confidence'] for m in metrics]
        avg_confidence = np.mean(confidence_values)
        
        votes = sum(1 for m in metrics if results[m]['accepted'])
        
        # 3. Final Decision Logic
        if results['euclidean']['accepted'] and votes >= 1:
            final_decision = True
        else:
            final_decision = votes >= 2

        # 4. NOW we can add the summary data safely
        results['final_decision'] = final_decision
        results['avg_confidence'] = avg_confidence
        results['votes'] = f"{votes}/3"

        return results