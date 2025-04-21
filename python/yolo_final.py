
from ultralytics import YOLO
import cv2
import numpy as np
from collections import defaultdict
import time
import uuid
import torch
import requests

# โหลดโมเดล YOLO
model = YOLO('C:/Users/topta/OneDrive/Desktop/api/best.pt')
cap = cv2.VideoCapture('C:/Users/topta/OneDrive/Desktop/api/project.mp4')
if not cap.isOpened():
    print(f"❌ เปิดวิดีโอไม่ได้")
    exit()
TARGET_RESOLUTION = (1920, 1080)
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Track คน
tracked_ids = {}
previous_bboxes = {}
movement_history = defaultdict(list)
last_seen_time = {}
frame_count = 0
start_time = time.time()

# สำหรับสรุปทุก 30 วินาที
summary_interval = 5  # วินาที
last_summary_time = time.time()
summary_index = 1

# ค่าปรับล่าสุด
CONF_THRESHOLD = 0.15
MIN_WIDTH = 20
MIN_HEIGHT = 20
MAX_CENTROID_DIST = 45
MIN_IOU_MATCH = 0.15
ID_TIMEOUT = 10  # วินาที

# กำหนด class index สำหรับคน
PERSON_CLASS = 0

# โหมด debug
DEBUG_SHOW_ALL_BOXES = True

# โซนที่ต้องให้ความสำคัญพิเศษ
FOCUS_ZONE_Y = 950  # แถวล่างที่มักมีคนเยอะ

API_URL = 'http://20.189.112.177:3000/postroomdata'
ROOM_ID = 'CPE-901'

def calculate_behavior_level(movement):
    if movement < 15:
        return 1
    elif movement < 30:
        return 2
    elif movement < 60:
        return 3
    elif movement < 100:
        return 4
    else:
        return 5

def calculate_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calculate_iou(box1, box2):
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    box1Area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2Area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    iou = interArea / float(box1Area + box2Area - interArea + 1e-5)
    return iou

def is_chair_zone(center, width, height):
    aspect_ratio = height / float(width)
    x, y = center
    is_chair_like = 0.8 < aspect_ratio < 1.3 and width > 50 and height > 50
    restricted_area = (y > 1000 and x < 300)
    return is_chair_like and restricted_area

def send_data_to_api(unique_people, room_id, average_level):
    payload = {
        "room_id": room_id,
        "total_people": unique_people,
        "behavior_level": average_level,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        print(f"📤 ส่ง payload ไปที่ API: {payload}")
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print("✅ ส่งข้อมูลสำเร็จ")
        else:
            print(f"⚠️ ส่งข้อมูลไม่สำเร็จ: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการส่งข้อมูล: {e}")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("❌ อ่านวิดีโอไม่ได้ หรือวิดีโอจบแล้ว")
        break

    frame_count += 1
    current_time = time.time()
    resized_frame = cv2.resize(frame, TARGET_RESOLUTION)
    results = model(resized_frame)[0]
    detections = []

    for box in results.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        width = x2 - x1
        height = y2 - y1
        center = ((x1 + x2) // 2, (y1 + y2) // 2)

        if DEBUG_SHOW_ALL_BOXES:
            cv2.rectangle(resized_frame, (x1, y1), (x2, y2), (128, 128, 128), 1)

        if cls == PERSON_CLASS and conf > CONF_THRESHOLD and width > MIN_WIDTH and height > MIN_HEIGHT:
            if is_chair_zone(center, width, height):
                continue
            detections.append((center, (x1, y1, x2, y2), conf))

    current_ids = {}
    for center, bbox, conf in detections:
        matched_id = None
        best_score = float('-inf')

        for pid, prev_center in tracked_ids.items():
            prev_bbox = previous_bboxes.get(pid, None)
            if not prev_bbox:
                continue
            dist = calculate_distance(center, prev_center)
            iou = calculate_iou(bbox, prev_bbox)
            if dist > MAX_CENTROID_DIST or iou < MIN_IOU_MATCH:
                continue
            score = (iou * 3.0) - (dist / MAX_CENTROID_DIST)
            if score > best_score:
                best_score = score
                matched_id = pid

        if matched_id is None:
            for pid, last_time in last_seen_time.items():
                if current_time - last_time < ID_TIMEOUT:
                    if pid not in tracked_ids:
                        dist = calculate_distance(center, previous_bboxes[pid][:2])
                        if dist < MAX_CENTROID_DIST * 1.5:
                            matched_id = pid
                            break

        if matched_id is None:
            matched_id = str(uuid.uuid4())[:8]

        tracked_ids[matched_id] = center
        previous_bboxes[matched_id] = bbox
        movement_history[matched_id].append(center)
        current_ids[matched_id] = center
        last_seen_time[matched_id] = current_time

        radius = max((bbox[2] - bbox[0]), (bbox[3] - bbox[1])) // 4
        circle_color = (0, 255, 0) if center[1] < FOCUS_ZONE_Y else (0, 255, 255)
        cv2.circle(resized_frame, center, radius, circle_color, 2)
        cv2.putText(resized_frame, f'ID {matched_id[:4]}', (bbox[0], bbox[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, circle_color, 2)

    # ==== สรุปทุก 30 วินาที ====
    if current_time - last_summary_time >= summary_interval:
        print(f"\n==== Summary Round {summary_index} ({summary_interval} sec) ====")
        all_levels = []
        for pid, points in movement_history.items():
            if len(points) >= 2:
                total_movement = sum(
                    calculate_distance(points[i], points[i - 1])
                    for i in range(1, len(points))
                )
                level = calculate_behavior_level(total_movement)
                all_levels.append(level)
                print(f" - ID {pid[:4]}: Behavior Level {level}")

        print(f"Total People This Round: {len(tracked_ids)}")
        print(f"Frames Processed: {frame_count}\n")

        if all_levels:
            average_level = sum(all_levels) / len(all_levels)
            send_data_to_api(len(tracked_ids), ROOM_ID, average_level)

        summary_index += 1
        last_summary_time = current_time

    expired_ids = [pid for pid, t in last_seen_time.items() if current_time - t > ID_TIMEOUT]
    for pid in expired_ids:
        tracked_ids.pop(pid, None)
        previous_bboxes.pop(pid, None)
        movement_history.pop(pid, None)
        last_seen_time.pop(pid, None)

    cv2.putText(resized_frame, f'People: {len(tracked_ids)}', (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imshow('Behavior Tracking', resized_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
