import os
from pathlib import Path

import cv2
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

import config
from database.database import add_alert, clear_alerts, init_db, list_alerts
from detector.fire_detector import FireSmokeDetector
from detector.object_detector import ObjectDetector

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
config.UPLOAD_DIR.mkdir(exist_ok=True)
config.MODEL_DIR.mkdir(exist_ok=True)
init_db(config.DATABASE_PATH)
object_detector = ObjectDetector(config.MODEL_DIR)
fire_detector = FireSmokeDetector(config.MODEL_DIR, config.DEMO_MODE)


def extension_allowed(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def status_for(fire_smoke):
    if fire_smoke["fire_confidence"] >= config.FIRE_THRESHOLD:
        return "FIRE ALERT"
    if fire_smoke["smoke_confidence"] >= config.SMOKE_THRESHOLD:
        return "WARNING"
    return "SAFE"


def analyze_frame(frame):
    objects = object_detector.detect(frame)
    fire = fire_detector.detect(frame)
    status = status_for(fire)
    if status == "FIRE ALERT":
        alert_type = "Fire + Smoke" if fire["smoke"] else "Fire"
    else:
        alert_type = "Smoke" if status == "WARNING" else "Object scan"
    confidence = max(fire["fire_confidence"], fire["smoke_confidence"], 0.0)
    return {
        "status": status,
        "alert_type": alert_type,
        "confidence": confidence,
        "objects": objects,
        "fire_smoke": fire,
    }


def write_annotated_image(image, filename, boxes):
    annotated = image.copy()
    for box in boxes:
        left, top, right, bottom = box["xyxy"]
        label = f'{box["label"]} {box["confidence"]:.0%}'
        cv2.rectangle(annotated, (left, top), (right, bottom), (201, 232, 107), 2)
        cv2.putText(annotated, label, (left, max(18, top - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (201, 232, 107), 2, cv2.LINE_AA)
    output_name = f"processed_{filename}"
    output_path = config.UPLOAD_DIR / output_name
    cv2.imwrite(str(output_path), annotated)
    return output_name


def save_alert(result):
    counts = result["objects"]
    add_alert(config.DATABASE_PATH, {
        "alert_type": result["alert_type"],
        "confidence": result["confidence"],
        "people_count": counts["people"],
        "animal_count": counts["animals"],
        "vehicle_count": counts["vehicles"],
        "status": result["status"],
    })


@app.get("/")
def index():
    return render_template("index.html", location=config.DEMO_LOCATION, demo_mode=config.DEMO_MODE,
                           detector_mode=object_detector.mode, fire_mode=fire_detector.mode)


@app.post("/api/detect/image")
def detect_image():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"error": "Choose an image file first."}), 400
    if not extension_allowed(upload.filename, config.ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({"error": "Unsupported image format. Use JPG, PNG, or WEBP."}), 415
    filename = secure_filename(upload.filename)
    path = config.UPLOAD_DIR / filename
    upload.save(path)
    image = cv2.imread(str(path))
    if image is None:
        return jsonify({"error": "The image could not be decoded."}), 400
    result = analyze_frame(image)
    boxes = result["objects"]["boxes"] + result["fire_smoke"]["boxes"]
    result["preview_url"] = f"/uploads/{write_annotated_image(image, filename, boxes)}"
    result["source"] = filename
    save_alert(result)
    return jsonify(result)


@app.post("/api/detect/video")
def detect_video():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"error": "Choose a video file first."}), 400
    if not extension_allowed(upload.filename, config.ALLOWED_VIDEO_EXTENSIONS):
        return jsonify({"error": "Unsupported video format. Use MP4, MOV, AVI, MKV, or WEBM."}), 415
    filename = secure_filename(upload.filename)
    path = config.UPLOAD_DIR / filename
    upload.save(path)
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        return jsonify({"error": "The video could not be opened on this machine."}), 400
    aggregate = {"people": 0, "animals": 0, "vehicles": 0}
    frames = 0
    last_result = analyze_frame(None)
    while frames < 60:
        ok, frame = capture.read()
        if not ok:
            break
        if frames % 5 == 0:
            last_result = analyze_frame(frame)
            for key in aggregate:
                aggregate[key] = max(aggregate[key], last_result["objects"][key])
        frames += 1
    capture.release()
    if frames == 0:
        return jsonify({"error": "The video contains no readable frames."}), 400
    last_result["objects"].update(aggregate)
    last_result["frames_processed"] = frames
    last_result["source"] = filename
    save_alert(last_result)
    return jsonify(last_result)


@app.get("/api/alerts")
def alerts():
    return jsonify(list_alerts(config.DATABASE_PATH))


@app.delete("/api/alerts")
def delete_alerts():
    clear_alerts(config.DATABASE_PATH)
    return jsonify({"message": "Alert history cleared."})


@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(config.UPLOAD_DIR, filename)


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "File is too large. Maximum size is 100 MB."}), 413


@app.errorhandler(Exception)
def handle_error(error):
    app.logger.exception("Unhandled FireWatch error", exc_info=error)
    return jsonify({"error": "Detection failed. Check the server log for details."}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
