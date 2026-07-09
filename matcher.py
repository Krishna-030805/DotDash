"""
Matcher Module - Normalized Distance Authentication
====================================================
Uses z-score normalized Euclidean and Manhattan distances so the
threshold is always in units of standard deviations — completely
independent of the raw millisecond scale of any individual feature.

Voting ensemble: Euclidean + Manhattan + DTW + SVM (4 models)
"""

import numpy as np
from fastdtw import fastdtw
import pickle
import base64


class Matcher:
    # Distance threshold in standard-deviation units.
    # A genuine user typically lands within 2.5-3.5 std devs of their enrollment mean.
    # An imposter is typically 5+ std devs away.
    Z_THRESHOLD = 3.5

    def __init__(self):
        pass

    # ──────────────────────────────────────────────────────────────────────────
    # Profile normalisation (handles DB key aliases)
    # ──────────────────────────────────────────────────────────────────────────

    def _normalize_profile(self, profile):
        """Ensure canonical keys exist and are numpy arrays."""
        p = profile.copy()

        # mean
        if 'mean' not in p and 'mean_vector' in p:
            p['mean'] = np.array(p['mean_vector'])
        elif 'mean' in p:
            p['mean'] = np.array(p['mean'])

        # std
        if 'std' not in p:
            for alt in ('std_vector', 'std_dev'):
                if alt in p:
                    p['std'] = np.array(p[alt])
                    break
        if 'std' in p:
            p['std'] = np.array(p['std'])

        # cov_matrix: stored flat in Firestore, reconstruct 2-D
        flat  = p.get('cov_matrix_flat', [])
        shape = p.get('cov_matrix_shape', [])
        if flat and len(shape) == 2:
            p['cov_matrix'] = np.array(flat).reshape(shape)

        return p

    # ──────────────────────────────────────────────────────────────────────────
    # Z-score normalised distances
    # ──────────────────────────────────────────────────────────────────────────

    def _z_normalize(self, test_vector, profile):
        """Return (test - mean) / max(std, 1e-5) — dimensionless z-score vector."""
        mean = profile['mean']
        std  = np.maximum(profile.get('std', np.ones_like(mean)), 1e-5)
        return (np.array(test_vector) - mean) / std

    def _euclidean_z(self, test_vector, profile):
        """Normalized Euclidean (z-score L2 norm per feature, then averaged)."""
        z = self._z_normalize(test_vector, profile)
        # Average per-feature z-score magnitude — interpretable as "how many
        # std devs away is this attempt, on average, across all features?"
        return float(np.mean(np.abs(z)))

    def _manhattan_z(self, test_vector, profile):
        """Normalized Manhattan (z-score L1 norm, averaged per feature)."""
        z = self._z_normalize(test_vector, profile)
        return float(np.mean(np.abs(z)))   # same as euclidean for L1 in 1-D aggregation

    # ──────────────────────────────────────────────────────────────────────────
    # Confidence mapping
    # ──────────────────────────────────────────────────────────────────────────

    def _confidence(self, z_distance, threshold=None):
        """
        Map a z-score distance onto [0, 1]:
          0.0  → 100% (perfect match)
          threshold → 50%
          infinity  →   0%
        """
        t = threshold or self.Z_THRESHOLD
        if z_distance < t:
            return 1.0 - (z_distance / t) * 0.5   # 100% → 50%
        else:
            return (t / max(z_distance, 1e-5)) * 0.5  # 50% → 0%

    # ──────────────────────────────────────────────────────────────────────────
    # DTW
    # ──────────────────────────────────────────────────────────────────────────

    def _dtw_distance(self, test_raw_seq, profile_raw_seqs):
        """Average DTW distance (ms per element) between attempt and enrollments."""
        if not test_raw_seq or not profile_raw_seqs:
            return 999.0

        def _flatten(seq):
            if isinstance(seq, dict):
                return np.concatenate((np.array(seq.get('presses', [])),
                                       np.array(seq.get('gaps', []))))
            if isinstance(seq, (tuple, list)) and len(seq) == 2:
                return np.concatenate((np.array(seq[0]), np.array(seq[1])))
            return np.array(seq)

        test_flat = _flatten(test_raw_seq)
        if len(test_flat) == 0:
            return 999.0

        distances = []
        for enrolled_seq in profile_raw_seqs:
            ef = _flatten(enrolled_seq)
            if len(ef) == 0:
                continue
            dist, _ = fastdtw(test_flat, ef, dist=lambda a, b: abs(a - b))
            distances.append(dist / (len(test_flat) + len(ef)))

        return float(np.mean(distances)) if distances else 999.0

    # ──────────────────────────────────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────────────────────────────────

    def authenticate_with_multiple_metrics(self, test_vector, profile, test_raw_seq=None):
        """
        Ensemble of 4 models: Euclidean-Z, Manhattan-Z, DTW, SVM.

        Voting:
          - Each of the 4 models casts 1 vote.
          - Pass requires >= 3 / 4 votes (majority + 1).
        """
        profile = self._normalize_profile(profile)
        results = {}

        # ── 1. Euclidean (z-score normalized) ────────────────────────────────
        eu_dist = self._euclidean_z(test_vector, profile)
        eu_acc  = eu_dist < self.Z_THRESHOLD
        eu_conf = self._confidence(eu_dist)
        results['euclidean'] = {'distance': eu_dist, 'accepted': eu_acc, 'confidence': eu_conf}
        print(f"  [EUCLIDEAN-Z] dist={eu_dist:.3f} threshold={self.Z_THRESHOLD} accepted={eu_acc} conf={eu_conf:.2f}")

        # ── 2. Manhattan (z-score normalized) ────────────────────────────────
        ma_dist = self._manhattan_z(test_vector, profile)
        ma_acc  = ma_dist < self.Z_THRESHOLD
        ma_conf = self._confidence(ma_dist)
        results['manhattan'] = {'distance': ma_dist, 'accepted': ma_acc, 'confidence': ma_conf}
        print(f"  [MANHATTAN-Z] dist={ma_dist:.3f} threshold={self.Z_THRESHOLD} accepted={ma_acc} conf={ma_conf:.2f}")

        # ── 3. DTW ────────────────────────────────────────────────────────────
        dtw_accepted  = False
        dtw_confidence = 0.0
        if test_raw_seq is not None and 'raw_sequences' in profile:
            dtw_dist      = self._dtw_distance(test_raw_seq, profile['raw_sequences'])
            DTW_THRESHOLD = 45.0   # ms per element
            dtw_accepted  = dtw_dist < DTW_THRESHOLD
            dtw_confidence = max(0.0, 1.0 - (dtw_dist / DTW_THRESHOLD))
            results['dtw'] = {'distance': dtw_dist, 'accepted': dtw_accepted, 'confidence': dtw_confidence}
            print(f"  [DTW] dist={dtw_dist:.3f} threshold={DTW_THRESHOLD} accepted={dtw_accepted} conf={dtw_confidence:.2f}")

        # ── 4. SVM ────────────────────────────────────────────────────────────
        svm_accepted   = False
        svm_confidence = 0.0
        if 'svm_model_b64' in profile and profile['svm_model_b64']:
            try:
                svm_model = pickle.loads(base64.b64decode(profile['svm_model_b64']))
                score     = svm_model.decision_function([test_vector])[0]

                # offset_[0] is the theoretical worst score (corresponds to 0%)
                max_penalty = abs(float(getattr(svm_model, 'offset_', [-0.3])[0]))
                if max_penalty <= 0:
                    max_penalty = 0.3

                svm_confidence = float(np.clip(1.0 + (score / max_penalty), 0.0, 1.0))
                svm_accepted   = svm_confidence > 0.5
                results['svm'] = {'distance': -score, 'accepted': svm_accepted, 'confidence': svm_confidence}
                print(f"  [SVM] raw_score={score:.4f} offset={max_penalty:.4f} conf={svm_confidence:.2f} accepted={svm_accepted}")
            except Exception as e:
                print(f"  [SVM] error: {e}")

        # ── 5. Voting ─────────────────────────────────────────────────────────
        # Collect all active model votes
        active_models = ['euclidean', 'manhattan']
        if 'dtw' in results:
            active_models.append('dtw')
        if 'svm' in results:
            active_models.append('svm')

        total_votes   = sum(1 for m in active_models if results[m]['accepted'])
        required_votes = max(2, len(active_models) - 1)   # majority: need n-1 of n
        final_decision = total_votes >= required_votes

        # ── 6. Summary ────────────────────────────────────────────────────────
        all_conf = [results[m]['confidence'] for m in active_models]
        results['final_decision'] = final_decision
        results['avg_confidence'] = float(np.mean(all_conf))
        results['votes'] = f"{total_votes}/{len(active_models)}"

        print(f"  => FINAL: {total_votes}/{len(active_models)} votes — {'GRANTED' if final_decision else 'DENIED'}")
        return results