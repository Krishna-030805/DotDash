import time
from pynput import keyboard

class TapListener:
    def __init__(self):
        self.press_times = []
        self.release_times = []
        self.gaps = []
        self.space_is_down = False
        self.last_release_time = None

    def start(self):
        print("Tap using SPACE.")
        print("Press ESC to finish.\n")

        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            listener.join()

    def on_press(self, key):
        now = time.time()

        if key == keyboard.Key.space:
            # ❌ Ignore auto-repeat presses
            if self.space_is_down:
                return

            self.space_is_down = True

            # Calculate gap
            if self.last_release_time is not None:
                gap = now - self.last_release_time
                if gap >= 0:
                    self.gaps.append(gap)

            self.press_times.append(now)

        elif key == keyboard.Key.esc:
            return False

    def on_release(self, key):
        if key == keyboard.Key.space:
            now = time.time()
            self.space_is_down = False
            self.release_times.append(now)
            self.last_release_time = now

    def get_sequences(self):
        presses = []

        count = min(len(self.press_times), len(self.release_times))

        for i in range(count):
            duration = self.release_times[i] - self.press_times[i]
            if duration >= 0:
                presses.append(duration)

        return presses, self.gaps


# ---------- MAIN ----------
if __name__ == "__main__":
    listener = TapListener()
    listener.start()

    presses, gaps = listener.get_sequences()

    print("\nResults:")
    print("Press durations (seconds):", presses)
    print("Gap durations (seconds):", gaps)