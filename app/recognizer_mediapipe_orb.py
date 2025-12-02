# app/recognizer_mediapipe_orb.py
import cv2
import mediapipe as mp
import pickle
import time
import mysql.connector
import os
from datetime import datetime

# ---------- CONFIG ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_db_password',  # update
    'database': 'face_attendance'    # ensure DB + tables exist or leave DB access optional
}
KNOWN_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'known_orb.pkl')
ATTENDANCE_THROTTLE_SECONDS = 15
CAMERA_INDEX = 0
# ----------------------------

mp_face = mp.solutions.face_detection

orb = cv2.ORB_create(1000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

def load_known():
    if not os.path.exists(KNOWN_PATH):
        return []
    with open(KNOWN_PATH, 'rb') as f:
        return pickle.load(f)

def query_person_details(name):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM persons WHERE name = %s LIMIT 1", (name,))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        return None

def mark_attendance(person_id, name, mode='camera'):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO attendance (person_id, name, checkin_time, mode) VALUES (%s,%s,%s,%s)",
                    (person_id, name, now, mode))
        conn.commit()
        conn.close()
        print('Attendance logged for', name, now)
    except Exception as e:
        # DB optional — print error but continue
        print('DB write error (attendance):', e)

def recognize_and_run():
    known = load_known()
    if not known:
        print("No enrolled people found. Run app/enroll_orb.py first.")
        return

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("OpenCV: cannot open camera. Check macOS Camera permissions (System Settings → Privacy & Security → Camera).")
        return

    with mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6) as detector:
        last_seen = {}
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Frame read failed, exiting.")
                break

            h, w = frame.shape[:2]
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(img_rgb)

            overlay = frame.copy()

            if results.detections:
                for det in results.detections:
                    box = det.location_data.relative_bounding_box
                    x1 = int(box.xmin * w)
                    y1 = int(box.ymin * h)
                    bw = int(box.width * w)
                    bh = int(box.height * h)
                    x2, y2 = x1 + bw, y1 + bh

                    pad = max(10, int(0.15 * max(bw, bh)))
                    sx = max(0, x1 - pad); sy = max(0, y1 - pad)
                    ex = min(w, x2 + pad); ey = min(h, y2 + pad)
                    face = frame[sy:ey, sx:ex]
                    if face.size == 0:
                        continue

                    face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                    kp2, desc2 = orb.detectAndCompute(face_gray, None)
                    best_name = "Unknown"
                    best_score = 0.0

                    if desc2 is not None:
                        for person in known:
                            desc1 = person.get('desc', None)
                            if desc1 is None:
                                continue

                            # ensure types match
                            if desc1.dtype != desc2.dtype:
                                try:
                                    desc1 = desc1.astype(desc2.dtype)
                                except Exception:
                                    continue

                            try:
                                matches = bf.match(desc1, desc2)
                            except Exception:
                                continue
                            if not matches:
                                continue

                            distances = [m.distance for m in matches]
                            good = [d for d in distances if d < 60]
                            score = len(good) / max(1, len(matches))

                            if score > best_score:
                                best_score = score
                                best_name = person['name']

                    if best_score < 0.20:
                        best_name = "Unknown"

                    color = (0, 255, 170) if best_name != "Unknown" else (0, 120, 255)
                    cv2.rectangle(overlay, (sx, sy), (ex, ey), color, 2)
                    label = f"{best_name} ({best_score:.2f})"
                    cv2.putText(overlay, label, (sx, sy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

                    details = query_person_details(best_name)
                    if details:
                        cv2.rectangle(overlay, (ex + 10, sy), (ex + 300, sy + 90), (0, 0, 0), -1)
                        cv2.putText(overlay, f"{details.get('name')}", (ex + 15, sy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,200), 2)
                        cv2.putText(overlay, f"ID: {details.get('identity') or ''}", (ex + 15, sy + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,255), 1)
                        if details.get('instagram'):
                            cv2.putText(overlay, f"IG: {details.get('instagram')}", (ex + 15, sy + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,255), 1)
                    else:
                        cv2.rectangle(overlay, (ex + 10, sy), (ex + 260, sy + 60), (0,0,0), -1)
                        cv2.putText(overlay, best_name, (ex + 15, sy + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,200), 2)

                    # attendance logging (throttle)
                    if best_name != "Unknown":
                        now_ts = time.time()
                        last = last_seen.get(best_name, 0)
                        if now_ts - last > ATTENDANCE_THROTTLE_SECONDS:
                            person_id = None
                            if details and details.get('id'):
                                person_id = details.get('id')
                            mark_attendance(person_id, best_name, mode='camera')
                            last_seen[best_name] = now_ts

            blended = cv2.addWeighted(overlay, 0.9, frame, 0.1, 0)
            cv2.imshow('Smart HUD - MediaPipe + ORB', blended)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    recognize_and_run()