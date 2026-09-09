# FireWatch AI Judge Q&A

## 1. What problem does FireWatch AI solve?

It provides a simple computer-vision workflow for reviewing forest images or short videos for fire, smoke, and supported people, animal, and vehicle signals. It also records the resulting alert status locally.

## 2. How does fire detection work?

A dedicated Ultralytics YOLO model is loaded from `models/fire_smoke_best.pt`. It returns detections labelled `fire` or `smoke`, confidence values, and bounding boxes. Fire confidence at or above 40% produces `FIRE ALERT`.

## 3. How does smoke detection work?

The same dedicated fire/smoke model has a separate `smoke` class. Smoke confidence at or above 60%, when fire has not crossed its threshold, produces `WARNING`.

## 4. Why use YOLO?

Ultralytics YOLO provides a practical pretrained/inference interface for lightweight object detection and returns class labels, confidence values, and coordinates. The project uses a separate custom fire/smoke YOLO model and a general object YOLO model for different responsibilities.

## 5. How are confidence thresholds used?

`config.py` contains `FIRE_THRESHOLD = 0.40` and `SMOKE_THRESHOLD = 0.60`. The detector aggregates the highest confidence for each class, and the status logic compares those values to the centralized thresholds.

## 6. How does the system decide SAFE/WARNING/FIRE ALERT?

Fire is checked first. Fire at least 40% means `FIRE ALERT`. Otherwise, smoke at least 60% means `WARNING`. If neither condition is met, the result is `SAFE`.

## 7. How are people and vehicles counted?

The general YOLO detector loops through model prediction boxes. `person` increments the people count. Labels in the configured vehicle set increment vehicles. Every prediction box is retained for preview annotation.

## 8. Can it detect animals?

Yes, for the animal labels explicitly supported in code: bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, and giraffe. This is class support, not a guarantee of reliable wildlife recognition in every forest scene.

## 9. How is alert history stored?

SQLite stores a UTC timestamp, alert type, maximum fire/smoke confidence, people count, animal count, vehicle count, and status. The dashboard reads the newest 25 rows through `/api/alerts`.

## 10. Why Flask?

Flask keeps the college prototype small and understandable while providing HTML rendering, multipart upload handling, JSON endpoints, and local development-server support.

## 11. What happens if the AI model fails?

The application catches model loading failures and exposes detector modes such as `unavailable`. The dedicated detector also supports clearly labelled `DEMO_MODE`; inference errors are returned in result information where applicable. This fallback does not create fake real-model detections.

## 12. What are the current limitations?

This is a local prototype. It has no authentication, production deployment, notification service, GPS integration, persistent camera inference, multi-user database, or guaranteed detection accuracy. Video is sampled rather than processed as a continuous stream.

## 13. How could this become a real-world system?

A production version would need validated domain-specific data, model evaluation, secure deployment, authenticated users, durable storage, alert delivery, location integration, privacy controls, monitoring, and operational testing with forestry experts.

## 14. What makes the project different from a simple camera system?

It turns uploaded visual data into separate fire/smoke and object signals, confidence-aware status decisions, annotated previews, and a queryable local alert history. It also avoids treating generic object detection as fire detection.

## 15. How would you improve accuracy?

Collect and label representative forest imagery, evaluate precision/recall by fire and smoke class, tune thresholds on a held-out validation set, test different lighting and camera angles, and validate animal classes with wildlife-specific data. Model licensing and dataset terms would also need review before broader deployment.
