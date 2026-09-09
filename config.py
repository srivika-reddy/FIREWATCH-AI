from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
MODEL_DIR = BASE_DIR / "models"
YOLO_MODEL_NAME = "yolo11n.pt"
FIRE_SMOKE_MODEL_NAME = "fire_smoke_best.pt"
FIRE_SMOKE_MODEL_URL = "https://github.com/longlivewama/fire-and-smoke-detection/raw/main/best.pt"
FIRE_SMOKE_MODEL_SHA256 = "2E065E86DDE76BA22548DBC1246848C79F872E4ACAD198860AF69D7F8A2392E9"
DATABASE_PATH = BASE_DIR / "firewatch.db"

MAX_CONTENT_LENGTH = 100 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
# Calibrated for the integrated fire/smoke model's confidence scale.
FIRE_THRESHOLD = 0.40
SMOKE_THRESHOLD = 0.60
DEMO_MODE = False
DEMO_LOCATION = {
    "name": "Pine Ridge Reserve",
    "latitude": 37.7749,
    "longitude": -122.4194,
}
