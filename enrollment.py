import numpy as np


class Enrollment:
    def __init__(self, min_samples=3, max_samples=5):
        self.min_samples = min_samples
        self.max_samples = max_samples
        self.samples = []
        self.qualities = []

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
    def add(self, feature_vector, rhythm_metrics):
        quality = self._compute_quality(rhythm_metrics)
        accepted, reason = self._passes_gate(rhythm_metrics)

        if accepted:
            self.samples.append(feature_vector)
            self.qualities.append(quality)

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

        weighted_mean = np.average(self.samples, axis=0, weights=weights)

        consistency = 1.0 - np.std(self.qualities)

        return {
            "mean_vector": weighted_mean.tolist(),
            "sample_count": len(self.samples),
            "consistency_score": float(np.clip(consistency, 0.0, 1.0))
        }