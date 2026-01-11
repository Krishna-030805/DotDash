"""
Final Integrated Morse Code Auth System
- Fixes 'KeyError: mean' by using robust serialization.
- Adds Numerical Evaluation storage.
"""

# --- IMPORTS ---
try:
    from tap_listener import TapListener
    from optimized_feature_extractor import OptimizedFeatureExtractor as FeatureExtractor
    from enrollment import Enrollment
    from matcher import Matcher
    from morse_codes import MORSE_CODE, get_character_from_morse, display_morse_chart
    from rhythm_analyzer import RhythmAnalyzer
except ImportError as e:
    print(f"\n❌ CRITICAL ERROR: Missing module: {e}")
    exit()

import uuid
import os
import time
import firebase_admin
from firebase_admin import credentials, db
import numpy as np

# ==========================================
# 1. FIREBASE CONFIGURATION
# ==========================================
KEY_PATH = "serviceAccountKey.json"  # Your Firebase service account key
DB_URL = "URL of your Firebase Realtime Database"  # Your Firebase Realtime Database URL

os.environ["GOOGLE_CLOUD_DISABLE_GRPC"] = "true"
os.environ["NO_GCE_CHECK"] = "true"

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(KEY_PATH)
        firebase_admin.initialize_app(cred, {'databaseURL': DB_URL, 'httpTimeout': 30})
        print("✅ Firebase Connection Established.")
    except Exception as e:
        print(f"\n❌ FIREBASE INIT ERROR: {e}")
        exit(1)

# ==========================================
# 2. DATA HELPER (The Fix for 'Mean' Error)
# ==========================================
def make_serializable(data):
    """
    Recursively converts Numpy data types to standard Python types
    so they can be saved to Firebase without errors.
    """
    if isinstance(data, dict):
        return {k: make_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_serializable(i) for i in data]
    elif isinstance(data, np.ndarray):
        return make_serializable(data.tolist())
    elif isinstance(data, (np.float32, np.float64, np.int32, np.int64)):
        return float(data) # Firebase handles floats well
    else:
        return data

# ==========================================
# 3. DATABASE FUNCTIONS
# ==========================================
def get_user_profile(username):
    try:
        ref = db.reference(f'users/{username}')
        return ref.get()
    except Exception as e:
        print(f"⚠️  DB Read Error: {e}")
        return None

def save_user_profile(user_id, username, password_info, profile, evaluations):
    """
    Saves profile + evaluations to Firebase.
    Uses make_serializable() to ensure NO data is lost.
    """
    try:
        ref = db.reference(f'users/{username}')
        
        # 1. Clean the complex objects
        clean_profile = make_serializable(profile)
        clean_evals = make_serializable(evaluations)

        user_data = {
            "user_id": user_id,
            "username": username,
            "created_at": time.ctime(),
            "timestamp": time.time(),
            
            # Password Info
            "decoded_word": password_info['decoded'],
            "morse_code": password_info['morse_code'],
            "pattern_count": password_info.get('pattern_count', 0),
            "total_elements": password_info.get('total_elements', 0),
            
            # The Critical Data
            "biometric_profile": clean_profile,
            "enrollment_metrics": clean_evals
        }
        
        ref.set(user_data)
        print("✅ User profile and evaluations saved to cloud.")
        
    except Exception as e:
        print(f"❌ DB Save Error: {e}")

def list_all_users():
    try:
        ref = db.reference('users')
        users_dict = ref.get()
        return list(users_dict.values()) if users_dict else []
    except Exception as e:
        print(f"⚠️  DB List Error: {e}")
        return []

# ==========================================
# 4. UI HELPERS
# ==========================================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def show_tapping_instructions(password_info):
    print("\n" + "-" * 50)
    print(f" PASSWORD: {password_info['decoded']}  ({password_info['morse_code']})")
    print(" INSTRUCTIONS: Tap SPACE for dots/dashes. Press ESC to finish.")
    print("-" * 50)

# ==========================================
# 5. CORE LOGIC
# ==========================================
def get_morse_password():
    # Simplified for brevity, assumes you have this logic or stick to the one from previous turn
    print_header("PASSWORD SETUP")
    while True:
        txt = input("\n🔐 Enter Morse (e.g., ... --- ...): ").strip()
        if not txt: continue
        # Basic decode check
        patterns = txt.split()
        decoded = ""
        for p in patterns:
            decoded += get_character_from_morse(p) or "?"
        
        print(f"   Decoded: {decoded}")
        if input("   Confirm? (y/n): ").lower() == 'y':
            return {
                'morse_code': txt, 
                'decoded': decoded, 
                'total_elements': sum(len(p) for p in patterns)
            }

def register_new_user():
    print_header("NEW USER REGISTRATION")
    
    # 1. Username
    while True:
        username = input("\n👤 Enter username: ").strip()
        if not username: continue
        if get_user_profile(username):
            print("❌ User exists.")
            continue
        break
    
    # 2. Password
    password_info = get_morse_password()
    
    # 3. Setup Analyzers
    extractor = FeatureExtractor(dot_dash_threshold_ratio=2.0)
    rhythm_analyzer = RhythmAnalyzer()
    enroller = Enrollment(min_samples=3, max_samples=5)
    
    accepted_scores = [] # <--- Store scores for DB
    
    print("\n--- ENROLLMENT STARTING ---")
    
    attempt = 1
    while not enroller.is_complete():
        print(f"\n📢 Attempt {attempt}/{enroller.max_samples}")
        show_tapping_instructions(password_info)
        
        input("  Press ENTER to record...")
        listener = TapListener()
        listener.start()
        presses, gaps = listener.get_sequences()
        
        if not presses:
            print("❌ No input.")
            continue
            
        # Analyze
        rhythm_score = rhythm_analyzer.analyze_rhythm(presses, gaps, password_info)
        feature_vector = extractor.extract(presses, gaps)
        result = enroller.add(feature_vector, rhythm_score)
        
        if result['status'] == 'accepted':
            print("✅ Sample Accepted")
            accepted_scores.append(rhythm_score)
        else:
            print("❌ Sample Rejected (Inconsistent)")
            
        print(f"   Samples: {result['samples_collected']}/3 required")
        
        if enroller.is_complete():
            break
        attempt += 1

    # 4. Calculate Average Evaluations
    print("\n⚙️  Calculating user metrics...")
    final_evals = {
        "overall_score": 0.0,
        "tempo_consistency": 0.0,
        "pattern_accuracy": 0.0,
        "timing_precision": 0.0
    }
    
    if accepted_scores:
        count = len(accepted_scores)
        for key in final_evals:
            # Safely sum keys if they exist
            total = sum(s.get(key, 0) for s in accepted_scores)
            final_evals[key] = round(total / count, 4)

    # 5. Save EVERYTHING
    profile = enroller.build_profile()
    user_id = str(uuid.uuid4())
    
    save_user_profile(user_id, username, password_info, profile, final_evals)
    
    print_header("REGISTRATION COMPLETE")
    print(f"User: {username} | Accuracy: {final_evals['pattern_accuracy']:.1%}")
    input("Press ENTER...")

def authenticate_user():
    print_header("AUTHENTICATION")
    username = input("\n👤 Username: ").strip()
    if not username: return
    
    # 1. Fetch
    user_data = get_user_profile(username)
    if not user_data:
        print("❌ User not found.")
        return

    # 2. Extract Profile (With Debugging)
    profile = user_data.get('biometric_profile')
    if not profile:
        print("❌ CRITICAL: Profile is empty/corrupt. Register this user again.")
        return
        
    # DEBUG: Print keys to ensure 'mean' or equivalent exists
    # print(f"DEBUG KEYS: {profile.keys()}") 

    # password_info = {
    #     'morse_code': user_data.get('morse_code', ''),
    #     'decoded': user_data.get('decoded_word', ''),
    #     'total_elements': user_data.get('total_elements', 0)
    # }

    # 3. Capture
    # show_tapping_instructions()
    input("  Press ENTER to authenticate...")
    
    listener = TapListener()
    listener.start()
    presses, gaps = listener.get_sequences()
    
    if not presses:
        print("❌ No input.")
        return

    # 4. Match
    extractor = FeatureExtractor(dot_dash_threshold_ratio=2.0)
    test_vector = extractor.extract(presses, gaps)
    
    matcher = Matcher(use_dynamic_threshold=True, metric='euclidean')
    
    # THIS is where the error likely happened before.
    # Now that 'profile' is fully populated, it should work.
    try:
        results = matcher.authenticate_with_multiple_metrics(test_vector, profile)
        
        print("\n--- RESULTS ---")
        if results['final_decision']:
            print("✅ ACCESS GRANTED")
        else:
            print("❌ ACCESS DENIED")
        
        print(f"Confidence: {results.get('avg_confidence', 0):.1%}")
    except KeyError as e:
        print(f"\n❌ MATCHING ERROR: Missing key {e}")
        print("   Solution: The Enroller and Matcher are looking for different keys.")
        print(f"   Database has: {list(profile.keys())}")

    input("Press ENTER...")

def show_statistics():
    print_header("STATISTICS")
    users = list_all_users()
    if not users:
        print("No users.")
    else:
        print(f"{'USER':<15} | {'ACCURACY':<10} | {'CONSISTENCY':<10}")
        print("-" * 40)
        for u in users:
            name = u.get('username', '?')
            # Get evaluations from the new node
            evals = u.get('enrollment_metrics', {})
            acc = evals.get('pattern_accuracy', 0)
            # Get consistency from profile
            prof = u.get('biometric_profile', {})
            cons = prof.get('consistency_score', 0)
            
            print(f"{name:<15} | {acc:>8.1%} | {cons:>8.1%}")
    input("Press ENTER...")

# ==========================================
# 6. RUN
# ==========================================
def main():
    while True:
        clear_screen()
        print("\n1. Register\n2. Login\n3. Stats\n4. Exit")
        c = input("Select: ")
        if c == '1': register_new_user()
        elif c == '2': authenticate_user()
        elif c == '3': show_statistics()
        elif c == '4': break

if __name__ == "__main__":
    main()