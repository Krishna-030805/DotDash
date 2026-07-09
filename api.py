import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from optimized_feature_extractor import OptimizedFeatureExtractor
from enrollment import Enrollment
from matcher import Matcher
import firebase_enhanced

app = Flask(__name__)
# Enable CORS for all routes (to allow React frontend to connect)
CORS(app)

extractor = OptimizedFeatureExtractor()
matcher = Matcher()

@app.route('/api/enroll', methods=['POST'])
def enroll():
    data = request.json
    username = data.get('username')
    decoded_word = data.get('decoded_word')
    samples = data.get('samples', [])
    
    if not username or not samples:
        return jsonify({"error": "Username and samples are required"}), 400
        
    enrollment_session = Enrollment(min_samples=3, max_samples=5)
    
    for sample in samples:
        presses = sample.get('presses', [])
        gaps = sample.get('gaps', [])
        
        feature_vec = extractor.extract(presses, gaps)
        
        # Perfect mock metrics for now, since rhythm is checked by DTW
        metrics = {
            "timing_precision": 0.95,
            "tempo_consistency": 0.95,
            "pattern_accuracy": 1.0,
            "outlier_ratio": 0.0
        }
        
        enrollment_session.add(feature_vec, metrics, raw_sequence=(presses, gaps))
        
    if not enrollment_session.is_complete():
        return jsonify({"error": f"Need at least 3 samples, got {len(samples)}"}), 400
        
    try:
        profile = enrollment_session.build_profile()
        
        password_info = {
            "morse_code": "", # Can be passed from frontend if needed
            "decoded": decoded_word,
            "pattern_count": len(samples[0].get('presses', [])),
            "total_elements": len(samples[0].get('presses', [])) + len(samples[0].get('gaps', []))
        }
        
        success = firebase_enhanced.save_user_profile(username, username, password_info, profile)
        
        if success:
            return jsonify({"status": "success", "message": "Enrolled successfully!"})
        else:
            return jsonify({"status": "error", "message": "Failed to save to Firebase"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.json
    username = data.get('username')
    attempt = data.get('attempt')
    
    if not username or not attempt:
        return jsonify({"error": "Username and attempt data are required"}), 400
        
    user_data = firebase_enhanced.get_user_profile(username)
    if not user_data:
        return jsonify({"error": "User not found"}), 404
        
    # The frontend could send a completely wrong password, so we could check the decoded word.
    # However, for pure biometric testing, we'll just check the rhythm.
    
    presses = attempt.get('presses', [])
    gaps = attempt.get('gaps', [])
    
    test_vector = extractor.extract(presses, gaps)
    profile = user_data.get('biometric_profile')
    
    if not profile:
         return jsonify({"error": "User biometric profile missing"}), 404
         
    results = matcher.authenticate_with_multiple_metrics(
        test_vector, 
        profile, 
        test_raw_seq=(presses, gaps)
    )
    
    def sanitize_for_json(o):
        import numpy as np
        if isinstance(o, dict):
            return {k: sanitize_for_json(v) for k, v in o.items()}
        elif isinstance(o, list):
            return [sanitize_for_json(x) for x in o]
        elif isinstance(o, np.bool_):
            return bool(o)
        elif isinstance(o, (np.integer, np.int64, np.int32)):
            return int(o)
        elif isinstance(o, (np.floating, np.float64, np.float32)):
            return float(o)
        elif isinstance(o, np.ndarray):
            return sanitize_for_json(o.tolist())
        return o
        
    sanitized_results = sanitize_for_json(results)
    
    return jsonify({
        "status": "success",
        "final_decision": sanitized_results.get("final_decision", False),
        "results": sanitized_results
    })

if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
