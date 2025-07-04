from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from collections import defaultdict
import cv2
import torch
import os
import numpy as np  # added for conversion

# Allowlist DetectionModel global
torch.serialization.add_safe_globals([
    "ultralytics.nn.tasks.DetectionModel"
])

model_path = os.path.join(os.path.dirname(__file__), "best.pt")
model = YOLO(model_path)

CLASS_NAMES = ["flowers", "green", "red", "turning red"]

# Store unique object IDs per class
unique_ids_per_class = defaultdict(set)

def run_batch_tracker(image_list):
    """
    Process all images together and track unique tomatoes across them.
    image_list: list of PIL Image objects
    """
    global unique_ids_per_class
    unique_ids_per_class.clear()

    # Initialize DeepSort tracker only once
    tracker = DeepSort()

    for image in image_list:
        # Convert PIL Image to numpy array in BGR format
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        results = model(frame)
        result = results[0]
        detections = []

        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            detections.append((xyxy, conf, cls_id))

        tracks = tracker.update_tracks(
            [(det[0], det[1], det[2]) for det in detections],
            frame=frame
        )

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            cls_id = track.det_class
            unique_ids_per_class[cls_id].add(track_id)

    return get_total_counts()

def get_total_counts():
    """
    Return the total unique counts by class.
    """
    return {
        CLASS_NAMES[i]: len(unique_ids_per_class[i])
        for i in range(len(CLASS_NAMES))
    }
