# FireWatch AI Hackathon Technical Summary

## Problem

Forest monitoring teams need early visual signals for fire and smoke while also understanding whether people, animals, or vehicles are present in a monitored frame. Manual review can be slow and does not provide a consistent alert history.

## Proposed Solution

FireWatch AI is a local web prototype where a user uploads an image or short video. Flask coordinates a dedicated fire/smoke model and a general Ultralytics YOLO object detector, then shows confidence values, bounding boxes, counts, an overall alert state, and SQLite history.

## Technical Approach

- Flask exposes the dashboard and JSON detection endpoints.
- OpenCV decodes images and samples video frames.
- The dedicated YOLOv8 model detects `fire` and `smoke`.
- The general YOLO model counts supported people, animals, and vehicle classes.
- The result uses centralized fire and smoke thresholds to classify `SAFE`, `WARNING`, or `FIRE ALERT`.
- Annotated image previews and alert rows are returned to the dashboard.

## Innovation

The prototype combines two intentionally separate computer-vision responsibilities instead of claiming that a generic object model detects fire. It combines:

- Early fire and smoke signals
- Awareness of supported people, animal, and vehicle classes
- Confidence-based status decisions
- Visual bounding boxes for detections
- A local audit trail in SQLite

This is a practical integration prototype, not a claim of production accuracy or emergency-service readiness.

## Current Prototype Results

| Test | Verified result |
|---|---|
| Normal forest image | `SAFE`; fire and smoke confidence `0%` |
| Smoke-focused image | `WARNING`; smoke confidence approximately `83.91%`, smoke threshold `60%`; fire approximately `36.14%` |
| Wildfire image | `FIRE ALERT`; fire confidence approximately `41.38%`; one fire box |
| Object test image | `SAFE`; 4 people, 1 vehicle, 5 YOLO boxes |

The smoke-focused image also returned a smoke bounding box. All tested image previews were served successfully and results were written to SQLite alert history.

## Future Scope

The following are future improvements, not current features:

- Send browser camera frames through the detection pipeline
- Add GPS/location integration
- Add notification services
- Evaluate or train a stronger fire/smoke model
- Expand animal classes and validate them with forest-specific data
- Deploy behind a production WSGI server or cloud service
- Optimize inference for edge devices
