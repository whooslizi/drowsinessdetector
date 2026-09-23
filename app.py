from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from typing import Optional

import cv2
import webview

from detector import DrowsinessDetector, TelemetryData

ALERT_SOUND_PATH: str = "/System/Library/Sounds/Sosumi.aiff"
ALERT_COOLDOWN: float = 1.0


class DesktopAppAPI:
    def __init__(self, detector: DrowsinessDetector) -> None:
        self.detector = detector
        self.is_tracking: bool = True
        self.window: Optional[webview.Window] = None

    def toggle_tracking(self, state: bool) -> bool:
        self.is_tracking = state
        return self.is_tracking

    def update_settings(self, ear_threshold: float, drowsy_time: float) -> None:
        self.detector.ear_threshold = float(ear_threshold)
        self.detector.drowsy_time_threshold = float(drowsy_time)

    def close_app(self) -> None:
        if self.window:
            self.window.destroy()


def run_vision_loop(app_api: DesktopAppAPI, detector: DrowsinessDetector) -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return

    last_alert_time = 0.0

    try:
        while True:
            if not app_api.is_tracking:
                time.sleep(0.2)
                continue

            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            telemetry: TelemetryData = detector.process_frame(frame)

            now = time.monotonic()
            if telemetry.is_drowsy and (now - last_alert_time >= ALERT_COOLDOWN):
                last_alert_time = now
                try:
                    subprocess.Popen(
                        ["afplay", ALERT_SOUND_PATH],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except FileNotFoundError:
                    pass

            if app_api.window is not None:
                telemetry_json = json.dumps(telemetry.to_dict())
                js_code = f"if (window.updateTelemetry) {{ window.updateTelemetry({telemetry_json}); }}"
                try:
                    app_api.window.evaluate_js(js_code)
                except Exception:
                    pass

            time.sleep(0.033)
    finally:
        cap.release()
        detector.release()


def main() -> None:
    dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dist", "index.html"))

    if os.path.exists(dist_path):
        target_url = f"file://{dist_path}"
    else:
        target_url = "http://localhost:5173"

    detector = DrowsinessDetector(ear_threshold=0.18, drowsy_time_threshold=2.0)
    app_api = DesktopAppAPI(detector)

    window = webview.create_window(
        title="DrowsinessDetector.exe",
        url=target_url,
        width=1024,
        height=768,
        resizable=True,
        js_api=app_api,
    )
    app_api.window = window

    vision_thread = threading.Thread(
        target=run_vision_loop, args=(app_api, detector), daemon=True
    )
    vision_thread.start()

    webview.start(debug=False)


if __name__ == "__main__":
    main()
