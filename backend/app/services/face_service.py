import cv2
import numpy as np
from insightface.app import FaceAnalysis

_face_app: FaceAnalysis | None = None

# Calibrated against real samples: live webcam frames measured glare_ratio == 0.0 essentially
# always, while a phone screen held up to the camera measured 0.16-0.54 (backlit-screen glare).
# -0.15 gives margin below the live baseline (~0.0 to 0.16) and above the glare-penalty range
# (~-0.5 to -0.7). See face_service liveness log for the raw numbers this was derived from.
LIVENESS_SCORE_THRESHOLD = -0.15


def _get_face_app() -> FaceAnalysis:
    global _face_app
    if _face_app is None:
        _face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app


def _decode(image_bytes: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image")
    return image


def _liveness_score(face_crop_bgr: np.ndarray) -> float:
    """Heuristic single-frame anti-spoofing score (higher = more likely a live capture).

    This is a best-effort heuristic, not a trained classifier. An earlier version also scored
    moire/aliasing energy from the FFT spectrum, but real calibration data showed that signal sits
    at ~0.3 for essentially every frame regardless of content at this crop resolution — it carried
    no discriminating information and was dropped rather than re-tuned. The remaining signal,
    hard-clipped glare from a backlit screen, measured a clean 0.0 on live webcam frames vs.
    0.16-0.54 whenever a phone screen was held up to the camera. This only catches glare from a
    backlit display — a printed photo, or a screen angled to avoid reflection, will slip through.
    """
    gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (128, 128))

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    glare_ratio = float(np.mean(gray > 245))

    score = 0.0
    score += min(laplacian_var / 500.0, 1.0) * 0.3
    score -= min(glare_ratio * 5.0, 1.0) * 0.7

    print(f"[liveness] laplacian_var={laplacian_var:.2f} glare_ratio={glare_ratio:.4f} score={score:.4f}", flush=True)
    return score


def detect_faces(image_bytes: bytes) -> list[dict]:
    image = _decode(image_bytes)
    faces = _get_face_app().get(image)
    if not faces:
        raise ValueError("No face detected in image")

    height, width = image.shape[:2]
    results = []
    for face in faces:
        x1, y1, x2, y2 = face.bbox
        x1, y1 = max(int(x1), 0), max(int(y1), 0)
        x2, y2 = min(int(x2), width), min(int(y2), height)
        crop = image[y1:y2, x1:x2]
        score = _liveness_score(crop) if crop.size else -1.0

        results.append(
            {
                "embedding": face.normed_embedding.tolist(),
                "bbox": [float(v) for v in face.bbox],
                "liveness_score": float(score),
                "is_live": bool(score >= LIVENESS_SCORE_THRESHOLD),
            }
        )
    return results


def extract_embedding(image_bytes: bytes) -> list[float]:
    """Single largest face — used for enrollment, where exactly one subject is expected."""
    faces = detect_faces(image_bytes)
    largest = max(faces, key=lambda face: (face["bbox"][2] - face["bbox"][0]) * (face["bbox"][3] - face["bbox"][1]))
    return largest["embedding"]
