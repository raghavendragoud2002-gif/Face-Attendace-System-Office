# app/enroll_orb.py
import cv2
import os
import pickle
import mediapipe as mp
import numpy as np

IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'images')
KNOWN_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'known_orb.pkl')

def build_known():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    # Initialize MediaPipe Face Detection
    mp_face_detection = mp.solutions.face_detection
    face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)
    
    orb = cv2.ORB_create(1000)
    known = []
    files = sorted([f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    print(f"[INFO] Found {len(files)} image files in {IMAGES_DIR}")
    
    for fname in files:
        path = os.path.join(IMAGES_DIR, fname)
        print(f"[INFO] Processing: {fname}")
        img = cv2.imread(path)
        
        if img is None:
            print(f"[WARN] Failed to load image: {fname}")
            continue
            
        # Convert to RGB for MediaPipe
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_detection.process(img_rgb)
        
        if not results.detections:
            print(f"[WARN] No face detected in: {fname} - Skipping!")
            continue
            
        # Process the first detected face
        detection = results.detections[0]
        bboxC = detection.location_data.relative_bounding_box
        ih, iw, _ = img.shape
        x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
        
        # Ensure valid coordinates
        x, y = max(0, x), max(0, y)
        w, h = min(w, iw - x), min(h, ih - y)
        
        # Crop the face
        face_roi = img[y:y+h, x:x+w]
        
        # Resize to standard size (200x200) for consistent feature extraction
        # This fixes the scale mismatch between high-res uploads and low-res webcam
        try:
            face_roi = cv2.resize(face_roi, (200, 200))
        except Exception as e:
            print(f"[WARN] Could not resize face: {e}")
            continue
        
        # Convert to grayscale for ORB
        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # This helps with lighting differences between webcam and enrollment
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray_face = clahe.apply(gray_face)
        
        kp, desc = orb.detectAndCompute(gray_face, None)
        if desc is None:
            print(f"[WARN] No descriptors found for face in: {fname}")
            continue
        
        name = os.path.splitext(fname)[0]
        known.append({'name': name, 'desc': desc, 'image_path': path})
        print(f"[OK] Enrolled: {name} | descriptors: {desc.shape}")
    
    if known:
        with open(KNOWN_PATH, 'wb') as f:
            pickle.dump(known, f)
        print(f"[SUCCESS] Saved {len(known)} known faces to {KNOWN_PATH}")
    else:
        print("[ERROR] No valid faces found in", IMAGES_DIR)

if __name__ == '__main__':
    build_known()