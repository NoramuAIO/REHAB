REHAB: Neuro-Rehabilitation & Motor Control Software

REHAB is an AI-powered physical rehabilitation tool designed to improve finger isolation and fine motor control. Using real-time computer vision, the software monitors hand posture and provides immediate feedback to retrain neural pathways for precise movement.
🚀 Core Features

    Dual-Hand Tracking: Real-time landmark detection for both left and right hands using OpenCV and MediaPipe.
    Dynamic Finger Isolation Algorithm: Detects involuntary finger movements by measuring vertical deviation from a baseline position.
    Global System Lock (Multi-Monitor): When a motor error is detected, REHAB deploys a "hard lock" across all connected monitors to enforce physical relaxation.
    Dynamic Thresholding: Automatically adjusts sensitivity based on the hand's distance from the camera to ensure fair and accurate monitoring.
    Gamified Typing Tasks: Interactive typing exercises loaded from external JSON data to practice motor control during functional tasks.

🛠 Tech Stack

    Python 3.11+
    OpenCV: Image processing and UI rendering.
    MediaPipe: High-fidelity hand landmark detection.
    Tkinter: Global multi-monitor management and lock-screen deployment.
    JSON: External configuration for training vocabulary.

📦 Installation

    Clone the repository:
    git clone https://github.com/NoramuAIO/REHAB.git
    cd REHAB
    Set up a virtual environment:
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    Install dependencies:
    pip install opencv-python mediapipe numpy

🎮 How to Use

    Prepare Vocabulary: Edit the words.json file to include the terms you wish to practice.
    Launch: Run python main.py. The application will launch in full-screen mode.
    Calibrate: Place your hands flat on your desk or a cushion (the "zero point"). Press 'C' to calibrate.
    Exercise: Type the target words displayed on the screen.
    Motor Error: If an inactive finger lifts beyond the threshold, REHAB will lock the system for a set duration (3-5 seconds). You must relax your hands to wait out the reset.
    Exit: Press 'Q' to safely close the application.

⚙️ Configuration

You can fine-tune the sensitivity in the main.py file:

    THRESHOLD_FACTOR: Adjusts how much a finger can lift before triggering an error (1.0 = length of the palm).
    RESET_TIME: Sets the duration of the global system lock.
