# DotDash: Morse Code Biometric Authentication System

DotDash is an advanced behavioral biometrics authentication system. Instead of relying solely on *what* you type (a password), it authenticates you based on *how* you type it (your unique keystroke rhythm). By typing a Morse code password, the system captures your exact millisecond timings and uses an ensemble of Machine Learning models to verify your identity.

## 🧠 How It Works (The ML Ensemble)

The system extracts a **32-dimensional optimized feature vector** from your typing, including press durations, gap durations, statistical moments (mean, std, skewness), and temporal dynamics (acceleration, rhythm stability).

During authentication, your typing is evaluated against a 4-model ensemble:

1. **Euclidean Distance (Z-Score Normalized)**: Measures the straight-line distance of your features from your enrolled mean, normalized by standard deviation.
2. **Manhattan Distance (Z-Score Normalized)**: Measures absolute variance across features, providing robustness against single-feature outliers.
3. **Dynamic Time Warping (DTW)**: Compares the raw temporal sequence of your presses and gaps, forgiving overall speed changes while verifying the relative rhythm.
4. **One-Class Support Vector Machine (SVM)**: A non-linear boundary drawn around your enrolled samples in high-dimensional space. The raw `decision_function` score is dynamically mapped to a 0-100% confidence scale based on the model's computed max-penalty offset.

**Voting Mechanism**: To successfully log in, your attempt must pass a majority vote (e.g., at least 3 out of 4 models must accept the attempt).

## 🏗️ Architecture

- **Frontend (`/Authentication System Frontend`)**: A modern React application (using Vite) that acts as the Morse code key. It records accurate millisecond timings for `mousedown` and `mouseup` events and displays live ML confidence metrics in a beautiful dashboard.
- **Backend (`api.py`)**: A Flask REST API that handles feature extraction, model training during enrollment, and the multi-metric authentication logic.
- **Database (`firebase_enhanced.py`)**: Google Cloud Firestore stores user credentials and biometric profiles. Complex structures like the 32x32 Covariance Matrix and the One-Class SVM model are flattened and base64-serialized for Firebase compatibility.

## 🚀 Getting Started

### 1. Start the Flask Backend
Make sure you have your Firebase `serviceAccountKey.json` in the root directory.
```bash
# Install dependencies
pip install flask flask-cors numpy scipy scikit-learn fastdtw firebase-admin

# Run the API
python api.py
```
*The server will run on `http://127.0.0.1:5000`*

### 2. Start the React Frontend
```bash
cd "Authentication System Frontend"

# Install dependencies
npm install

# Start the dev server
npm run dev
```

## 🔒 Enrollment & Security Note
During registration, you must provide 3 to 5 samples of your Morse code password. It is highly recommended to type naturally and consistently. If your enrollment samples are too erratic, the system will widen its acceptance threshold, making it slightly easier for imposters. Consistent enrollment yields a tight, highly secure biometric boundary.
