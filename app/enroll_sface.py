import cv2
import numpy as np
import os
import pickle

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')
KNOWN_PATH = os.path.join(DATA_DIR, 'known_sface.pkl')

# Models
DETECTOR_PATH = os.path.join(BASE_DIR, 'models', 'face_detection_yunet_2023mar.onnx')
RECOGNIZER_PATH = os.path.join(BASE_DIR, 'models', 'face_recognition_sface_2021dec.onnx')

print(f"[INFO] Loading models...")
try:
    # Lowered threshold to 0.6 to detect side profiles
    detector = cv2.FaceDetectorYN.create(DETECTOR_PATH, "", (320, 320), 0.6, 0.3, 5000)
    recognizer = cv2.FaceRecognizerSF.create(RECOGNIZER_PATH, "")
except Exception as e:
    print(f"[ERROR] Failed to load models: {e}")
    exit(1)

known_faces = []

if not os.path.exists(IMAGES_DIR):
    print(f"[ERROR] Images directory not found: {IMAGES_DIR}")
    exit(1)

files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
print(f"[INFO] Found {len(files)} images.")

for filename in files:
    path = os.path.join(IMAGES_DIR, filename)
    
    # Extract ID and Name
    # Format: ID_Name_Suffix.jpg or ID_Name.jpg
    name_part = os.path.splitext(filename)[0]
    parts = name_part.split('_')
    
    if len(parts) >= 2:
        emp_id = parts[0]
        name = parts[1]
        full_name = f"{emp_id}_{name}" # Store as ID_Name
    else:
        print(f"[WARN] Invalid filename format: {filename}")
        continue

    img = cv2.imread(path)
    if img is None:
        continue

    h, w, _ = img.shape
    detector.setInputSize((w, h))
    
    # Detect
    faces = detector.detect(img)
    if faces[1] is not None:
        # Take the face with highest confidence
        face = faces[1][0]
        
        # Align and Crop
        face_align = recognizer.alignCrop(img, face)
        
        # Extract Feature
        face_feature = recognizer.feature(face_align)
        
        known_faces.append({
            'name': full_name,
            'feature': face_feature,
            'filename': filename
        })
        print(f"[OK] Enrolled: {full_name} from {filename}")
    else:
        print(f"[WARN] No face detected in {filename}")

# Save
with open(KNOWN_PATH, 'wb') as f:
    pickle.dump(known_faces, f)

print(f"[SUCCESS] Saved {len(known_faces)} faces to {KNOWN_PATH}")
