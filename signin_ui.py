"""
===============================================================================
INTEGRATED SIGN-IN UI - FIXED VERSION
===============================================================================
This file handles user authentication by:
1. Fetching user profile from Firebase
2. Recording the user's tap pattern
3. Comparing against enrolled biometric profile
4. Granting or denying access based on match
===============================================================================
"""

import tkinter as tk
from tkinter import messagebox
import time
import numpy as np

# ==========================================
# IMPORT BACKEND MODULES
# ==========================================
try:
    from optimized_feature_extractor import OptimizedFeatureExtractor as FeatureExtractor
    from matcher import Matcher
    from rhythm_analyzer import RhythmAnalyzer
except ImportError as e:
    print(f"❌ ERROR: Missing required module - {e}")
    exit(1)

# ==========================================
# FIREBASE SETUP
# ==========================================
import firebase_admin
from firebase_admin import credentials, db
import os

KEY_PATH = "serviceAccountKey.json"  # Your Firebase service account key
DB_URL = "URL of your Firebase Realtime Database"  # Your Firebase Realtime Database URL

os.environ["GOOGLE_CLOUD_DISABLE_GRPC"] = "true"
os.environ["NO_GCE_CHECK"] = "true"

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(KEY_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': DB_URL,
            'httpTimeout': 30
        })
        print("✅ Firebase Connected")
    except Exception as e:
        print(f"❌ Firebase Error: {e}")


# ==========================================
# DATABASE HELPER
# ==========================================
def get_user_profile(username):
    """Retrieve user profile from Firebase"""
    try:
        ref = db.reference(f'users/{username}')
        return ref.get()
    except Exception as e:
        print(f"⚠️ DB Read Error: {e}")
        return None


# ==========================================
# COLORS
# ==========================================
BG_COLOR = "#0f172a"
PRIMARY_BTN = "#38bdf8"
TEXT_COLOR = "#FFFFFF"
SUBTEXT_COLOR = "#94a3b8"
BTN_TEXT = "#111827"
INPUT_BG = "#020617"
SUCCESS = "#22c55e"
ERROR = "#ef4444"
SURFACE = "#1e293b"


# ==========================================
# MAIN APPLICATION
# ==========================================
class SignInApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sign In - Morse Authentication")
        self.root.geometry("900x650")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # Backend components
        self.extractor = FeatureExtractor(dot_dash_threshold_ratio=2.0)
        self.matcher = Matcher(use_dynamic_threshold=True, metric='euclidean')

        # Recording state
        self.recording_active = False
        self.press_times = []
        self.release_times = []
        self.space_is_down = False

        self.setup_ui()

        # Bind recording keys
        self.root.bind("<space>", self.on_space_press)
        self.root.bind("<KeyRelease-space>", self.on_space_release)
        self.root.bind("<Return>", self.on_enter_pressed)

    def setup_ui(self):
        """Setup the complete UI"""
        # Main frame
        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.pack(expand=True)

        # Title
        tk.Label(
            frame,
            text="🔐 Secure Sign In",
            font=("Helvetica", 28, "bold"),
            fg=TEXT_COLOR,
            bg=BG_COLOR
        ).pack(pady=(0, 10))

        tk.Label(
            frame,
            text="Authenticate with your unique rhythm pattern",
            font=("Helvetica", 12),
            fg=SUBTEXT_COLOR,
            bg=BG_COLOR
        ).pack(pady=(0, 40))

        # Username input
        tk.Label(
            frame,
            text="Username",
            font=("Helvetica", 13, "bold"),
            fg=TEXT_COLOR,
            bg=BG_COLOR
        ).pack(anchor="w", padx=250)

        self.username_entry = tk.Entry(
            frame,
            font=("Helvetica", 14),
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            width=32,
            relief="flat",
            highlightbackground=PRIMARY_BTN,
            highlightthickness=2
        )
        self.username_entry.pack(pady=(8, 35), ipady=8)

        # Status display area (no password shown)
        self.pattern_display = tk.Label(
            frame,
            text="Enter your username and authenticate",
            font=("Helvetica", 12),
            fg=SUBTEXT_COLOR,
            bg=BG_COLOR,
            width=40,
            height=3
        )
        self.pattern_display.pack(pady=20)

        # Info card
        info_frame = tk.Frame(frame, bg=SURFACE, relief="solid", borderwidth=1)
        info_frame.pack(pady=20, padx=80, fill="x")

        tk.Label(
            info_frame,
            text="🎵 Authentication Process",
            font=("Helvetica", 14, "bold"),
            fg=PRIMARY_BTN,
            bg=SURFACE
        ).pack(pady=(15, 5))

        tk.Label(
            info_frame,
            text="1. Enter your username\n"
                 "2. Click AUTHENTICATE\n"
                 "3. Your pattern will be shown\n"
                 "4. Tap it using SPACEBAR\n"
                 "5. Press ENTER when done",
            font=("Helvetica", 11),
            fg=SUBTEXT_COLOR,
            bg=SURFACE,
            justify="left"
        ).pack(pady=(0, 15))

        # Authenticate button
        tk.Button(
            frame,
            text="AUTHENTICATE",
            font=("Helvetica", 14, "bold"),
            bg=PRIMARY_BTN,
            fg=BTN_TEXT,
            width=22,
            height=2,
            relief="flat",
            command=self.start_authentication,
            cursor="hand2"
        ).pack(pady=25)

        # Status label
        self.status_label = tk.Label(
            frame,
            text="",
            font=("Helvetica", 12),
            bg=BG_COLOR
        )
        self.status_label.pack(pady=15)

        # Footer
        tk.Label(
            self.root,
            text="Biometric rhythm authentication • DotDash Labs",
            fg=SUBTEXT_COLOR,
            bg=BG_COLOR,
            font=("Helvetica", 10)
        ).pack(side="bottom", pady=20)

    def start_authentication(self):
        """Start the authentication process"""
        username = self.username_entry.get().strip()

        # Validation
        if not username:
            messagebox.showerror("Error", "Please enter your username")
            return

        self.status_label.config(text="🔍 Loading user profile...", fg=SUBTEXT_COLOR)
        self.root.update()

        # Fetch user data
        user_data = get_user_profile(username)

        if not user_data:
            self.status_label.config(text="", fg=TEXT_COLOR)
            messagebox.showerror(
                "User Not Found",
                f"Username '{username}' does not exist.\n\n"
                "Please check your username or enroll first."
            )
            return

        # Extract profile
        profile = user_data.get('biometric_profile')
        if not profile:
            messagebox.showerror(
                "Error",
                "User profile is corrupted. Please re-enroll."
            )
            return

        # Store for authentication
        self.current_username = username
        self.user_profile = profile
        self.password_info = {
            'morse_code': user_data.get('morse_code', ''),
            'decoded': user_data.get('decoded_word', ''),
            'total_elements': user_data.get('total_elements', 0)
        }

        # Update display (no pattern shown)
        self.pattern_display.config(
            text="User verified. Tap your pattern to authenticate."
        )

        msg = f"👤 User: {username}\n\n"
        msg += f"🔒 Authentication Required\n\n"
        msg += f"Instructions:\n"
        msg += f"1. Press OK to start recording\n"
        msg += f"2. Tap your enrolled pattern using SPACEBAR\n"
        msg += f"3. Press ENTER when done\n\n"
        msg += f"⚠️ Your unique rhythm will be verified."

        messagebox.showinfo("Ready to Authenticate", msg)

        # Start recording
        self.start_recording()

    def start_recording(self):
        """Start recording tap pattern"""
        self.recording_active = True
        self.press_times = []
        self.release_times = []
        self.space_is_down = False

        self.status_label.config(
            text="🔴 RECORDING... Tap your pattern! (Press ENTER when done)",
            fg=ERROR
        )

        self.pattern_display.config(
            text="🔴 Recording in progress...\n\nTap your pattern now"
        )

        self.root.focus_force()
        self.root.update()

    def on_space_press(self, event):
        """Handle spacebar press"""
        if not self.recording_active:
            return "break"

        if self.space_is_down:
            return "break"

        self.space_is_down = True
        now = time.time()
        self.press_times.append(now)

        # Update display - show tap count only
        self.pattern_display.config(
            text=f"🔴 Recording...\n\nTaps recorded: {len(self.press_times)}"
        )

        return "break"

    def on_space_release(self, event):
        """Handle spacebar release"""
        if not self.recording_active:
            return "break"

        if not self.space_is_down:
            return "break"

        self.space_is_down = False
        now = time.time()
        self.release_times.append(now)

        # Update display
        self.pattern_display.config(
            text=f"🔴 Recording...\n\nTaps recorded: {len(self.press_times)}"
        )

        return "break"

    def on_enter_pressed(self, event):
        """Handle Enter key"""
        if self.recording_active:
            self.finish_recording()
            return "break"
        return None

    def finish_recording(self):
        """Process the recorded pattern"""
        if not self.recording_active:
            return

        self.recording_active = False

        # Reset display
        self.pattern_display.config(
            text="Verifying your pattern..."
        )

        # Calculate presses and gaps
        presses = []
        gaps = []

        count = min(len(self.press_times), len(self.release_times))

        if count == 0:
            messagebox.showwarning(
                "No Input",
                "No tapping detected.\n\nTry again!"
            )
            self.status_label.config(text="", fg=TEXT_COLOR)
            return

        # Calculate press durations
        for i in range(count):
            duration = self.release_times[i] - self.press_times[i]
            if duration >= 0:
                presses.append(duration)

        # Calculate gaps
        for i in range(1, count):
            gap = self.press_times[i] - self.release_times[i - 1]
            if gap >= 0:
                gaps.append(gap)

        print(f"Recorded: {len(presses)} presses, {len(gaps)} gaps")

        # Authenticate
        self.authenticate_pattern(presses, gaps)

    def authenticate_pattern(self, presses, gaps):
        """Authenticate the tapped pattern"""
        self.status_label.config(text="🔐 Verifying pattern...", fg=SUBTEXT_COLOR)
        self.root.update()

        try:
            # First check: Did they tap the right number of elements?
            expected_elements = self.password_info['total_elements']
            actual_elements = len(presses)

            print(f"Expected elements: {expected_elements}, Got: {actual_elements}")

            # Extract features from test pattern
            test_vector = self.extractor.extract(presses, gaps)
            print(f"Test vector extracted: {len(test_vector)} features")

            # Perform multi-metric authentication
            results = self.matcher.authenticate_with_multiple_metrics(
                test_vector,
                self.user_profile
            )

            print(f"Authentication results: {results}")

            # Get results
            final_decision = results['final_decision']
            avg_confidence = results.get('avg_confidence', 0)
            votes = results.get('votes', '0/3')

            # Show results
            if final_decision:
                # ACCESS GRANTED
                self.status_label.config(text="✅ Authentication Successful", fg=SUCCESS)

                msg = f"✅ ACCESS GRANTED\n\n"
                msg += f"Welcome, {self.current_username}!\n\n"
                msg += f"Authentication successful.\n"
                msg += f"Confidence: {avg_confidence:.1%}\n"
                msg += f"Match: {votes}"

                messagebox.showinfo("Access Granted ✅", msg)

                # Reset for next login
                self.username_entry.delete(0, tk.END)
                self.pattern_display.config(
                    text="Enter your username and authenticate"
                )
                self.status_label.config(text="", fg=TEXT_COLOR)

            else:
                # ACCESS DENIED - Simple message
                self.status_label.config(text="❌ Access Denied", fg=ERROR)

                msg = f"❌ ACCESS DENIED\n\n"
                msg += f"Authentication failed.\n\n"
                msg += f"Possible reasons:\n"
                msg += f"• Wrong pattern\n"
                msg += f"• Incorrect rhythm\n"
                msg += f"• Biometric mismatch\n\n"
                msg += f"Match score: {avg_confidence:.1%}\n"
                msg += f"Required: 2/3 metrics\n"
                msg += f"Result: {votes}"

                messagebox.showerror("Access Denied ❌", msg)

        except Exception as e:
            self.status_label.config(text="❌ Authentication Error", fg=ERROR)
            messagebox.showerror(
                "Error",
                f"Authentication failed:\n\n{str(e)}"
            )
            print(f"Authentication error: {e}")
            import traceback
            traceback.print_exc()


# ==========================================
# RUN APPLICATION
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = SignInApp(root)
    root.mainloop()