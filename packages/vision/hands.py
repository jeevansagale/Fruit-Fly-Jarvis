"""Hand tracking + gesture classification (MediaPipe Hands backend).

Architecture: MediaPipe's ML models (palm detector + 21-landmark regressor)
do detection; this module contributes the rule-based classifier on top
(static poses + dynamic swipes with cooldowns) and emits contract-shaped
system events. The classifier takes plain landmark lists, so it is fully
testable without a camera or MediaPipe installed.
"""
from __future__ import annotations

import time
import urllib.request
from pathlib import Path

# MediaPipe HandLandmarker indices.
WRIST = 0
THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP = 4, 8, 12, 16, 20
THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP = 3, 6, 10, 14, 18

FINGER_TIPS = (INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)
FINGER_PIPS = (INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP)

SWIPE_MIN_DX = 0.12      # normalized-x travel to count as a swipe
SWIPE_MAX_DY = 0.10      # vertical drift allowed during horizontal swipe
SWIPE_MAX_DT = 1.5       # seconds to complete the travel (low-fps cameras)
SWIPE_COOLDOWN = 1.2     # seconds before the same hand swipes again
PINCH_MAX_DIST = 0.05    # thumb-index tip distance for pinch
SMOOTH_ALPHA = 0.5       # landmark exponential smoothing factor
ROI_MARGIN = 0.35        # bbox expansion around last known hand
ROI_MAX_MISS = 3         # full-frame re-detects after this many misses

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/1/hand_landmarker.task")
MODEL_PATH = Path.home() / ".cache" / "fruit-fly" / "hand_landmarker.task"
ONNX_URL = ("https://github.com/PINTO0309/hand_landmark/releases/download/"
            "1.0.0/hand_landmark_sparse_Nx3x224x224.onnx")
ONNX_PATH = Path.home() / ".cache" / "fruit-fly" / "hand_landmark_sparse.onnx"
ONNX_SIZE = 224
ONNX_MIN_SCORE = 0.5


def _dist(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _finger_extended(lm, tip: int, pip: int) -> bool:
    # Finger is extended when tip is farther from wrist than its PIP joint.
    return _dist(lm[tip], lm[WRIST]) > _dist(lm[pip], lm[WRIST])


def classify_static(lm: list) -> str:
    """One of: open_palm, fist, pinch, point, unknown. Needs 21 (x, y) points."""
    if len(lm) < 21:
        return "unknown"
    extended = [_finger_extended(lm, t, p) for t, p in zip(FINGER_TIPS, FINGER_PIPS)]
    pinch = _dist(lm[THUMB_TIP], lm[INDEX_TIP]) < PINCH_MAX_DIST
    if all(extended) and not pinch:
        return "open_palm"
    if not any(extended):
        return "fist"
    if pinch and extended[0] and not any(extended[1:]):
        return "pinch"
    if extended[0] and not any(extended[1:]) and not pinch:
        return "point"
    return "unknown"


class SwipeTracker:
    """Tracks one hand's palm centroid; emits swipe_left/right/up/down."""

    def __init__(self, clock=time.monotonic, dx_min: float = SWIPE_MIN_DX,
                 cooldown: float = SWIPE_COOLDOWN):
        self.clock = clock
        self.dx_min = dx_min
        self.cooldown = cooldown
        self.start: tuple[float, float] | None = None
        self.start_t = 0.0
        self.last_fire = 0.0

    def update(self, centroid: tuple[float, float]) -> str | None:
        now = self.clock()
        if self.start is None:
            self.start, self.start_t = centroid, now
            return None
        dx = centroid[0] - self.start[0]
        dy = centroid[1] - self.start[1]
        dt = now - self.start_t
        if dt > SWIPE_MAX_DT:
            self.start, self.start_t = centroid, now
            return None
        if now - self.last_fire < self.cooldown:
            return None
        gesture = None
        if abs(dx) > self.dx_min and abs(dy) < SWIPE_MAX_DY:
            gesture = "swipe_right" if dx > 0 else "swipe_left"
        elif abs(dy) > self.dx_min and abs(dx) < SWIPE_MAX_DY:
            gesture = "swipe_down" if dy > 0 else "swipe_up"
        if gesture:
            self.last_fire = now
            self.start = None
        return gesture

    def reset(self) -> None:
        self.start = None


def smooth_points(prev: list | None, new: list, alpha: float = SMOOTH_ALPHA) -> list:
    """Exponential moving average over landmarks; kills single-frame jitter."""
    if prev is None or len(prev) != len(new):
        return [tuple(p) for p in new]
    return [((1 - alpha) * a[0] + alpha * b[0],
             (1 - alpha) * a[1] + alpha * b[1]) for a, b in zip(prev, new)]


def bbox_of(lm: list, margin: float = ROI_MARGIN) -> tuple[float, float, float, float]:
    xs = [p[0] for p in lm]
    ys = [p[1] for p in lm]
    w = max(max(xs) - min(xs), 0.05)
    h = max(max(ys) - min(ys), 0.05)
    x0 = max(0.0, min(xs) - w * margin)
    y0 = max(0.0, min(ys) - h * margin)
    x1 = min(1.0, max(xs) + w * margin)
    y1 = min(1.0, max(ys) + h * margin)
    return (x0, y0, x1, y1)


def map_crop_to_frame(pts: list, box: tuple[float, float, float, float]) -> list:
    x0, y0, x1, y1 = box
    return [(x0 + x * (x1 - x0), y0 + y * (y1 - y0)) for x, y in pts]


def gesture_event(gesture: str, confidence: float = 0.9) -> dict:
    return {"type": "system.event", "event": "gesture",
            "data": {"gesture": gesture,
                     "confidence": max(0.0, min(1.0, confidence))}}


# Static/dynamic gestures with a wired capability. Everything else observes.
GESTURE_INTENTS = {
    "swipe_left": ("workspace.previous", {}),
    "swipe_right": ("workspace.next", {}),
    "swipe_up": ("scroll.page", {"direction": "up"}),
    "swipe_down": ("scroll.page", {"direction": "down"}),
    "pinch": ("media.play_pause", {}),
}


def gesture_intent(gesture: str) -> tuple[str, dict] | None:
    mapped = GESTURE_INTENTS.get(gesture)
    return (mapped[0], dict(mapped[1])) if mapped else None


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
    except OSError as exc:
        raise RuntimeError(f"cannot download hand model: {exc}") from exc
    return dest


def _ensure_model() -> Path:
    """Fetch the HandLandmarker model into ~/.cache on first use."""
    if MODEL_PATH.exists():
        return MODEL_PATH
    return _download(MODEL_URL, MODEL_PATH)


def _ensure_onnx_model() -> Path:
    if ONNX_PATH.exists():
        return ONNX_PATH
    return _download(ONNX_URL, ONNX_PATH)


class OnnxBackend:
    """Single-shot 21-landmark regression via ONNX Runtime (no MediaPipe,
    no palm pre-stage). Raises RuntimeError when onnxruntime is missing."""

    def __init__(self):
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError(
                "hand tracking needs: pip install onnxruntime opencv-python") from exc
        model = _ensure_onnx_model()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        self.session = ort.InferenceSession(
            str(model), sess_options=options,
            providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def detect(self, frame_bgr, box: tuple | None = None) -> tuple[list | None, float]:
        """Run on full frame (box=None) or a normalized crop box. Returns
        (landmarks in frame coords | None, score)."""
        import cv2
        import numpy as np
        h, w = frame_bgr.shape[:2]
        if box is None:
            crop, origin, size = frame_bgr, (0.0, 0.0), (float(w), float(h))
        else:
            x0 = max(0, int(box[0] * w))
            y0 = max(0, int(box[1] * h))
            x1 = min(w, int(box[2] * w))
            y1 = min(h, int(box[3] * h))
            if x1 - x0 < 32 or y1 - y0 < 32:
                return None, 0.0
            crop = frame_bgr[y0:y1, x0:x1]
            origin, size = (float(x0) / w, float(y0) / h), (float(x1 - x0) / w, float(y1 - y0) / h)
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        small = cv2.resize(rgb, (ONNX_SIZE, ONNX_SIZE))
        tensor = (small.astype("float32") / 255.0).transpose(2, 0, 1)[None]
        xyz, score, _handed = self.session.run(None, {self.input_name: tensor})
        self.last_score = float(score[0][0])
        if self.last_score < ONNX_MIN_SCORE:
            return None, self.last_score
        pts = xyz[0].reshape(21, 3)
        crop_pts = [(float(x), float(y)) for x, y, _z in pts]
        if box is None:
            return crop_pts, self.last_score
        return map_crop_to_frame(crop_pts, (origin[0], origin[1],
                                            origin[0] + size[0], origin[1] + size[1])), self.last_score

    last_score: float = 0.0


class HandTracker:
    """Live camera tracker. Raises RuntimeError with install instructions
    when mediapipe/opencv are missing instead of failing at import."""

    def __init__(self, camera: int = 0, max_hands: int = 1, backend: str = "auto",
                 swipe_dx: float = SWIPE_MIN_DX, swipe_cooldown: float = SWIPE_COOLDOWN):
        """backend: onnx (default), mediapipe, or auto (onnx, then mediapipe)."""
        try:
            import cv2  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "hand tracking needs: pip install onnxruntime opencv-python") from exc
        self.camera = camera
        self.backend_name = backend
        self.onnx = None
        self.landmarker = None
        if backend in ("auto", "onnx"):
            try:
                self.onnx = OnnxBackend()
                self.backend_name = "onnx"
            except RuntimeError:
                if backend == "onnx":
                    raise
        if self.onnx is None:
            try:
                from mediapipe.tasks import python as mp_python
                from mediapipe.tasks.python import vision
            except ImportError as exc:
                raise RuntimeError(
                    "hand tracking needs: pip install mediapipe opencv-python") from exc
            model = _ensure_model()
            options = vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(model)),
                num_hands=max_hands, min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.5, min_tracking_confidence=0.5)
            self.landmarker = vision.HandLandmarker.create_from_options(options)
            self.backend_name = "mediapipe"
        self.last_brightness = 0.0
        self.last_small = None
        self.roi: tuple | None = None
        self.roi_misses = 0
        self.prev_lm: list | None = None
        self.swipes = [SwipeTracker(clock=time.monotonic, dx_min=swipe_dx,
                                    cooldown=swipe_cooldown) for _ in range(max_hands)]

    def _detect_onnx(self, frame) -> list[list[tuple[float, float]]]:
        lm, _score = self.onnx.detect(frame, self.roi)
        if lm is None and self.roi is not None:
            lm, _score = self.onnx.detect(frame, None)  # lost track: full frame
        if lm is None:
            self.roi_misses += 1
            if self.roi_misses >= ROI_MAX_MISS:
                self.roi, self.prev_lm = None, None
                self.roi_misses = 0
            return []
        self.roi, self.roi_misses = bbox_of(lm), 0
        lm = smooth_points(self.prev_lm, lm)
        self.prev_lm = lm
        return [lm]

    def _detect_mediapipe(self, frame) -> list[list[tuple[float, float]]]:
        import cv2
        import mediapipe as mp
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.landmarker.detect(image)
        return [[(p.x, p.y) for p in hand] for hand in (result.hand_landmarks or [])]

    def read(self) -> list[dict]:
        """Capture one frame; return [{landmarks, static, swipe}] per hand."""
        import cv2
        cap = cv2.VideoCapture(self.camera)
        if not cap.isOpened():
            raise RuntimeError(f"cannot open camera {self.camera}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        try:
            ok, frame = cap.read()
            if not ok or frame is None:
                return []
            self.last_brightness = float(frame.mean())
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.last_small = cv2.resize(gray, (160, 120))
            if self.onnx is not None:
                hands = self._detect_onnx(frame)
            else:
                hands = self._detect_mediapipe(frame)
            out = []
            for i, lm in enumerate(hands):
                cx = sum(p[0] for p in lm) / len(lm)
                cy = sum(p[1] for p in lm) / len(lm)
                out.append({
                    "landmarks": lm,
                    "static": classify_static(lm),
                    "swipe": self.swipes[i].update((cx, cy)) if i < len(self.swipes) else None,
                })
            if not out:
                for tracker in self.swipes:
                    tracker.reset()
                self.roi, self.prev_lm, self.roi_misses = None, None, 0
            return out
        finally:
            cap.release()
