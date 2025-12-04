# app/enroll_orb.py
import cv2
import os
import pickle

IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'images')
KNOWN_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'known_orb.pkl')

def build_known():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    orb = cv2.ORB_create(1000)
    known = []
    files = sorted([f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    print(f"[INFO] Found {len(files)} image files in {IMAGES_DIR}")
    
    for fname in files:
        path = os.path.join(IMAGES_DIR, fname)
        print(f"[INFO] Processing: {fname}")
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[WARN] Failed to load image: {fname}")
            continue
        
        kp, desc = orb.detectAndCompute(img, None)
        if desc is None:
            print(f"[WARN] No descriptors found for: {fname}")
            continue
        
        name = os.path.splitext(fname)[0]
        known.append({'name': name, 'desc': desc, 'image_path': path})
        print(f"[OK] Enrolled: {name} | descriptors: {desc.shape}")
    
    if known:
        with open(KNOWN_PATH, 'wb') as f:
            pickle.dump(known, f)
        print(f"[SUCCESS] Saved {len(known)} known faces to {KNOWN_PATH}")
    else:
        print("[ERROR] No valid images found in", IMAGES_DIR)

if __name__ == '__main__':
    build_known()