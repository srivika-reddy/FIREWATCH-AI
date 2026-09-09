import hashlib
from pathlib import Path
from urllib.request import urlopen

import config


class FireSmokeDetector:
    """Dedicated Ultralytics fire/smoke detector with an honest fallback."""

    def __init__(self, model_dir, demo_mode=False):
        self.model = None
        self.mode = "demo/mock" if demo_mode else "unavailable"
        self.error = None
        self.model_path = Path(model_dir) / config.FIRE_SMOKE_MODEL_NAME
        if not demo_mode:
            self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO

            if not self.model_path.exists() or not self._matches_checksum(self.model_path):
                self._download_model()
            self.model = YOLO(str(self.model_path))
            names = {str(name).lower() for name in self.model.names.values()}
            if not {"fire", "smoke"}.issubset(names):
                raise RuntimeError(f"Expected fire/smoke classes, found: {sorted(names)}")
            self.mode = "real model"
        except Exception as error:
            self.model = None
            self.error = str(error)

    @staticmethod
    def _matches_checksum(path):
        digest = hashlib.sha256()
        with path.open("rb") as model_file:
            for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().upper() == config.FIRE_SMOKE_MODEL_SHA256

    def _download_model(self):
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.model_path.with_suffix(".download")
        try:
            with urlopen(config.FIRE_SMOKE_MODEL_URL, timeout=60) as response, temporary_path.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            if not self._matches_checksum(temporary_path):
                raise RuntimeError("Downloaded fire/smoke model failed SHA-256 verification.")
            temporary_path.replace(self.model_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def detect(self, image):
        result = {
            "fire": False,
            "fire_confidence": 0.0,
            "smoke": False,
            "smoke_confidence": 0.0,
            "boxes": [],
            "mode": self.mode,
        }
        if self.mode == "demo/mock":
            result["message"] = "Dedicated fire/smoke model disabled; DEMO/MOCK mode is active."
            return result
        if self.model is None or image is None:
            result["message"] = self.error or "Dedicated fire/smoke model is unavailable."
            return result
        try:
            prediction = self.model.predict(image, verbose=False, conf=0.25)[0]
            names = prediction.names
            for box in prediction.boxes:
                label = str(names[int(box.cls[0])]).lower()
                confidence = float(box.conf[0])
                coordinates = [int(value) for value in box.xyxy[0].tolist()]
                result["boxes"].append({"label": label, "confidence": confidence, "xyxy": coordinates})
                if label == "fire":
                    result["fire_confidence"] = max(result["fire_confidence"], confidence)
                elif label == "smoke":
                    result["smoke_confidence"] = max(result["smoke_confidence"], confidence)
            result["fire"] = result["fire_confidence"] >= config.FIRE_THRESHOLD
            result["smoke"] = result["smoke_confidence"] >= config.SMOKE_THRESHOLD
        except Exception as error:
            result["message"] = str(error)
        return result
