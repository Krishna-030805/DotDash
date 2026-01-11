"""
===============================================================================
INTEGRATED ENROLLMENT UI - CLEAN VERSION
===============================================================================
This file creates a user enrollment interface where users can:
1. Enter their username
2. Type a Morse code pattern (dots and dashes)
3. Record biometric rhythm samples by tapping
4. Save everything to Firebase

The system captures not just WHAT they type, but HOW they tap it (rhythm/timing)
===============================================================================
"""

import tkinter as tk
import time
import uuid
import numpy as np
from tkinter import messagebox

# ==========================================
# IMPORT BACKEND MODULES
# ==========================================
# These are your existing Python files that handle the logic
try:
    from tap_listener import TapListener  # Captures keyboard tapping
    from optimized_feature_extractor import OptimizedFeatureExtractor as FeatureExtractor  # Extracts biometric features
    from enrollment import Enrollment  # Handles enrollment logic
    from rhythm_analyzer import RhythmAnalyzer  # Analyzes rhythm quality
    from morse_codes import MORSE_CODE, get_character_from_morse  # Morse code dictionary
except ImportError as e:
    print(f"❌ ERROR: Missing required module - {e}")
    print("Make sure all backend files are in the same directory!")
    exit(1)

# ==========================================
# FIREBASE SETUP
# ==========================================
import firebase_admin
from firebase_admin import credentials, db
import os

# Firebase configuration
KEY_PATH = "serviceAccountKey.json"  # Your Firebase service account key
DB_URL = "URL of your Firebase Realtime Database"  # Your Firebase Realtime Database URL

# These environment variables fix connection issues
os.environ["GOOGLE_CLOUD_DISABLE_GRPC"] = "true"
os.environ["NO_GCE_CHECK"] = "true"

# Initialize Firebase (only once)
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(KEY_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': DB_URL,
            'httpTimeout': 30
        })
        print("✅ Firebase Connected Successfully")
    except Exception as e:
        print(f"❌ Firebase Connection Error: {e}")
        print("Check that 'fresh key.json' exists and DATABASE_URL is correct")


# ==========================================
# HELPER FUNCTIONS FOR FIREBASE
# ==========================================

def make_serializable(data):
    """
    Convert numpy arrays to regular Python types.
    Firebase can't save numpy types directly, so we convert them.
    """
    if isinstance(data, dict):
        return {k: make_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_serializable(i) for i in data]
    elif isinstance(data, np.ndarray):
        return data.tolist()  # Convert numpy array to list
    elif isinstance(data, (np.float32, np.float64, np.int32, np.int64)):
        return float(data)  # Convert numpy number to Python float
    else:
        return data


def save_user_to_firebase(user_id, username, password_info, profile, evaluations):
    """
    Save complete user profile to Firebase Realtime Database.

    Structure:
    users/
      username/
        - user_id: unique identifier
        - username: the username
        - decoded_word: the actual password (e.g., "SOS")
        - morse_code: the Morse pattern (e.g., "... --- ...")
        - biometric_profile: the rhythm/timing fingerprint
        - enrollment_metrics: quality scores
    """
    try:
        ref = db.reference(f'users/{username}')

        # Clean data for Firebase
        clean_profile = make_serializable(profile)
        clean_evals = make_serializable(evaluations)

        user_data = {
            "user_id": user_id,
            "username": username,
            "created_at": time.ctime(),
            "timestamp": time.time(),
            "decoded_word": password_info['decoded'],
            "morse_code": password_info['morse_code'],
            "pattern_count": password_info.get('pattern_count', 0),
            "total_elements": password_info.get('total_elements', 0),
            "biometric_profile": clean_profile,
            "enrollment_metrics": clean_evals
        }

        ref.set(user_data)
        return True
    except Exception as e:
        print(f"❌ Firebase Save Error: {e}")
        return False


def check_user_exists(username):
    """Check if a username is already taken"""
    try:
        ref = db.reference(f'users/{username}')
        return ref.get() is not None
    except:
        return False


# ==========================================
# UI COLOR SCHEME
# ==========================================
BG = "#111827"  # Dark blue-gray background
SURFACE = "#0F172A"  # Slightly darker for panels
TEXT = "#F9FAFB"  # White text
ACCENT = "#38BDF8"  # Bright blue for highlights
BORDER = "#334155"  # Gray for borders
SUCCESS = "#22c55e"  # Green for success messages
ERROR = "#ef4444"  # Red for error messages
SUBTEXT_COLOR = "#94a3b8"  # Light gray for helper text

# ==========================================
# MORSE CODE LOOKUP TABLES
# ==========================================
MORSE_TABLE = MORSE_CODE  # From morse_codes.py
REVERSE_MORSE = {v: k for k, v in MORSE_TABLE.items()}  # For decoding


# ==========================================
# MAIN APPLICATION CLASS
# ==========================================
class EnrollmentApp:
    """
    Main application for user enrollment.
    This creates the window and handles all user interactions.
    """

    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        self.root.title("DotDash Labs — User Enrollment")
        self.root.geometry("1050x650")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # State variables
        self.morse_groups = []  # List of Morse patterns entered

        # Recording state
        self.recording_active = False
        self.press_times = []
        self.release_times = []
        self.space_is_down = False
        self.last_release_time = None

        # Backend components (initialized once)
        self.extractor = FeatureExtractor(dot_dash_threshold_ratio=2.0)
        self.rhythm_analyzer = RhythmAnalyzer()
        self.enroller = Enrollment(min_samples=3, max_samples=5)
        self.accepted_scores = []  # Stores quality scores of accepted samples
        self.enrollment_attempt = 0

        # Build the user interface
        self.setup_ui()

        # Bind recording keys (always active, but only work when recording_active=True)
        self.root.bind("<space>", self.on_record_space_press)
        self.root.bind("<KeyRelease-space>", self.on_record_space_release)
        self.root.bind("<Return>", self.on_enter_pressed)

    def setup_ui(self):
        """Create all the visual elements"""
        # Split window into left and right panels
        left_panel = tk.Frame(self.root, bg=BG)
        left_panel.pack(side="left", padx=24, pady=16, fill="both", expand=True)

        right_panel = tk.Frame(self.root, bg=BG)
        right_panel.pack(side="right", padx=24, pady=16)

        # Build the panels
        self.setup_left_panel(left_panel)
        self.setup_morse_reference(right_panel)

    def setup_left_panel(self, parent):
        """Setup the main input area (left side)"""

        # === HEADER ===
        tk.Label(
            parent,
            text="DotDash Labs",
            font=("Arial", 22, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(pady=6)

        tk.Label(
            parent,
            text="Enter Morse Code: Use . (dot) and - (dash) • Separate characters with SPACE",
            fg=TEXT,
            bg=BG,
            font=("Arial", 10)
        ).pack(pady=(4, 14))

        # === USERNAME INPUT ===
        tk.Label(
            parent,
            text="Username",
            fg=TEXT,
            bg=BG,
            font=("Arial", 12, "bold")
        ).pack(anchor="w")

        self.user_entry = tk.Entry(
            parent,
            width=38,
            bg="#020617",
            fg="#FFFFFF",
            insertbackground="#F9FAFB",
            highlightbackground=ACCENT,
            highlightthickness=1,
            relief="flat",
            font=("Arial", 11)
        )
        self.user_entry.pack(pady=(4, 10))

        # === MORSE CODE INPUT TEXTBOX ===
        tk.Label(
            parent,
            text="Morse Code Pattern",
            font=("Arial", 14, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(anchor="w", pady=(10, 4))

        self.morse_input = tk.Entry(
            parent,
            width=38,
            bg="#020617",
            fg=ACCENT,
            insertbackground=ACCENT,
            highlightbackground=ACCENT,
            highlightthickness=2,
            relief="flat",
            font=("Courier", 14, "bold")
        )
        self.morse_input.pack(pady=(4, 4))

        # Bind the textbox to auto-decode on every keystroke
        self.morse_input.bind("<KeyRelease>", self.on_morse_input_change)

        # Helper text with examples
        tk.Label(
            parent,
            text="Example: ... --- ... (for SOS) • ... .- -- (for SAM)",
            fg=SUBTEXT_COLOR,
            bg=BG,
            font=("Arial", 9, "italic")
        ).pack(pady=(0, 10))

        # === DECODED PASSWORD DISPLAY ===
        tk.Label(
            parent,
            text="Decoded Password (Auto-generated)",
            font=("Arial", 14, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(anchor="w", pady=(10, 4))

        self.text_preview = tk.Label(
            parent,
            text="",
            font=("Courier", 16, "bold"),
            fg=ACCENT,
            bg=SURFACE,
            width=38,
            height=1,
            relief="solid",
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.text_preview.pack(pady=(4, 14))

        # === INSTRUCTIONS PANEL ===
        self.tap_area = tk.Label(
            parent,
            text="💡 QUICK GUIDE\n\n"
                 "1. Enter Morse code above (dots and dashes)\n"
                 "2. Use SPACE to separate characters\n"
                 "3. Check decoded password below\n"
                 "4. Click 'START ENROLLMENT' when ready",
            font=("Arial", 11),
            width=38,
            height=7,
            fg=TEXT,
            bg=SURFACE,
            relief="solid",
            highlightbackground=BORDER,
            highlightthickness=2,
            justify="left",
            anchor="n",
            padx=15,
            pady=15
        )
        self.tap_area.pack(pady=10)

        # === STATUS MESSAGES ===
        self.status_label = tk.Label(
            parent,
            text="Status: Enter username and Morse pattern",
            fg=TEXT,
            bg=BG,
            font=("Arial", 10)
        )
        self.status_label.pack(pady=8)

        self.progress_label = tk.Label(
            parent,
            text="",
            fg=ACCENT,
            bg=BG,
            font=("Arial", 10, "bold")
        )
        self.progress_label.pack(pady=4)

        # === ENROLL BUTTON ===
        tk.Button(
            parent,
            text="START ENROLLMENT",
            width=22,
            height=2,
            bg=ACCENT,
            fg="#111827",
            relief="flat",
            activebackground=ACCENT,
            activeforeground="#111827",
            font=("Arial", 12, "bold"),
            command=self.start_enrollment,
            cursor="hand2"
        ).pack(pady=12)

    def setup_morse_reference(self, parent):
        """Setup the Morse code reference table (right side)"""
        tk.Label(
            parent,
            text="Morse Code Reference",
            font=("Arial", 16, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(pady=6)

        table_frame = tk.Frame(parent, bg=BG)
        table_frame.pack()

        def create_table(title, keys):
            """Helper function to create a reference table"""
            frame = tk.Frame(table_frame, bg=BG)

            tk.Label(
                frame,
                text=title,
                fg=TEXT,
                bg=BG,
                font=("Arial", 12, "bold")
            ).pack()

            box = tk.Text(
                frame,
                width=18,
                height=len(keys),
                font=("Courier", 11),
                bg=SURFACE,
                fg=TEXT,
                relief="solid",
                highlightbackground=BORDER,
                highlightthickness=1
            )

            for k in keys:
                box.insert("end", f"{k}  →  {MORSE_TABLE[k]}\n")

            box.config(state="disabled")  # Make read-only
            box.pack()
            frame.pack(side="left", padx=6)

        # Create three columns
        create_table("A — M", list("ABCDEFGHIJKLM"))
        create_table("N — Z", list("NOPQRSTUVWXYZ"))
        create_table("0 — 9", list("0123456789"))

    def on_morse_input_change(self, event):
        """
        Called every time user types in the Morse code textbox.
        Automatically decodes the Morse and shows the password.
        """
        morse_text = self.morse_input.get().strip()

        # If empty, clear everything
        if not morse_text:
            self.text_preview.config(text="", bg=SURFACE)
            self.morse_groups = []
            self.status_label.config(
                text="Status: Enter Morse code pattern",
                fg=TEXT
            )
            return

        # Split by spaces to get individual patterns (e.g., "... --- ..." → ["...", "---", "..."])
        patterns = morse_text.split()
        decoded = ""
        valid = True

        # Decode each pattern
        for pattern in patterns:
            # Check if pattern only contains dots and dashes
            if not all(c in '.-—' for c in pattern):
                valid = False
                break

            # Normalize (both - and — work as dash)
            normalized = pattern.replace('—', '-')

            # Look up character
            char = REVERSE_MORSE.get(normalized, '?')
            decoded += char

        # Update the decoded text display
        if valid and decoded and '?' not in decoded:
            # Valid Morse code!
            self.text_preview.config(text=decoded, bg=SURFACE)
            self.morse_groups = patterns
            self.status_label.config(
                text=f"✓ Valid Morse code • {len(patterns)} characters",
                fg=SUCCESS
            )
        elif '?' in decoded:
            # Some patterns are invalid
            self.text_preview.config(text=decoded, bg=SURFACE)
            self.morse_groups = patterns
            self.status_label.config(
                text="⚠ Some patterns are invalid (shown as ?)",
                fg=ERROR
            )
        else:
            # Invalid format
            self.text_preview.config(text="", bg=SURFACE)
            self.morse_groups = []
            self.status_label.config(
                text="⚠ Invalid Morse code format",
                fg=ERROR
            )

    def start_enrollment(self):
        """
        Called when user clicks 'START ENROLLMENT' button.
        Validates input and begins the biometric sample collection.
        """
        username = self.user_entry.get().strip()
        morse_code = self.morse_input.get().strip()

        # === VALIDATION ===
        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return

        if check_user_exists(username):
            messagebox.showerror("Error", "Username already exists!\nPlease choose a different one.")
            return

        if not morse_code:
            messagebox.showerror("Error", "Please enter a Morse code pattern")
            return

        decoded = self.text_preview.cget("text")

        if not decoded:
            messagebox.showerror("Error", "Please enter a valid Morse pattern")
            return

        if "?" in decoded:
            messagebox.showerror("Error",
                                 "Invalid Morse pattern detected (contains ?)\nCheck the reference table on the right.")
            return

        # === PREPARE PASSWORD INFO ===
        self.password_info = {
            'morse_code': morse_code,
            'decoded': decoded,
            'pattern_count': len(self.morse_groups),
            'total_elements': sum(len(g.replace('—', '-')) for g in self.morse_groups)
        }

        # === SHOW INSTRUCTIONS ===
        msg = f"Password Created: {decoded}\n\n"
        msg += f"Morse Pattern: {morse_code}\n\n"
        msg += "You will now record 3-5 biometric samples.\n\n"
        msg += "How it works:\n"
        msg += "• You'll tap this pattern using SPACEBAR\n"
        msg += "• The system captures your rhythm and timing\n"
        msg += "• This creates your unique biometric fingerprint\n\n"
        msg += "Press OK to record your first sample."

        messagebox.showinfo("Start Enrollment", msg)

        # Start recording samples
        self.record_enrollment_samples(username)

    def record_enrollment_samples(self, username):
        """
        Collect 3-5 biometric samples from the user.
        Each sample is analyzed for rhythm quality.
        """
        self.enrollment_attempt = 0
        self.accepted_scores = []
        self.enroller = Enrollment(min_samples=3, max_samples=5)

        # Start recording the first sample
        self.record_next_sample(username)

    def record_next_sample(self, username):
        """
        Record a single biometric sample using built-in tkinter events.
        This avoids the crashing issue with TapListener.
        """
        # Check if we have enough samples
        if self.enroller.is_complete():
            self.complete_enrollment(username)
            return

        self.enrollment_attempt += 1
        self.current_username = username  # Store for later use

        # Update UI
        self.status_label.config(
            text=f"Preparing sample {self.enrollment_attempt}...",
            fg=ACCENT
        )
        self.progress_label.config(
            text=f"Samples: {len(self.accepted_scores)}/3 required"
        )
        self.root.update()

        # Show instructions to user
        msg = f"Sample {self.enrollment_attempt}/{self.enroller.max_samples}\n\n"
        msg += f"Pattern to tap: {self.password_info['decoded']}\n"
        msg += f"Morse code: {self.password_info['morse_code']}\n\n"
        msg += "📋 Instructions:\n"
        msg += "1. Press OK to start recording\n"
        msg += "2. Tap your pattern using SPACEBAR\n"
        msg += "   • Short press = DOT (.)\n"
        msg += "   • Long press = DASH (-)\n"
        msg += "3. Press ENTER when finished\n\n"
        msg += "💡 Tip: Watch for the GREEN flash when you tap!"

        result = messagebox.showinfo("Record Sample", msg)

        # Initialize recording state
        self.recording_active = True
        self.press_times = []
        self.release_times = []
        self.space_is_down = False
        self.last_release_time = None

        # Update UI to show recording status
        self.status_label.config(
            text="🔴 RECORDING... Press SPACEBAR to tap! | Press ENTER when done",
            fg=ERROR
        )
        self.tap_area.config(
            text="🔴 RECORDING IN PROGRESS\n\n"
                 f"Pattern: {self.password_info['decoded']}\n"
                 f"Morse: {self.password_info['morse_code']}\n\n"
                 "👇 PRESS SPACEBAR TO TAP 👇\n"
                 "Watch for GREEN flash!\n\n"
                 "Short press = DOT • Long press = DASH\n"
                 "Press ENTER when finished\n\n"
                 "Taps recorded: 0",
            fg=TEXT,
            bg="#2d1515",
            highlightbackground=ERROR,
            highlightthickness=3
        )

        # Force focus on main window
        self.root.focus_force()
        self.root.update()

        print("Recording activated! Press SPACEBAR to start tapping...")  # Debug

    def on_record_space_press(self, event):
        """Handle spacebar press during recording"""
        if not self.recording_active:
            return "break"  # Prevent default behavior when not recording

        # Ignore auto-repeat
        if self.space_is_down:
            return "break"

        self.space_is_down = True
        now = time.time()
        self.press_times.append(now)

        # Visual feedback - GREEN flash
        self.tap_area.config(
            highlightbackground="#22c55e",
            highlightthickness=5,
            bg="#1a3a1a"
        )

        print(f"Space pressed at {now}")  # Debug
        return "break"

    def on_record_space_release(self, event):
        """Handle spacebar release during recording"""
        if not self.recording_active:
            return "break"

        if not self.space_is_down:
            return "break"

        self.space_is_down = False
        now = time.time()
        self.release_times.append(now)
        self.last_release_time = now

        # Calculate duration
        if len(self.press_times) > 0:
            duration = now - self.press_times[-1]
            tap_type = "DOT" if duration < 0.25 else "DASH"
            print(f"Space released: {duration:.3f}s ({tap_type})")  # Debug

        # Visual feedback - back to RED
        self.tap_area.config(
            highlightbackground=ERROR,
            highlightthickness=3,
            bg="#2d1515"
        )

        # Update tap count
        tap_count = len(self.press_times)
        self.status_label.config(
            text=f"🔴 RECORDING... Taps recorded: {tap_count} | Press ENTER when done",
            fg=ERROR
        )

        return "break"

    def on_enter_pressed(self, event):
        """Handle Enter key press"""
        if self.recording_active:
            self.finish_recording(self.current_username)
            return "break"
        return None

    def finish_recording(self, username):
        """Process the recorded sample"""
        if not self.recording_active:
            return

        print(f"Finishing recording. Total taps: {len(self.press_times)}")  # Debug

        self.recording_active = False

        # Reset UI
        self.tap_area.config(
            text="💡 QUICK GUIDE\n\n"
                 "1. Enter Morse code above (dots and dashes)\n"
                 "2. Use SPACE to separate characters\n"
                 "3. Check decoded password below\n"
                 "4. Click 'START ENROLLMENT' when ready",
            fg=TEXT,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=2
        )

        # Calculate presses and gaps
        presses = []
        gaps = []

        count = min(len(self.press_times), len(self.release_times))

        print(f"Press times: {len(self.press_times)}, Release times: {len(self.release_times)}")  # Debug

        if count == 0:
            messagebox.showwarning(
                "No Input",
                "No tapping detected.\n\nMake sure you:\n• Click on the main window\n• Press SPACEBAR to tap\n• Press ENTER when done\n\nTry again."
            )
            self.record_next_sample(username)
            return

        # Calculate press durations
        for i in range(count):
            duration = self.release_times[i] - self.press_times[i]
            if duration >= 0:
                presses.append(duration)
                print(f"Press {i + 1}: {duration:.3f}s")  # Debug

        # Calculate gaps between presses
        for i in range(1, count):
            gap = self.press_times[i] - self.release_times[i - 1]
            if gap >= 0:
                gaps.append(gap)

        print(f"Processed: {len(presses)} presses, {len(gaps)} gaps")  # Debug

        # Process the sample
        self.process_sample(username, presses, gaps)

    def process_sample(self, username, presses, gaps):
        """Process the recorded sample (analyze and evaluate)"""

        if not presses:
            messagebox.showwarning(
                "No Input",
                "No valid tapping detected.\n\nTry again."
            )
            self.record_next_sample(username)
            return

        # === ANALYZE RHYTHM ===
        rhythm_score = self.rhythm_analyzer.analyze_rhythm(
            presses, gaps, self.password_info
        )

        # === EXTRACT BIOMETRIC FEATURES ===
        feature_vector = self.extractor.extract(presses, gaps)

        # === ADD TO ENROLLMENT ===
        result = self.enroller.add(feature_vector, rhythm_score)

        # === SHOW RESULT ===
        if result['status'] == 'accepted':
            # Sample was good!
            self.accepted_scores.append(rhythm_score)
            messagebox.showinfo(
                "Sample Accepted ✓",
                f"Great! Sample recorded successfully.\n\n"
                f"Quality Score: {result['quality_score']:.1%}\n"
                f"Samples Collected: {result['samples_collected']}/{self.enroller.min_samples}\n\n"
                f"Metrics:\n"
                f"• Pattern Accuracy: {rhythm_score['pattern_accuracy']:.1%}\n"
                f"• Tempo Consistency: {rhythm_score['tempo_consistency']:.1%}\n"
                f"• Timing Precision: {rhythm_score['timing_precision']:.1%}"
            )
        else:
            # Sample was rejected (too inconsistent)
            messagebox.showwarning(
                "Sample Rejected ✗",
                f"This sample didn't meet quality standards.\n\n"
                f"Reason: {result['rejection_reason']}\n"
                f"Quality Score: {result['quality_score']:.1%}\n\n"
                f"Tips for better quality:\n"
                f"• Maintain consistent rhythm\n"
                f"• Clear distinction between dots and dashes\n"
                f"• Don't rush, take your time\n\n"
                f"Try again!"
            )

        # Update progress
        self.progress_label.config(
            text=f"Samples: {len(self.accepted_scores)}/3 required"
        )
        self.status_label.config(
            text=f"Sample {self.enrollment_attempt} complete",
            fg=TEXT
        )

        # Continue recording (recursive call)
        self.root.after(500, lambda: self.record_next_sample(username))

    def handle_recording_error(self, username, error):
        """Handle errors during recording"""
        messagebox.showerror(
            "Recording Error",
            f"An error occurred during recording:\n\n{error}\n\nPlease try again."
        )
        self.status_label.config(text="Error during recording", fg=ERROR)
        self.root.after(1000, lambda: self.record_next_sample(username))

    def complete_enrollment(self, username):
        """
        Called when we have enough samples.
        Calculates final metrics and saves to Firebase.
        """
        self.status_label.config(text="Processing enrollment...", fg=ACCENT)
        self.root.update()

        # === CALCULATE AVERAGE METRICS ===
        final_evals = {
            "overall_score": 0.0,
            "tempo_consistency": 0.0,
            "pattern_accuracy": 0.0,
            "timing_precision": 0.0
        }

        if self.accepted_scores:
            count = len(self.accepted_scores)
            for key in final_evals:
                total = sum(s.get(key, 0) for s in self.accepted_scores)
                final_evals[key] = round(total / count, 4)

        # === BUILD BIOMETRIC PROFILE ===
        profile = self.enroller.build_profile()
        user_id = str(uuid.uuid4())  # Generate unique ID

        # === SAVE TO FIREBASE ===
        success = save_user_to_firebase(
            user_id, username, self.password_info, profile, final_evals
        )

        if success:
            # Success!
            messagebox.showinfo(
                "Enrollment Complete ✓",
                f"User '{username}' enrolled successfully!\n\n"
                f"Password: {self.password_info['decoded']}\n"
                f"Pattern Accuracy: {final_evals['pattern_accuracy']:.1%}\n"
                f"Consistency Score: {profile['consistency_score']:.1%}\n"
                f"Samples Used: {profile['sample_count']}\n\n"
                f"Your biometric profile has been saved.\n"
                f"You can now sign in with this account!"
            )
            self.status_label.config(text="✓ Enrollment complete", fg=SUCCESS)

            # Reset form for next user
            self.root.after(2000, self.reset_form)
        else:
            # Failed to save
            messagebox.showerror(
                "Error",
                "Failed to save user profile to Firebase.\n\nCheck your internet connection and try again."
            )
            self.status_label.config(text="✗ Enrollment failed", fg=ERROR)

    def reset_form(self):
        """Clear the form for a new enrollment"""
        self.user_entry.delete(0, tk.END)
        self.morse_input.delete(0, tk.END)
        self.morse_groups = []
        self.text_preview.config(text="")
        self.status_label.config(
            text="Status: Ready for new enrollment",
            fg=TEXT
        )
        self.progress_label.config(text="")


# ==========================================
# RUN THE APPLICATION
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = EnrollmentApp(root)
    root.mainloop()