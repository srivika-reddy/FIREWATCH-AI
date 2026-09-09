from pathlib import Path
from shutil import copy2

import config


class ObjectDetector:
    """Optional YOLO adapter for classes supported by the selected model."""

    ANIMAL_CLASSES = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}
    VEHICLE_CLASSES = {"bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat"}

    def __init__(self, model_dir):
        self.model = None
        self.mode = "unavailable"
        self.error = None
        model_path = Path(model_dir) / config.YOLO_MODEL_NAME
        try:
            from ultralytics import YOLO
            # Ultralytics downloads the official model automatically when the
            # model name is passed and no local copy exists.
            if model_path.exists():
                self.model = YOLO(str(model_path))
            else:
                self.model = YOLO(config.YOLO_MODEL_NAME)
                downloaded_path = Path(config.YOLO_MODEL_NAME)
                if downloaded_path.exists():
                    model_path.parent.mkdir(parents=True, exist_ok=True)
                    copy2(downloaded_path, model_path)
            self.mode = "yolo"
        except Exception as error:
            self.model = None
            self.error = str(error)

    def detect(self, image):
        result = {"people": 0, "animals": 0, "vehicles": 0, "boxes": [], "mode": self.mode}
        if self.model is None or image is None:
            return result
        try:
            predictions = self.model.predict(image, verbose=False, conf=0.25)[0]
            names = predictions.names
            for box in predictions.boxes:
                class_id = int(box.cls[0])
                label = str(names[class_id]).lower()
                confidence = float(box.conf[0])
                coordinates = [int(value) for value in box.xyxy[0].tolist()]
                if label == "person":
                    result["people"] += 1
                elif label in self.ANIMAL_CLASSES:
                    result["animals"] += 1
                elif label in self.VEHICLE_CLASSES:
                    result["vehicles"] += 1
                result["boxes"].append({"label": label, "confidence": confidence, "xyxy": coordinates})
        except Exception as error:
            result["error"] = str(error)
        return result
