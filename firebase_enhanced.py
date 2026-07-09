# -*- coding: utf-8 -*-
"""
Enhanced Firebase Database Module
==================================
Provides complete user management:
1. Save new user profiles
2. Retrieve existing user profiles
3. Update user profiles
4. List all users
5. Delete users
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import numpy as np


# Initialize Firebase (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client(database_id="morse-auth")


def save_user_profile(user_id, username, password_info, profile):
    try:
        def to_list(v):
            """Convert numpy arrays/matrices to plain Python lists for Firestore."""
            import numpy as np
            if isinstance(v, np.ndarray):
                return v.tolist()
            if isinstance(v, list):
                return [to_list(i) for i in v]
            if isinstance(v, (np.integer,)):
                return int(v)
            if isinstance(v, (np.floating,)):
                return float(v)
            return v

        import numpy as np
        # Firestore does NOT support nested arrays.
        # Flatten cov_matrix from 32x32 -> 1024 flat list, store shape alongside.
        cov = profile.get("cov_matrix", [])
        cov_arr = np.array(cov)
        cov_flat = cov_arr.flatten().tolist() if cov_arr.ndim == 2 else to_list(cov)
        cov_shape = list(cov_arr.shape) if cov_arr.ndim == 2 else []

        data = {
            "user_id": user_id,
            "username": username,
            "morse_code": password_info["morse_code"],
            "decoded_word": password_info["decoded"],
            "pattern_count": password_info["pattern_count"],
            "total_elements": password_info["total_elements"],
            "biometric_profile": {
                # Canonical field names (used by matcher)
                "mean": to_list(profile.get("mean", profile.get("mean_vector", []))),
                "std": to_list(profile.get("std", profile.get("std_vector", []))),
                "cov_matrix_flat": cov_flat,
                "cov_matrix_shape": cov_shape,
                "recommended_threshold": float(profile.get("recommended_threshold", 65.0)),
                # Legacy alias
                "mean_vector": to_list(profile.get("mean", profile.get("mean_vector", []))),
                # Metadata
                "sample_count": int(profile.get("sample_count", 0)),
                "consistency_score": float(profile.get("consistency_score", 0.0)),
                "raw_sequences": profile.get("raw_sequences", []),
                "svm_model_b64": profile.get("svm_model_b64", "")
            },
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }

        db.collection("morse_auth_profiles").document(username).set(data)
        print(f"Profile saved to Firebase for user: {username}")
        return True

    except Exception as e:
        print(f"Error saving profile: {e}")
        return False


def get_user_profile(username):
    try:
        doc = db.collection("morse_auth_profiles").document(username).get()
        if not doc.exists:
            return None

        data = doc.to_dict()
        return data

    except Exception as e:
        print(f"❌ Error retrieving profile: {e}")
        return None


def update_user_profile(username, new_profile):
    """
    Update an existing user's biometric profile.
    Useful for adaptive learning systems.
    
    Args:
        username (str): Username to update
        new_profile (dict): New biometric profile data
    
    Returns:
        bool: True if successful
    """
    try:
        doc_ref = db.collection("morse_auth_profiles").document(username)
        
        # Check if user exists
        if not doc_ref.get().exists:
            print(f"❌ User '{username}' not found.")
            return False
        
        update_data = {
            "biometric_profile": {
                "mean_vector": new_profile["mean"].tolist(),
                "std_vector": new_profile["std"].tolist(),
                "consistency_score": float(new_profile["consistency_score"]),
                "recommended_threshold": float(new_profile["recommended_threshold"]),
                "sample_count": int(new_profile["sample_count"])
            },
            "last_updated": datetime.now().isoformat()
        }
        
        doc_ref.update(update_data)
        print(f"✅ Profile updated for user: {username}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating profile: {e}")
        return False


def delete_user_profile(username):
    """
    Delete a user profile from Firebase.
    
    Args:
        username (str): Username to delete
    
    Returns:
        bool: True if successful
    """
    try:
        db.collection("morse_auth_profiles").document(username).delete()
        print(f"✅ Profile deleted for user: {username}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting profile: {e}")
        return False


def list_all_users():
    """
    List all registered users.
    
    Returns:
        list: List of user dictionaries
    """
    try:
        docs = db.collection("morse_auth_profiles").stream()
        
        users = []
        for doc in docs:
            data = doc.to_dict()
            users.append({
                'username': data.get('username'),
                'decoded_word': data.get('decoded_word'),
                'pattern_count': data.get('pattern_count'),
                'consistency_score': data.get('biometric_profile', {}).get('consistency_score', 0),
                'created_at': data.get('created_at', 'N/A')
            })
        
        return users
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []


def user_exists(username):
    """
    Check if a username already exists.
    
    Args:
        username (str): Username to check
    
    Returns:
        bool: True if exists
    """
    try:
        doc = db.collection("morse_auth_profiles").document(username).get()
        return doc.exists
    except:
        return False


def get_user_statistics():
    """
    Get aggregated statistics about all users.
    
    Returns:
        dict: Statistics summary
    """
    try:
        users = list_all_users()
        
        if not users:
            return {
                'total_users': 0,
                'avg_consistency': 0,
                'most_common_length': 0
            }
        
        consistency_scores = [u['consistency_score'] for u in users]
        pattern_lengths = [u['pattern_count'] for u in users]
        
        from collections import Counter
        most_common = Counter(pattern_lengths).most_common(1)
        
        return {
            'total_users': len(users),
            'avg_consistency': sum(consistency_scores) / len(consistency_scores),
            'most_common_length': most_common[0][0] if most_common else 0,
            'consistency_range': (min(consistency_scores), max(consistency_scores)) if consistency_scores else (0, 0)
        }
        
    except Exception as e:
        print(f"❌ Error calculating statistics: {e}")
        return {}


# Testing functions
if __name__ == "__main__":
    print("🧪 Testing Firebase Database Module")
    
    # Test user listing
    print("\n📋 Current users:")
    users = list_all_users()
    for user in users:
        print(f"  - {user['username']}: {user['decoded_word']}")
    
    # Test statistics
    stats = get_user_statistics()
    print(f"\n📊 Statistics:")
    print(f"  Total users: {stats.get('total_users', 0)}")
    print(f"  Avg consistency: {stats.get('avg_consistency', 0):.1%}")
