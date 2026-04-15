import cv2
import mediapipe as mp
import time
import numpy as np
import random
import tkinter as tk
import json
import os

THRESHOLD_FACTOR = 1  
RESET_TIME = 3        
JSON_FILE = "words.json"
MIN_PIXEL_TOLERANCE = 45

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, 
                       min_detection_confidence=0.8, min_tracking_confidence=0.8)

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
            self.lock_window.config(bg="#2c0000") # Koyu bordo (Gözü yormaz ama uyarıcı)
            
            tk.Label(self.lock_window, text="ENGINE FAULT DETECTION\n\nPlease release your fingers.", 
                     fg="white", bg="#2c0000", font=("Arial", 38, "bold")).pack(expand=True)
            self.lock_window.update()

    def unlock(self):
        if self.lock_window:
            self.lock_window.destroy()
            self.lock_window = None

class ProjeDisgrafiV4:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.locker = GlobalLocker()
        self.baseline_y = {}
        self.locked_until = 0
        self.is_calibrated = False
        self.current_text = ""
        self.finger_tips = [8, 12, 16, 20]
        self.words = self._load_words()
        self.target_word = random.choice(self.words)

    def _load_words(self):
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("rehab_words", ["odaklan"])
        return ["systen", "join"]

    def check_error(self, results):
        if not self.is_calibrated or not results.multi_hand_landmarks:
            return False
            
        for hl, info in zip(results.multi_hand_landmarks, results.multi_handedness):
            lbl = info.classification[0].label
            if lbl not in self.baseline_y: continue
            
            # Elin boyutuna göre dinamik bir koridor oluştur
            palm_size = abs(hl.landmark[0].y - hl.landmark[5].y) * 480
            # Toleransı belirle (Annen için 0.8 veya 1.0 bile yapılabilir)
            dynamic_threshold = max(palm_size * THRESHOLD_FACTOR, MIN_PIXEL_TOLERANCE)
            
            for i, tip_idx in enumerate(self.finger_tips):
                curr_y = hl.landmark[tip_idx].y * 480
                diff = self.baseline_y[lbl][i] - curr_y
                
                # Eğer parmak gerçekten 'fırlama' yapmıyorsa (eşikten küçükse) hata sayma
                if diff > dynamic_threshold:
                    # Küçük bir ek güvenlik: Hata vermeden önce parmağın 
                    # gerçekten yukarıda sabit kalıp kalmadığına bakılabilir 
                    # ama şimdilik eşiği yükseltmek en iyi çözüm.
                    return True
        return False
    def run(self):
        cv2.namedWindow("REHAB", cv2.WINDOW_NORMAL)
        
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            curr_time = time.time()
            locked = curr_time < self.locked_until

            if locked:
                self.locker.lock()
            else:
                self.locker.unlock()

            if not locked and self.is_calibrated:
                if self.check_error(results):
                    self.locked_until = curr_time + RESET_TIME
                    self.current_text = ""

            # UI Çizimi
            if not locked:
                if results.multi_hand_landmarks:
                    for hl in results.multi_hand_landmarks:
                        mp.solutions.drawing_utils.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)

                cv2.rectangle(frame, (0, h-90), (w, h), (20, 20, 20), -1)
                cv2.putText(frame, f"TARGET: {self.target_word}", (30, h-55), 1, 1.3, (0, 255, 255), 2)
                cv2.putText(frame, f"> {self.current_text}", (30, h-20), 1, 1.8, (0, 255, 0), 2)
            
            cv2.imshow("REHAB", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            elif key == ord('c') and not locked:
                if results.multi_hand_landmarks:
                    for hl, info in zip(results.multi_hand_landmarks, results.multi_handedness):
                        lbl = info.classification[0].label
                        self.baseline_y[lbl] = [hl.landmark[idx].y * 480 for idx in self.finger_tips]
                    self.is_calibrated = True
            elif self.is_calibrated and not locked:
                if 97 <= key <= 122:
                    self.current_text += chr(key)
                    if self.current_text == self.target_word:
                        self.target_word = random.choice(self.words)
                        self.current_text = ""
                elif key == 8: self.current_text = self.current_text[:-1]

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    ProjeDisgrafiV4().run()