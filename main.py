import cv2
import mediapipe as mp
import time
import numpy as np
import random
import tkinter as tk
import json
import os
from pynput import keyboard
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
THRESHOLD_FACTOR = 1.0  
RESET_TIME = 3          
JSON_FILE = "words.json"
MIN_PIXEL_TOLERANCE = 45

# MediaPipe optimization: model_complexity=0 (faster)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, 
    max_num_hands=2, 
    model_complexity=0, # 0 = Fastest, 1 = Balanced
    min_detection_confidence=0.6, # Slightly lower for speed
    min_tracking_confidence=0.6
)

class GlobalLocker:
    def __init__(self):
        self.lock_window = None

    def lock(self):
        if self.lock_window is None:
            self.lock_window = tk.Tk()
            sw = self.lock_window.winfo_vrootwidth()
            sh = self.lock_window.winfo_vrootheight()
            sx = self.lock_window.winfo_vrootx()
            sy = self.lock_window.winfo_vrooty()
            self.lock_window.geometry(f"{sw}x{sh}+{sx}+{sy}")
            self.lock_window.attributes("-topmost", True)
            self.lock_window.overrideredirect(True)
            self.lock_window.config(bg="#2c0000")
            tk.Label(self.lock_window, text="MOTOR ERROR DETECTED\n\nPlease relax your fingers.", 
                     fg="white", bg="#2c0000", font=("Arial", 38, "bold")).pack(expand=True)
            self.lock_window.update()

    def unlock(self):
        if self.lock_window:
            self.lock_window.destroy()
            self.lock_window = None

class RehabApp:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        # Performance: Lower internal resolution for faster processing
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.locker = GlobalLocker()
        self.baseline_y = {}
        self.locked_until = 0
        self.is_calibrated = False
        self.current_text = ""
        self.finger_tips = [8, 12, 16, 20]
        self.words = self._load_words()
        self.target_word = random.choice(self.words)
        self.running = True
        self.should_calibrate = False
        self.c_is_held = False 

        try:
            self.font = ImageFont.truetype("arial.ttf", 28)
        except:
            self.font = ImageFont.load_default()

        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def _load_words(self):
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("rehab_words", ["focus"])
            except:
                return ["error"]
        return ["ready", "system"]

    def put_text_ui(self, img, text, position, color=(255, 255, 255)):
        img_pil = Image.fromarray(img) # Already RGB from loop
        draw = ImageDraw.Draw(img_pil)
        draw.text(position, text, font=self.font, fill=color)
        return np.array(img_pil)

    def on_press(self, key):
        if time.time() < self.locked_until: return
        try:
            if hasattr(key, 'char') and key.char is not None:
                k = key.char
                if k.lower() == 'c' and not self.is_calibrated:
                    if not self.c_is_held:
                        self.should_calibrate = True
                        self.c_is_held = True
                elif k.lower() == 'q':
                    self.running = False
                else:
                    self.current_text += k
            elif key == keyboard.Key.space:
                self.current_text += " "
            elif key == keyboard.Key.backspace:
                self.current_text = self.current_text[:-1]

            if self.current_text == self.target_word:
                self.target_word = random.choice(self.words)
                self.current_text = ""
        except: pass

    def on_release(self, key):
        try:
            if hasattr(key, 'char') and key.char.lower() == 'c':
                self.c_is_held = False
        except: pass

    def check_error(self, results):
        if not self.is_calibrated or not results.multi_hand_landmarks:
            return False
        for hl, info in zip(results.multi_hand_landmarks, results.multi_handedness):
            lbl = info.classification[0].label
            if lbl not in self.baseline_y: continue
            
            # Use height from frame directly (480)
            palm_size = abs(hl.landmark[0].y - hl.landmark[5].y) * 480
            dynamic_threshold = max(palm_size * THRESHOLD_FACTOR, MIN_PIXEL_TOLERANCE)
            
            for i, tip_idx in enumerate(self.finger_tips):
                curr_y = hl.landmark[tip_idx].y * 480
                if (self.baseline_y[lbl][i] - curr_y) > dynamic_threshold:
                    return True
        return False

    def run(self):
        cv2.namedWindow("REHAB", cv2.WINDOW_NORMAL)

        while self.cap.isOpened() and self.running:
            ret, frame = self.cap.read()
            if not ret: break
            
            frame = cv2.flip(frame, 1)
            # Conversion for MediaPipe and PIL
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            
            curr_time = time.time()
            locked = curr_time < self.locked_until

            if locked:
                self.locker.lock()
            else:
                self.locker.unlock()

            if self.should_calibrate and not locked:
                if results.multi_hand_landmarks:
                    for hl, info in zip(results.multi_hand_landmarks, results.multi_handedness):
                        lbl = info.classification[0].label
                        self.baseline_y[lbl] = [hl.landmark[idx].y * 480 for idx in self.finger_tips]
                    self.is_calibrated = True
                self.should_calibrate = False 

            if not locked and self.is_calibrated:
                if self.check_error(results):
                    self.locked_until = curr_time + RESET_TIME
                    self.current_text = ""

            # UI Section
            if not locked:
                if results.multi_hand_landmarks:
                    for hl in results.multi_hand_landmarks:
                        mp.solutions.drawing_utils.draw_landmarks(rgb_frame, hl, mp_hands.HAND_CONNECTIONS)
                
                # Draw overlay and text on RGB frame
                h, w, _ = rgb_frame.shape
                # Simple rectangle using numpy slicing for speed
                rgb_frame[h-100:h, 0:w] = [20, 20, 20]
                
                rgb_frame = self.put_text_ui(rgb_frame, f"TARGET: {self.target_word}", (30, h-85), (0, 255, 255))
                rgb_frame = self.put_text_ui(rgb_frame, f"> {self.current_text}", (30, h-45), (0, 255, 0))
                
                if not self.is_calibrated:
                    rgb_frame = self.put_text_ui(rgb_frame, "PRESS 'C' TO START REHAB", (w//5, h//2), (255, 165, 0))
            
            # Back to BGR for display
            cv2.imshow("REHAB", cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        self.cap.release()
        cv2.destroyAllWindows()
        self.listener.stop()

if __name__ == "__main__":
    RehabApp().run()
