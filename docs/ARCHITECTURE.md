# FireWatch AI Technical Architecture

## System Overview

FireWatch AI is a local Flask prototype for forest and wildfire safety monitoring. A user uploads an image or short video through the dashboard. The application runs two separate computer-vision paths:

- A dedicated YOLOv8 fire/smoke model detects `fire` and `smoke`.
- An official lightweight Ultralytics YOLO model detects supported COCO objects, including people, animals, and vehicles.

The application returns confidence values, detection boxes, object counts, an overall status, and a processed image preview for image uploads. Each processed image or video result is recorded in SQLite alert history.

## High-Level Architecture

```text
User
  |
  v
FireWatch Dashboard (HTML/CSS/JavaScript)
  |
  v
Flask API
  |
  +--> Image upload --> OpenCV decode --> both detectors
  |
  +--> Video upload --> OpenCV frame sampling --> both detectors
                                      |
                    +-----------------+------------------+
                    v                                    v
          Fire/smoke detector                   YOLO object detector
          fire, smoke classes                   person, animals, vehicles
                    +-----------------+------------------+
                                      v
                              Detection result
                                      |
                                      v
                              Alert decision logic
                              SAFE / WARNING / FIRE ALERT
                                      |
                 +--------------------+--------------------+
                 v                                         v
        JSON response and dashboard               SQLite alert history
```

## Component Architecture

| Component | Implemented responsibility |
|---|---|
| Frontend | `templates/index.html` defines the dashboard. `static/js/app.js` uploads files, renders results, loads history, and provides a browser camera preview. `static/css/style.css` provides responsive styling. |
| Flask backend | `app.py` serves the dashboard, validates uploads, invokes detection, creates previews, writes alerts, and exposes JSON endpoints. |
| Image processing | OpenCV decodes uploaded images. The image is passed to both detectors. A processed copy is written with all returned detection boxes. |
| Video processing | OpenCV opens the uploaded video. Up to 60 frames are read, and every fifth frame is analyzed. The maximum people, animal, and vehicle counts across sampled frames are returned. |
| Fire/smoke detector | `detector/fire_detector.py` loads the verified `models/fire_smoke_best.pt` model, downloads it when missing, validates its `fire` and `smoke` classes, aggregates confidence by class, and returns boxes. |
| YOLO detector | `detector/object_detector.py` loads `models/yolo11n.pt` or asks Ultralytics to download it. It counts supported person, animal, and vehicle labels and returns prediction boxes. |
| Alert/status logic | `status_for()` in `app.py` compares fire confidence first, then smoke confidence, with thresholds from `config.py`. |
| SQLite database | `database/database.py` creates the `alerts` table, inserts rows, lists the newest 25 rows, and clears history. |
| Upload/preview handling | Files are restricted by extension and saved under `uploads/` using `secure_filename`. Image results receive a served processed preview URL. |
| Configuration | `config.py` centralizes paths, allowed extensions, upload size, model names/URL/checksum, thresholds, demo mode, and the demo location. |

## AI Detection Pipeline

### Image path

1. Flask receives a multipart file under the `file` field.
2. The filename extension is checked against the configured image extensions.
3. The file is saved to `uploads/` and decoded with `cv2.imread()`.
4. The same OpenCV image is passed independently to the fire/smoke detector and YOLO object detector.
5. Each model returns detections with labels, confidence values, and `xyxy` box coordinates.
6. Fire and smoke confidence values are aggregated by class. Supported YOLO labels are converted into people, animal, and vehicle counts.
7. The alert status is calculated from fire/smoke confidence thresholds.
8. Object and fire/smoke boxes are drawn onto a processed image.
9. The result is saved to SQLite and returned as JSON.

### Video path

1. Flask validates and saves the uploaded video.
2. OpenCV opens the file and reads at most 60 frames.
3. Every fifth readable frame is analyzed by both detectors.
4. The maximum people, animal, and vehicle counts across sampled frames are merged into the last sampled result.
5. The final result is saved to SQLite and returned as JSON.

The current video endpoint does not create a processed video file or a video preview URL.

## Alert Logic

The thresholds are centralized in `config.py`:

- `FIRE_THRESHOLD = 0.40`
- `SMOKE_THRESHOLD = 0.60`

The order in `status_for()` is significant:

| Condition | Status |
|---|---|
| Fire confidence >= 40% | `FIRE ALERT` |
| Otherwise, smoke confidence >= 60% | `WARNING` |
| Otherwise | `SAFE` |

A fire result takes precedence over smoke. The alert confidence stored in history is the larger of fire and smoke confidence. Alert types are `Fire`, `Fire + Smoke`, `Smoke`, or `Object scan` based on the result.

## API Architecture

| Method | Endpoint | Request | Purpose |
|---|---|---|---|
| `GET` | `/` | None | Renders the dashboard with the demo location and detector modes. |
| `POST` | `/api/detect/image` | Multipart field `file`; JPG, JPEG, PNG, or WEBP | Runs both detectors, writes an annotated image, stores an alert, and returns detection JSON. |
| `POST` | `/api/detect/video` | Multipart field `file`; MP4, MOV, AVI, MKV, or WEBM | Samples up to 60 video frames, runs detection on every fifth frame, stores an alert, and returns the final aggregate result. |
| `GET` | `/api/alerts` | None | Returns the newest 25 SQLite alert rows as JSON. |
| `DELETE` | `/api/alerts` | None | Deletes all alert history and returns a confirmation JSON message. |
| `GET` | `/uploads/<filename>` | Filename path | Serves uploaded and processed files from the local uploads directory. |

An image detection response contains `status`, `alert_type`, `confidence`, `objects`, `fire_smoke`, `preview_url`, and `source`. Object results contain counts, boxes, and detector mode. Fire/smoke results contain `fire`, `fire_confidence`, `smoke`, `smoke_confidence`, boxes, and detector mode.

## Database Architecture

The database file is `firewatch.db`. Startup creates this table if it does not exist:

| Field | Type | Meaning |
|---|---|---|
| `id` | INTEGER primary key | Alert row identifier |
| `timestamp` | TEXT | UTC ISO timestamp generated at insert time |
| `alert_type` | TEXT | `Fire`, `Fire + Smoke`, `Smoke`, or `Object scan` |
| `confidence` | REAL | Maximum fire/smoke confidence for the result |
| `people_count` | INTEGER | Count returned by the object detector |
| `animal_count` | INTEGER | Count returned by the object detector |
| `vehicle_count` | INTEGER | Count returned by the object detector |
| `status` | TEXT | `SAFE`, `WARNING`, or `FIRE ALERT` |

The list endpoint sorts by newest inserted row and limits the response to 25 records.

## Model Architecture

### Fire/smoke model

The dedicated model is `models/fire_smoke_best.pt`, loaded through Ultralytics YOLO. If it is absent or its SHA-256 checksum does not match the configured value, the application downloads the configured GitHub artifact into a temporary file, verifies it, and replaces the local model only after verification. The model is checked for the `fire` and `smoke` classes before being enabled.

The repository is published under Apache-2.0. The repository describes training data from Roboflow, but separate underlying dataset terms must be verified before redistribution or public deployment.

### Object model

The object model is the official lightweight `yolo11n.pt` model loaded through Ultralytics. It is used only for its supported general-object labels. The application counts:

- People: `person`
- Animals: `bird`, `cat`, `dog`, `horse`, `sheep`, `cow`, `elephant`, `bear`, `zebra`, `giraffe`
- Vehicles: `bicycle`, `car`, `motorcycle`, `airplane`, `bus`, `train`, `truck`, `boat`

Generic YOLO is not used as a fire or smoke detector.

## Error Handling

Implemented error handling includes:

- Missing file: HTTP 400 with a useful JSON error.
- Unsupported image or video extension: HTTP 415.
- Undecodable image: HTTP 400.
- Video open failure: HTTP 400.
- Video with no readable frames: HTTP 400.
- Upload larger than 100 MB: HTTP 413.
- Model import/load/inference failures: detector fallback modes or result-level error information instead of application startup failure where possible.
- Unexpected Flask errors: logged server-side and returned as a generic HTTP 500 JSON response.

## Security and Privacy Considerations

This is a local development prototype, not a hardened production service. Uploaded files are stored locally, and the dashboard exposes the local upload route. There is no authentication, authorization, rate limiting, antivirus scanning, content quarantine, or retention policy. Uploaded images and videos may contain sensitive people or location information and should be handled accordingly.

The application uses `secure_filename`, extension allowlists, and a 100 MB request limit, but those controls are not a complete production upload security design.

## Limitations

- The system is a college hackathon prototype and is not an emergency alerting service.
- Model confidence and accuracy depend on training data, image quality, viewpoint, and environment.
- The fire/smoke model is not a guarantee of fire safety or fire absence.
- The underlying Roboflow dataset licensing should be verified before redistribution.
- `app.py` starts Flask's development server on `127.0.0.1:5000`; production deployment is not configured.
- The browser Start Monitoring button shows a local camera preview, but camera frames are not sent through the detection API.
- The configured location is static demo data; GPS integration is not implemented.
- Video processing is lightweight frame sampling, not continuous real-time streaming.
- The current video endpoint does not return a processed video preview.
- Animal support is limited to the listed model labels.
- SQLite history is local and has no multi-user or remote synchronization.
