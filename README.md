# FireWatch AI

FireWatch AI is a local computer-vision prototype for forest and wildfire safety monitoring. It analyzes uploaded images and short videos with separate fire/smoke and general-object models, presents confidence values and bounding boxes, classifies the result as `SAFE`, `WARNING`, or `FIRE ALERT`, and stores alert history in SQLite.

## Overview

The dashboard is designed for a college hackathon demonstration. It supports a dedicated fire/smoke detector, an Ultralytics YOLO object detector for supported classes, OpenCV image/video processing, annotated image previews, and a simple local audit trail.

## Problem

Manual review of forest imagery can delay recognition of fire or smoke and does not consistently record what was observed. A lightweight visual monitoring workflow can help a user review signals and organize the results for a prototype demonstration.

## Solution

The user uploads an image or short video in the dashboard. Flask saves and validates the file, OpenCV decodes or samples it, both detectors run independently, and the backend returns a JSON result. Image results receive an annotated preview, and every processed result is recorded in SQLite alert history.

## Key Features

- Image upload and processing
- Lightweight video upload processing with sampled frames
- Dedicated `fire` and `smoke` model
- General YOLO detection for supported people, animal, and vehicle classes
- Confidence values and bounding boxes
- `SAFE`, `WARNING`, and `FIRE ALERT` statuses
- SQLite alert history with counts and status
- Demo monitoring location card
- Browser camera preview control; camera frames are not currently sent to the detection API
- Clearly labelled real-model, unavailable, and DEMO/MOCK detector modes

## Technology Stack

- Python 3
- Flask 3
- HTML, CSS, and JavaScript
- OpenCV
- Ultralytics YOLO
- SQLite
- Local filesystem storage for uploads, previews, and model weights

## System Architecture

```text
User -> Dashboard -> Flask API -> OpenCV processing
								  |-> Fire/smoke model
								  |-> General YOLO model
								  v
						 Status + JSON result + preview
								  |-> Dashboard
								  |-> SQLite alert history
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/architecture.mmd](docs/architecture.mmd), and [docs/data-flow.mmd](docs/data-flow.mmd) for the detailed architecture and diagrams.

## AI Models

### Fire/smoke model

`models/fire_smoke_best.pt` is a YOLOv8 model loaded through Ultralytics. It exposes `fire` and `smoke` classes. `detector/fire_detector.py` downloads the configured artifact if needed, verifies its SHA-256 checksum, validates the classes, and returns confidence values and boxes.

### General object model

`models/yolo11n.pt` is the lightweight general Ultralytics model. The application counts these supported classes:

- People: `person`
- Animals: `bird`, `cat`, `dog`, `horse`, `sheep`, `cow`, `elephant`, `bear`, `zebra`, `giraffe`
- Vehicles: `bicycle`, `car`, `motorcycle`, `airplane`, `bus`, `train`, `truck`, `boat`

Generic YOLO is not used as a fire or smoke detector.

## Detection Workflow

For images, the backend saves the upload, decodes it with OpenCV, runs both models on the same frame, aggregates confidences and counts, draws all returned boxes on a processed image, stores an alert, and returns JSON.

For videos, OpenCV reads at most 60 frames and analyzes every fifth frame. The maximum people, animal, and vehicle counts across sampled frames are returned with the last sampled result. The current video endpoint does not create a processed video preview.

## Alert States

Thresholds are centralized in `config.py`:

| Condition | Status |
|---|---|
| Fire confidence >= `0.40` | `FIRE ALERT` |
| Otherwise, smoke confidence >= `0.60` | `WARNING` |
| Otherwise | `SAFE` |

Fire is checked first, so a fire alert takes precedence over a smoke warning.

## Project Structure

```text
firewatch-ai/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── THIRD_PARTY_NOTICES.md
├── firewatch.db
├── detector/
├── database/
├── models/
├── templates/
├── static/
├── uploads/
└── docs/
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for each important file and folder.

## Installation

From PowerShell in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The model files are already present in `models/`. On a fresh setup, the detector code can download the configured model artifacts when they are missing and the environment has network access.

## Running the Application

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Open <http://127.0.0.1:5000> in a browser.

The command starts Flask's local development server. A production WSGI deployment is not configured.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Render the dashboard |
| `POST` | `/api/detect/image` | Detect an uploaded image; multipart field: `file` |
| `POST` | `/api/detect/video` | Sample an uploaded video; multipart field: `file` |
| `GET` | `/api/alerts` | Return the newest 25 SQLite alert rows |
| `DELETE` | `/api/alerts` | Clear all alert history |
| `GET` | `/uploads/<filename>` | Serve a local uploaded or processed file |

Image and video upload errors return JSON with useful HTTP error statuses for missing files, unsupported extensions, invalid media, oversized uploads, and processing failures.

## Testing

The application has been tested through the Flask test client and the browser dashboard using actual image fixtures.

Verified states:

- `SAFE`: normal forest image; fire and smoke confidence `0%`.
- `WARNING`: smoke-focused image; smoke confidence approximately `83.91%` against the `60%` threshold; fire confidence approximately `36.14%`.
- `FIRE ALERT`: wildfire image; fire confidence approximately `41.38%` against the `40%` threshold; one fire box.

Verified general-object result:

- Object test image: 4 people, 1 vehicle, and 5 YOLO boxes.

The tests also verified processed image previews, confidence values, dashboard updates, API responses, and SQLite alert-history rows.

## Example Results

| Scenario | Status | Fire | Smoke | Object counts |
|---|---|---:|---:|---|
| Normal forest | `SAFE` | 0% | 0% | 0 people, 0 animals, 0 vehicles |
| Smoke-focused image | `WARNING` | ~36.14% | ~83.91% | 0 people, 0 animals, 0 vehicles |
| Wildfire image | `FIRE ALERT` | ~41.38% | 0% in the verified fixture | 0 people, 0 animals, 0 vehicles |
| Object test image | `SAFE` | 0% | 0% | 4 people, 0 animals, 1 vehicle |

## Limitations

- This is a college hackathon prototype, not an emergency alerting service.
- Detection accuracy depends on the model, training data, image quality, viewpoint, and lighting.
- The local Flask development server is not a production deployment.
- Browser camera preview is present, but camera frames are not processed by the backend.
- The location card uses static demo coordinates; GPS integration is not implemented.
- Video processing samples frames and does not stream continuously or return a processed video.
- There is no authentication, authorization, notification service, multi-user storage, or cloud synchronization.
- The animal list is limited to the classes configured in `object_detector.py`.

## Model/Dataset Licensing Note

The fire/smoke model repository is published under Apache-2.0 and is documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The repository states that the model was trained on a Roboflow dataset, but the underlying dataset's separate terms are not included. Verify model and dataset licensing before redistribution or public deployment. Also review the applicable Ultralytics/model terms before redistributing model weights.

## Future Improvements

These are future improvements, not current features:

- Real-time camera frame inference
- GPS/location integration
- Notification services
- Improved and better-validated fire/smoke models
- Additional animal classes and forest-specific training data
- Cloud or production deployment
- Edge-device optimization

## More Documentation

- [Technical architecture](docs/ARCHITECTURE.md)
- [Architecture diagram](docs/architecture.mmd)
- [Architecture diagram SVG](docs/architecture.svg)
- [Architecture diagram PNG](docs/architecture.png)
- [Data-flow diagram](docs/data-flow.mmd)
- [Hackathon technical summary](docs/HACKATHON_TECHNICAL_SUMMARY.md)
- [Judge Q&A](docs/JUDGE_QA.md)
- [Project structure](docs/PROJECT_STRUCTURE.md)
