from ultralytics import YOLO
import cv2
import numpy as np
from collections import defaultdict
import time
import uuid
import requests

# โหลดโมเดล YOLO ที่เทรนมาแล้ว
model = YOLO('d:/Files/[02] My Works/CPE495/best.pt')  # ตรวจจับหัวคน (class 0)
cap = cv2.VideoCapture('d:/Files/[02] My Works/CPE495/003.MOV')  # ตรวจสอบว่าไฟล์นี้มีนามสกุลถูกต้องและอยู่ในโฟลเดอร์เดียวกัน
TARGET_RESOLUTION = (1920, 1080)
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Track คนจากตำแหน่ง centroid
tracked_ids = {}
movement_history = defaultdict(list)
person_behavior_by_minute = defaultdict(list)
frame_count = 0
start_time = time.time()

def calculate_behavior_level(movement):
    if movement < 5:
        return 1  # แทบไม่ขยับ
    elif movement < 15:
        return 2  # ขยับเล็กน้อย
    elif movement < 30:
        return 3  # เคลื่อนไหวบ่อย
    elif movement < 60:
        return 4  # ขยับตัวมาก
    else:
        return 5  # เคลื่อนไหวเยอะมาก

def calculate_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    current_minute = int((time.time() - start_time) // 60)
    resized_frame = cv2.resize(frame, TARGET_RESOLUTION)
    
    results = model(resized_frame)
    detections = []

    for result in results[0].boxes:
        cls = int(result.cls[0])
        conf = float(result.conf[0])
        if cls == 0:  # Person class
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            detections.append((center, (x1, y1, x2, y2), conf))

    current_ids = {}
    for center, bbox, conf in detections:
        matched_id = None
        min_dist = float('inf')
        
        for pid, prev_center in tracked_ids.items():
            dist = calculate_distance(center, prev_center)
            if dist < 50 and dist < min_dist:
                min_dist = dist
                matched_id = pid
        
        if matched_id is None:
            matched_id = str(uuid.uuid4())[:8]
        
        tracked_ids[matched_id] = center
        movement_history[matched_id].append(center)
        current_ids[matched_id] = center
        
        radius = max((bbox[2] - bbox[0]), (bbox[3] - bbox[1])) // 4
        cv2.circle(resized_frame, center, radius, (0, 255, 0), 2)
        cv2.putText(resized_frame, f'ID {matched_id[:4]}', (bbox[0], bbox[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # วิเคราะห์พฤติกรรมทุก 1 วินาที (60 เฟรม ถ้า fps=60)
    if frame_count % fps == 0:
        for pid, points in movement_history.items():
            if len(points) >= 2:
                total_movement = sum(
                    calculate_distance(points[i], points[i - 1])
                    for i in range(1, len(points))
                )
                level = calculate_behavior_level(total_movement)
                person_behavior_by_minute[current_minute].append((pid, level))
        movement_history.clear()

    # แสดงจำนวนคนไม่ซ้ำ
    cv2.putText(resized_frame, f'Unique People: {len(tracked_ids)}', (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imshow('Behavior Tracking', resized_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# ==== สรุปผล ====
print("\n==== Behavior Summary ====")
print(f"Total Unique People Detected: {len(tracked_ids)}\n")

for minute, behaviors in person_behavior_by_minute.items():
    print(f"Minute {minute + 1}:")
    for pid, level in behaviors:
        print(f" - ID {pid[:4]}: Behavior Level {level}")
    print()

# ==== สรุปเพิ่มเติม ====
total_levels = 0
total_entries = 0

for behaviors in person_behavior_by_minute.values():
    for _, level in behaviors:
        total_levels += level
        total_entries += 1

average_behavior_level = total_levels / total_entries if total_entries > 0 else 0

print("==== Analysis Summary ====")
print(f"Total Frames Processed: {frame_count}")
print(f"Total Unique People: {len(tracked_ids)}")
print(f"Average Behavior Level: {average_behavior_level:.2f}")

API_URL = 'http://20.189.112.177/postroomdata'
ROOM_ID = 'CPE101' 

def send_data_to_api(unique_people, room_id, average_level):
    payload = {
        "room_id": room_id,
        "total_people": unique_people,
        "behavior_level": average_level,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print("✅ ส่งข้อมูลสำเร็จ")
        else:
            print(f"⚠️ ส่งข้อมูลไม่สำเร็จ: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการส่งข้อมูล: {e}")

send_data_to_api(len(tracked_ids), ROOM_ID, average_behavior_level)