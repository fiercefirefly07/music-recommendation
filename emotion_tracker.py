"""Per-browser-session webcam tracking. No Streamlit calls run in media threads."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


EMOTIONS = ("angry", "disgust", "fear", "happy", "sad", "surprise", "neutral")


@dataclass(frozen=True)
class TrackingState:
    emotion: str | None
    confidence: float
    face_visible: bool
    face_recent: bool
    box: tuple[int, int, int, int] | None
    error: str | None


class EmotionTracker:
    """Analyze only the newest frame and hold state through short detection gaps."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._frame: np.ndarray | None = None
        self._box: tuple[int, int, int, int] | None = None
        self._seen_at = 0.0
        self._emotion: str | None = None
        self._confidence = 0.0
        self._scores: dict[str, float] = {}
        self._candidate: str | None = None
        self._candidate_count = 0
        self._error: str | None = None
        self._thread: threading.Thread | None = None

    @property
    def closed(self) -> bool:
        return self._stop.is_set()

    def submit(self, frame: np.ndarray) -> None:
        if self.closed:
            return
        # The WebRTC callback stays quick even if DeepFace takes seconds.
        with self._lock:
            self._frame = frame.copy()
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, daemon=True)
                self._thread.start()
        self._wake.set()

    def snapshot(self) -> TrackingState:
        now = time.monotonic()
        with self._lock:
            age = now - self._seen_at
            recent = self._seen_at > 0 and age < 4.0
            visible = self._seen_at > 0 and age < 1.8
            return TrackingState(
                emotion=self._emotion if recent else None,
                confidence=self._confidence if recent else 0.0,
                face_visible=visible,
                face_recent=recent,
                box=self._box if recent else None,
                error=self._error,
            )

    def close(self) -> None:
        self._stop.set()
        self._wake.set()

    def _run(self) -> None:
        bundled = Path(__file__).resolve().parent / "assets" / "haarcascade_frontalface_default.xml"
        packaged = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        cascade_path = next((path for path in (bundled, packaged) if path.is_file()), None)
        cascade = cv2.CascadeClassifier(str(cascade_path)) if cascade_path else None
        if cascade is None or cascade.empty():
            with self._lock:
                self._error = "Face detector data could not load. Reinstall the bundled assets/haarcascade_frontalface_default.xml file."
            return
        last_analysis = 0.0
        while not self._stop.is_set():
            self._wake.wait(timeout=0.5)
            self._wake.clear()
            if self._stop.is_set():
                return
            with self._lock:
                frame = self._frame
                self._frame = None
            if frame is None:
                continue
            try:
                box = self._detect(cascade, frame)
                if box is None:
                    # snapshot() provides a short grace period.
                    continue
                now = time.monotonic()
                with self._lock:
                    if self._seen_at and now - self._seen_at >= 4.0:
                        self._emotion = None
                        self._confidence = 0.0
                        self._scores.clear()
                        self._candidate = None
                        self._candidate_count = 0
                    self._box = box
                    self._seen_at = now
                    self._error = None
                if now - last_analysis < 0.9:
                    continue
                x, y, w, h = box
                pad = int(min(w, h) * 0.12)
                crop = frame[max(0, y-pad):min(frame.shape[0], y+h+pad),
                             max(0, x-pad):min(frame.shape[1], x+w+pad)]
                if crop.size == 0:
                    continue
                from deepface import DeepFace

                result = DeepFace.analyze(
                    img_path=crop,
                    actions=["emotion"],
                    detector_backend="skip",
                    enforce_detection=False,
                    silent=True,
                )
                if isinstance(result, list):
                    result = result[0] if result else {}
                scores = result.get("emotion", {})
                self._update_emotion(scores)
                last_analysis = time.monotonic()
            except Exception as exc:
                with self._lock:
                    self._error = f"Analysis paused: {type(exc).__name__}: {exc}"
                time.sleep(1)

    def _detect(self, cascade: cv2.CascadeClassifier, frame: np.ndarray):
        height, width = frame.shape[:2]
        scale = min(1.0, 640 / width)
        small = cv2.resize(frame, None, fx=scale, fy=scale) if scale < 1 else frame
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.08, minNeighbors=4, minSize=(55, 55)
        )
        if len(faces) == 0:
            return None
        boxes = [tuple(int(round(v / scale)) for v in face) for face in faces]
        with self._lock:
            previous = self._box if time.monotonic() - self._seen_at < 2.5 else None
        def rank(box):
            x, y, w, h = box
            area = w * h
            if previous is None:
                return area
            px, py, pw, ph = previous
            ix = max(0, min(x+w, px+pw) - max(x, px))
            iy = max(0, min(y+h, py+ph) - max(y, py))
            overlap = ix * iy / max(1, area + pw*ph - ix*iy)
            return area * (1 + 3 * overlap)
        selected = max(boxes, key=rank)
        if previous is None:
            return selected
        return tuple(int(round(0.65 * old + 0.35 * new))
                     for old, new in zip(previous, selected))

    def _update_emotion(self, raw_scores: dict) -> None:
        values = {name: max(0.0, float(raw_scores.get(name, 0))) for name in EMOTIONS}
        if not any(values.values()):
            return
        ranked = sorted(values.values(), reverse=True)
        if ranked[0] < 28 or ranked[0] - ranked[1] < 4:
            return
        with self._lock:
            self._scores = {
                name: 0.58 * self._scores.get(name, values[name]) + 0.42 * values[name]
                for name in EMOTIONS
            }
            winner = max(self._scores, key=self._scores.get)
            if self._emotion is None:
                if winner == self._candidate:
                    self._candidate_count += 1
                else:
                    self._candidate, self._candidate_count = winner, 1
                if self._candidate_count >= 2:
                    self._emotion = winner
                    self._candidate = None
                    self._candidate_count = 0
            elif winner != self._emotion:
                if winner == self._candidate:
                    self._candidate_count += 1
                else:
                    self._candidate, self._candidate_count = winner, 1
                if self._candidate_count >= 2 and (
                    self._scores[winner] - self._scores[self._emotion] >= 5
                ):
                    self._emotion = winner
                    self._candidate = None
                    self._candidate_count = 0
            else:
                self._candidate = None
                self._candidate_count = 0
            if self._emotion is not None:
                self._confidence = self._scores[self._emotion]
