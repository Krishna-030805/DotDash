import numpy as np
import pickle
import base64
from sklearn.svm import OneClassSVM

class Enrollment:
    def __init__(self, min_samples=3, max_samples=5):
        self.min_samples = min_samples
        self.max_samples = max_samples
        self.samples = []
        self.qualities = []
        self.raw_sequences = []

    def is_complete(self):
        return len(self.samples) >= self.min_samples

    def can_accept_more(self):
        return len(self.samples) < self.max_samples

    # -------------------------------
    # QUALITY SCORE (CONTINUOUS)
    # -------------------------------
    def _compute_quality(self, metrics):
        """
        metrics expected in range [0,1]
        """
        timing = metrics["timing_precision"]
        tempo = metrics["tempo_consistency"]
        pattern = metrics["pattern_accuracy"]
        outlier_ratio = metrics.get("outlier_ratio", 0.0)

        outlier_score = 1.0 - outlier_ratio

        quality = (
            0.40 * timing +
            0.30 * tempo +
            0.20 * pattern +
            0.10 * outlier_score
        )

        return float(np.clip(quality, 0.0, 1.0))

    # -------------------------------
    # HARD SECURITY GATE
    # -------------------------------
    def _passes_gate(self, metrics):
        if metrics["pattern_accuracy"] < 1.0:
            return False, "Pattern mismatch"

        if metrics["timing_precision"] < 0.85:
            return False, "Timing precision too low"

        if metrics.get("outlier_ratio", 0.0) > 0.25:
            return False, "Too many rhythm outliers"

        return True, None

    # -------------------------------
    # PUBLIC API
    # -------------------------------
    def add(self, feature_vector, rhythm_metrics, raw_sequence=None):
        quality = self._compute_quality(rhythm_metrics)
        accepted, reason = self._passes_gate(rhythm_metrics)

        if accepted:
            self.samples.append(feature_vector)
            self.qualities.append(quality)
            if raw_sequence is not None:
                self.raw_sequences.append(raw_sequence)

        return {
            "status": "accepted" if accepted else "rejected",
            "quality_score": quality,
            "rejection_reason": reason,
            "samples_collected": len(self.samples),
            "samples_needed": max(0, self.min_samples - len(self.samples))
        }

    # -------------------------------
    # PROFILE BUILDING
    # -------------------------------
    def build_profile(self):
        weights = np.array(self.qualities)
        weights = weights / np.sum(weights)

        X_train = np.array(self.samples)
        weighted_mean = np.average(X_train, axis=0, weights=weights)
        std_dev = np.std(X_train, axis=0)
        
        # Covariance matrix (regularized to be invertible)
        if len(X_train) > 1:
            cov_matrix = np.cov(X_train.T)
            if cov_matrix.ndim == 0:
                cov_matrix = np.array([[float(cov_matrix)]])
            # Regularize
            cov_matrix += np.eye(cov_matrix.shape[0]) * 1e-4
        else:
            cov_matrix = np.eye(X_train.shape[1]) * 1e-4

        # Recommended threshold: based on inter-sample variance
        # Use average std deviation across all features as the threshold baseline
        recommended_threshold = float(np.mean(std_dev) * 3.0 + 65.0)

        # Consistency: how similar the enrolled samples are to each other
        consistency = float(np.clip(1.0 - np.std(self.qualities), 0.0, 1.0))

        # Train One-Class SVM
        # Unscaled RBF with gamma='scale' (divides by n_features*X.var()) works best here
        svm_model = OneClassSVM(kernel='rbf', gamma='scale', nu=0.1)
        svm_model.fit(X_train)
        
        # Serialize the SVM model for Firebase storage
        svm_bytes = pickle.dumps(svm_model)
        svm_b64 = base64.b64encode(svm_bytes).decode('utf-8')

        # Convert raw_sequences to serializable dicts (Firestore does not support nested arrays)
        serializable_raw = []
        for seq in self.raw_sequences:
            if isinstance(seq, (tuple, list)) and len(seq) == 2:
                serializable_raw.append({
                    "presses": [float(x) for x in seq[0]],
                    "gaps": [float(x) for x in seq[1]]
                })
            elif isinstance(seq, dict):
                serializable_raw.append({
                    "presses": [float(x) for x in seq.get("presses", [])],
                    "gaps": [float(x) for x in seq.get("gaps", [])]
                })

        return {
            # Canonical field names (used by matcher)
            "mean": weighted_mean.tolist(),
            "std": std_dev.tolist(),
            "cov_matrix": cov_matrix.tolist(),
            "recommended_threshold": recommended_threshold,
            # Legacy alias (kept for backwards compat)
            "mean_vector": weighted_mean.tolist(),
            "std_vector": std_dev.tolist(),
            # Metadata
            "sample_count": len(self.samples),
            "consistency_score": consistency,
            "raw_sequences": serializable_raw,
            "svm_model_b64": svm_b64
        }
