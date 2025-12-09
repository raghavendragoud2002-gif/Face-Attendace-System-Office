# app/server.py
import os
import sys
# Force UTF-8 encoding for stdout/stderr on Windows to prevent emojis from crashing the app
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
import threading
import time
import pickle
import json
from datetime import datetime, date

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector

# recognition imports
import cv2
import mediapipe as mp
import numpy as np

# local helpers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
KNOWN_PATH = os.path.join(DATA_DIR, 'known_sface.pkl')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')

# from enroll_orb import build_known, IMAGES_DIR, KNOWN_PATH # Deprecated

# ---------- CONFIG ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': "Raghu@3033",
    'database': 'face_attendance'
}
# Camera Configuration File
CAMERAS_FILE = os.path.join(BASE_DIR, '..', 'data', 'cameras.json')

def load_cameras():
    if os.path.exists(CAMERAS_FILE):
        try:
            with open(CAMERAS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load cameras.json: {e}")
    # Default Config
    return [
        {'id': 0, 'source': 0, 'name': 'Main Entrance (Webcam)'},
        {'id': 1, 'source': 'http://10.150.144.63:8080/video', 'name': 'Office Area (Wireless)'}
    ]

def save_cameras(cameras):
    try:
        with open(CAMERAS_FILE, 'w') as f:
            json.dump(cameras, f, indent=4)
        print("[INFO] Saved camera config to cameras.json")
    except Exception as e:
        print(f"[ERROR] Failed to save cameras.json: {e}")


def build_known():
    print("[INFO] Rebuilding known faces...")
    # Initialize Models
    DETECTOR_PATH = os.path.join(BASE_DIR, 'models', 'face_detection_yunet_2023mar.onnx')
    RECOGNIZER_PATH = os.path.join(BASE_DIR, 'models', 'face_recognition_sface_2021dec.onnx')
    
    if not os.path.exists(DETECTOR_PATH) or not os.path.exists(RECOGNIZER_PATH):
        print("[ERROR] Models not found for build_known!")
        return

    try:
         # Use local instances to avoid threading issues
         detector = cv2.FaceDetectorYN.create(DETECTOR_PATH, "", (320, 320), 0.6, 0.3, 5000)
         recognizer = cv2.FaceRecognizerSF.create(RECOGNIZER_PATH, "")
    except Exception as e:
        print(f"[ERROR] Failed to load models in build_known: {e}")
        return

    known_faces = []
    if not os.path.exists(IMAGES_DIR):
        print(f"[WARN] Images dir not found: {IMAGES_DIR}")
        return

    files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    for filename in files:
        path = os.path.join(IMAGES_DIR, filename)
        name_part = os.path.splitext(filename)[0]
        parts = name_part.split('_')
        
        emp_id = None
        full_name = name_part
        if len(parts) >= 2:
            emp_id = parts[0]
            full_name = f"{parts[0]}_{parts[1]}"
        
        img = cv2.imread(path)
        if img is None: continue
        
        h, w, _ = img.shape
        detector.setInputSize((w, h))
        faces = detector.detect(img)
        if faces[1] is not None:
            # Take highest confidence face
            face = faces[1][0]
            face_align = recognizer.alignCrop(img, face)
            face_feature = recognizer.feature(face_align)
            
            known_faces.append({
                'id': emp_id,
                'name': full_name,
                'feature': face_feature,
                'filename': filename
            })
            
    with open(KNOWN_PATH, 'wb') as f:
        pickle.dump(known_faces, f)
    print(f"[INFO] Rebuilt known faces: {len(known_faces)} enrolled.")

# Initialize Global Cameras
CAMERAS = load_cameras()
ATTENDANCE_THROTTLE_SECONDS = 60 * 5 # 5 minutes throttle

# Global State for Multi-Camera
camera_frames = {} # {id: frame}
camera_locks = {}  # {id: lock}
for cam in CAMERAS:
    camera_locks[cam['id']] = threading.Lock()


DB_ONLINE = False
outputFrame = None
lock = threading.Lock()

# ensure data directories exist
# ensure data directories exist
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, '..', 'data')
os.makedirs(os.path.join(DATA_DIR, 'images'), exist_ok=True)
OFFLINE_DATA_PATH = os.path.join(DATA_DIR, 'employees.json')
OFFLINE_ATTENDANCE_PATH = os.path.join(DATA_DIR, 'attendance.json')

# Frontend Dist Path
DIST_DIR = os.path.join(ROOT, '..', 'frontend', 'dist')

# Initialize Flask with absolute path to dist
print(f"[INFO] Static Folder (DIST_DIR): {DIST_DIR}")
if os.path.exists(DIST_DIR):
    print("[OK] DIST_DIR exists")
else:
    print("[ERROR] DIST_DIR does NOT exist!")

app = Flask(__name__, static_folder=DIST_DIR)
CORS(app)
def check_db_connection():
    global DB_ONLINE
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.close()
        DB_ONLINE = True
        print("[OK] Database Connected Successfully.")
    except mysql.connector.Error as err:
        DB_ONLINE = False
        print(f"[WARN] Database Connection Failed: {err}")
        print("[WARN] System running in OFFLINE MODE. Attendance will not be saved to DB.")

def get_db():
    if not DB_ONLINE:
        return None
    return mysql.connector.connect(**DB_CONFIG)

def load_offline_data():
    if not os.path.exists(OFFLINE_DATA_PATH):
        return []
    try:
        with open(OFFLINE_DATA_PATH, 'r') as f:
            return json.load(f)
    except:
        return []

def save_offline_data(data):
    with open(OFFLINE_DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def load_offline_attendance():
    if not os.path.exists(OFFLINE_ATTENDANCE_PATH):
        return []
    try:
        with open(OFFLINE_ATTENDANCE_PATH, 'r') as f:
            return json.load(f)
    except:
        return []

def save_offline_attendance(data):
    with open(OFFLINE_ATTENDANCE_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# ---------------- API ROUTES ----------------

@app.route('/api/login', methods=['POST'])
def login():
    if not DB_ONLINE:
        # Fallback for offline mode testing
        data = request.json
        if data.get('username') == 'admin' and data.get('password') == 'admin123':
             return jsonify({'success': True, 'user': {'username': 'admin (offline)'}})
        return jsonify({'success': False, 'message': 'DB Offline & Invalid Default Creds'}), 401

    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM admins WHERE username = %s AND password_hash = %s", (username, password))
        admin = cur.fetchone()
        conn.close()
        
        if admin:
            return jsonify({'success': True, 'user': {'username': admin['username']}})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employees', methods=['GET', 'POST'])
def manage_employees():
    if not DB_ONLINE:
        # Offline Mode: Use JSON
        if request.method == 'GET':
            return jsonify(load_offline_data())
        # POST handled below


    if request.method == 'GET':
        try:
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM employees ORDER BY created_at DESC")
            employees = cur.fetchall()
            conn.close()
            return jsonify(employees)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        name = request.form.get('name')
        emp_id = request.form.get('employee_id')
        dept = request.form.get('department')
        desig = request.form.get('designation')
        email = request.form.get('email')
        
        # Handle multiple files
        files_to_save = []
        if request.files.get('file_front'):
            files_to_save.append(('front', request.files['file_front']))
        if request.files.get('file_left'):
            files_to_save.append(('left', request.files['file_left']))
        if request.files.get('file_right'):
            files_to_save.append(('right', request.files['file_right']))
            
        # Legacy support
        if request.files.get('file'):
            files_to_save.append(('front', request.files['file']))
        
        if not files_to_save or not name or not emp_id:
            return jsonify({'error': 'Missing required fields (name, id, or photos)'}), 400
            
        safe_name = name.strip().replace(' ', '_')
        primary_image_path = None
        
        saved_count = 0
        for suffix, f in files_to_save:
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1] or '.jpg'
                filename = f"{emp_id}_{safe_name}_{suffix}{ext}"
                save_path = os.path.join(DATA_DIR, 'images', filename)
                f.save(save_path)
                saved_count += 1
                
                # Use front image as primary for DB
                if suffix == 'front':
                    primary_image_path = save_path
        
        # If no front image, use the first one saved as primary
        if not primary_image_path and saved_count > 0:
             # Reconstruct path of first file
             suffix, f = files_to_save[0]
             ext = os.path.splitext(f.filename)[1] or '.jpg'
             primary_image_path = os.path.join(DATA_DIR, 'images', f"{emp_id}_{safe_name}_{suffix}{ext}")

        try:
            if DB_ONLINE:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO employees (name, employee_id, department, designation, email, image_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, emp_id, dept, desig, email, primary_image_path))
                conn.commit()
                conn.close()
            else:
                # Offline Save
                employees = load_offline_data()
                new_id = 1
                if employees:
                    new_id = max(e['id'] for e in employees) + 1
                
                new_emp = {
                    'id': new_id,
                    'name': name,
                    'employee_id': emp_id,
                    'department': dept,
                    'designation': desig,
                    'email': email,
                    'image_path': primary_image_path,
                    'created_at': str(datetime.now())
                }
                employees.insert(0, new_emp) # Add to top
                save_offline_data(employees)

            build_known()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<int:id>', methods=['PUT', 'DELETE'])
def employee_operations(id):
    if not DB_ONLINE: 
        # Offline Mode
        employees = load_offline_data()
        
        if request.method == 'DELETE':
            emp = next((e for e in employees if e['id'] == id), None)
            if emp:
                if emp.get('image_path') and os.path.exists(emp['image_path']):
                    os.remove(emp['image_path'])
                employees = [e for e in employees if e['id'] != id]
                save_offline_data(employees)
                build_known()
            return jsonify({'success': True})

        elif request.method == 'PUT':
            data = request.json
            for e in employees:
                if e['id'] == id:
                    e.update({
                        'name': data['name'],
                        'employee_id': data['employee_id'],
                        'department': data['department'],
                        'designation': data['designation'],
                        'email': data['email']
                    })
                    break
            save_offline_data(employees)
            return jsonify({'success': True})
            
        return jsonify({'error': 'Invalid Method'}), 405

    if request.method == 'DELETE':
        try:
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            # Get image path to delete file
            cur.execute("SELECT image_path FROM employees WHERE id = %s", (id,))
            emp = cur.fetchone()
            
            if emp and emp['image_path'] and os.path.exists(emp['image_path']):
                os.remove(emp['image_path'])
            
            cur.execute("DELETE FROM employees WHERE id = %s", (id,))
            conn.commit()
            conn.close()
            build_known()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        data = request.json
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE employees 
                SET name=%s, employee_id=%s, department=%s, designation=%s, email=%s
                WHERE id=%s
            """, (data['name'], data['employee_id'], data['department'], data['designation'], data['email'], id))
            conn.commit()
            conn.close()
            # Note: If name/ID changes, we might need to rename the file to keep consistency, 
            # but for now we'll leave the file as is to avoid complexity. 
            # A full re-enrollment (delete + add) is better for name changes.
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/daily', methods=['GET'])
def daily_attendance():
    from datetime import timedelta
    
    filter_type = request.args.get('filter', 'today') # today, month, yesterday, last_7_days, last_30_days, last_month, custom
    status_filter = request.args.get('status', 'All') # All, Present, Late, Absent
    start_date_str = request.args.get('start_date')  # For custom date range (YYYY-MM-DD)
    end_date_str = request.args.get('end_date')      # For custom date range (YYYY-MM-DD)

    if not DB_ONLINE:
        # Offline Mode (Simplified: returns all records for today, ignoring filters for now)
        att_records = load_offline_attendance()
        employees = load_offline_data()
        today_str = str(date.today())
        todays_records = [r for r in att_records if r['date'] == today_str]
        
        result = []
        for r in todays_records:
            emp = next((e for e in employees if e['id'] == r['employee_id']), None)
            if emp:
                r_copy = r.copy()
                r_copy['name'] = emp['name']
                r_copy['department'] = emp['department']
                r_copy['image_path'] = emp['image_path']
                
                try:
                    fmt = "%H:%M:%S"
                    t1 = datetime.strptime(r['first_in'], fmt)
                    t2 = datetime.strptime(r['last_seen'], fmt)
                    duration = (t2 - t1).total_seconds()
                    work_sec = r.get('total_work_seconds', 0)
                    if work_sec == 0: work_sec = duration
                    break_sec = max(0, duration - work_sec)
                except:
                    work_sec = 0
                    break_sec = 0
                
                def fmt_sec(s):
                    h = int(s // 3600)
                    m = int((s % 3600) // 60)
                    return f"{h}h {m}m"
                
                r_copy['work_hours'] = fmt_sec(work_sec)
                r_copy['break_hours'] = fmt_sec(break_sec)
                result.append(r_copy)
        return jsonify(result)
        
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Base Query
        query = """
            SELECT a.*, e.name, e.department, e.image_path, e.employee_id as custom_id
            FROM attendance a 
            JOIN employees e ON a.employee_id = e.id 
            WHERE 1=1
        """
        params = []
        
        today = date.today()
        
        # Date Filter - Enhanced with more options
        if filter_type == 'today':
            query += " AND a.date = %s"
            params.append(today)
        elif filter_type == 'yesterday':
            yesterday = today - timedelta(days=1)
            query += " AND a.date = %s"
            params.append(yesterday)
        elif filter_type == 'last_7_days':
            start = today - timedelta(days=6)
            query += " AND a.date BETWEEN %s AND %s"
            params.append(start)
            params.append(today)
        elif filter_type == 'last_30_days':
            start = today - timedelta(days=29)
            query += " AND a.date BETWEEN %s AND %s"
            params.append(start)
            params.append(today)
        elif filter_type == 'this_month':
            query += " AND MONTH(a.date) = %s AND YEAR(a.date) = %s"
            params.append(today.month)
            params.append(today.year)
        elif filter_type == 'last_month':
            # Calculate last month
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            query += " AND a.date BETWEEN %s AND %s"
            params.append(last_month_start)
            params.append(last_month_end)
        elif filter_type == 'custom' and start_date_str and end_date_str:
            # Custom date range
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query += " AND a.date BETWEEN %s AND %s"
                params.append(start_date)
                params.append(end_date)
            except ValueError:
                print(f"[WARN] Invalid date format: {start_date_str} or {end_date_str}")
                # Fallback to today
                query += " AND a.date = %s"
                params.append(today)
        elif filter_type == 'month':
            # Backward compatibility
            query += " AND MONTH(a.date) = %s AND YEAR(a.date) = %s"
            params.append(today.month)
            params.append(today.year)
            
        # Status Filter (Present/Late) - "Absent" is handled separately
        if status_filter in ['Present', 'Late']:
            query += " AND a.status = %s"
            params.append(status_filter)
            
        query += " ORDER BY a.date DESC, a.first_in DESC"
        
        cur.execute(query, tuple(params))
        records = cur.fetchall()
        
        # Handle "Absent" Filter (Only for Today)
        if status_filter == 'Absent' and filter_type == 'today':
            # Get all employees
            cur.execute("SELECT id, name, department, image_path, employee_id as custom_id FROM employees")
            all_emps = cur.fetchall()
            
            # Get IDs present today (from the attendance table)
            cur.execute("SELECT employee_id FROM attendance WHERE date = %s", (today,))
            present_recs = cur.fetchall()
            present_ids = [r['employee_id'] for r in present_recs]
            
            absent_records = []
            for emp in all_emps:
                if emp['id'] not in present_ids:
                    absent_records.append({
                        'name': emp['name'],
                        'department': emp['department'],
                        'image_path': emp['image_path'],
                        'custom_id': emp['custom_id'],
                        'date': str(today),
                        'first_in': '-',
                        'last_seen': '-',
                        'work_hours': '0h 0m',
                        'break_hours': '0h 0m',
                        'status': 'Absent'
                    })
            records = absent_records
            
        conn.close()
        
        # Format Results
        result = []
        for r in records:
            if r.get('status') == 'Absent':
                result.append(r)
                continue
                
            # Format Times
            if r.get('first_in'): r['first_in'] = str(r['first_in'])
            if r.get('last_seen'): r['last_seen'] = str(r['last_seen'])
            if r.get('date'): r['date'] = str(r['date'])
            
            # Calculate Work/Break
            work_sec = r.get('total_work_seconds', 0)
            
            # Calculate Duration (First In to Last Seen)
            duration = 0
            try:
                fmt = "%H:%M:%S"
                # Handle timedelta if needed
                def to_time_str(val):
                    if isinstance(val, (timedelta)):
                        return (datetime.min + val).time().strftime(fmt)
                    return str(val)

                t1 = datetime.strptime(to_time_str(r['first_in']), fmt)
                t2 = datetime.strptime(to_time_str(r['last_seen']), fmt)
                duration = (t2 - t1).total_seconds()
            except: 
                pass
            
            if work_sec == 0 and duration > 0: 
                work_sec = duration
            
            break_sec = max(0, duration - work_sec)
            
            def fmt_sec(s):
                h = int(s // 3600)
                m = int((s % 3600) // 60)
                return f"{h}h {m}m"
            
            r['work_hours'] = fmt_sec(work_sec)
            r['break_hours'] = fmt_sec(break_sec)
            result.append(r)
            
        return jsonify(result)
    except Exception as e:
        print(f"Error in daily_attendance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    if not DB_ONLINE:
        # Offline Stats
        employees = load_offline_data()
        att_records = load_offline_attendance()
        today_str = str(date.today())
        
        total_employees = len(employees)
        todays_records = [r for r in att_records if r['date'] == today_str]
        present_today = len(set(r['employee_id'] for r in todays_records))
        
        # Recent Activity
        # Sort by first_in desc
        sorted_recs = sorted(todays_records, key=lambda x: x['first_in'], reverse=True)[:5]
        recent = []
        for r in sorted_recs:
            emp = next((e for e in employees if e['id'] == r['employee_id']), None)
            if emp:
                recent.append({
                    'check_in_time': r['first_in'],
                    'name': emp['name'],
                    'employee_id': emp['employee_id']
                })

        return jsonify({
            'total_employees': total_employees,
            'present_today': present_today,
            'absent': total_employees - present_today,
            'recent_activity': recent
        })

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Total Employees
        cur.execute("SELECT COUNT(*) as count FROM employees")
        total_employees = cur.fetchone()['count']
        
        # Present Today
        today = date.today()
        cur.execute("SELECT COUNT(DISTINCT employee_id) as count FROM attendance WHERE date = %s", (today,))
        present_today = cur.fetchone()['count']
        
        # Recent Activity (Using first_in)
        cur.execute("""
            SELECT a.first_in as check_in_time, e.name, e.employee_id 
            FROM attendance a 
            JOIN employees e ON a.employee_id = e.id 
            WHERE a.date = %s 
            ORDER BY a.first_in DESC 
            LIMIT 5
        """, (today,))
        recent = cur.fetchall()
        
        conn.close()
        
        for r in recent:
            if r['check_in_time']: r['check_in_time'] = str(r['check_in_time'])

        return jsonify({
            'total_employees': total_employees,
            'present_today': present_today,
            'absent': total_employees - present_today,
            'recent_activity': recent
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras', methods=['GET', 'POST'])
def handle_cameras():
    global CAMERAS
    if request.method == 'POST':
        try:
            new_config = request.json
            # Validate
            if not isinstance(new_config, list):
                return jsonify({"error": "Invalid format"}), 400
            
            CAMERAS = new_config
            save_cameras(CAMERAS)
            return jsonify({"status": "updated", "cameras": CAMERAS})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify(CAMERAS)

@app.route('/latest')
def latest_json():
    # Return latest activity (simplified for now)
    return jsonify({})

def generate(camera_id):
    while True:
        if camera_id in camera_locks:
            with camera_locks[camera_id]:
                frame = camera_frames.get(camera_id)
                if frame is None:
                    # Yield a placeholder frame
                    blank = np.zeros((480, 640, 3), np.uint8)
                    cv2.putText(blank, "CONNECTING...", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    (flag, encodedImage) = cv2.imencode(".jpg", blank)
                    if not flag: continue
                else:
                    (flag, encodedImage) = cv2.imencode(".jpg", frame)
                    if not flag: continue

            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                bytearray(encodedImage) + b'\r\n')
            
            if frame is None:
                time.sleep(0.5)
            else:
                time.sleep(0.03) # ~30 FPS
        else:
            time.sleep(1)

@app.route("/video_feed/<int:camera_id>")
def video_feed(camera_id):
    return Flask.response_class(generate(camera_id),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    full_path = os.path.join(app.static_folder, path)
    print(f"[INFO] Request: {path} | Looking for: {full_path}")
    
    if path != "" and os.path.exists(full_path):
        print(f"   -> Found file: {path}")
        return send_from_directory(app.static_folder, path)
    else:
        print(f"   -> Not found, serving index.html")
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    images_dir = os.path.join(DATA_DIR, 'images')
    return send_from_directory(images_dir, filename)

# -------------- Recognition Logic --------------

# --- Advanced Attendance Logic ---
OFFICE_START_TIME = "09:00:00"

def mark_attendance(employee_id, name):
    today = date.today()
    now = datetime.now()
    now_time = now.time()
    now_time_str = now.strftime("%H:%M:%S")
    today_str = str(today)
    
    print(f"[ATTENDANCE] Attempting to mark attendance for {name} (ID: {employee_id}) at {now_time_str}")

    if not DB_ONLINE:
        # Offline Attendance
        print(f"[ATTENDANCE] Running in OFFLINE mode")
        att_records = load_offline_attendance()
        
        # Find existing record for today
        existing = next((r for r in att_records if r['employee_id'] == employee_id and r['date'] == today_str), None)
        
        if not existing:
            # First Entry
            status = 'Present'
            if str(now_time) > OFFICE_START_TIME:
                status = 'Late'
            
            new_record = {
                'id': len(att_records) + 1, # Simple ID generation
                'employee_id': employee_id,
                'date': today_str,
                'first_in': now_time_str,
                'last_seen': now_time_str,
                'total_work_seconds': 0,
                'status': status
            }
            att_records.append(new_record)
            print(f"[OK] First Entry (Offline): {name} ({status}) at {now_time_str}")
            save_offline_attendance(att_records)
        else:
            # Update Existing
            last_seen_str = existing['last_seen']
            try:
                last_dt = datetime.combine(today, datetime.strptime(last_seen_str, "%H:%M:%S").time())
                diff_seconds = (now - last_dt).total_seconds()
                
                added_work = 0
                if diff_seconds < 300:
                    added_work = diff_seconds
                
                existing['last_seen'] = now_time_str
                existing['total_work_seconds'] += added_work
                save_offline_attendance(att_records)
                print(f"[UPDATE] Updated (Offline): {name} - Last seen: {now_time_str}, Work added: {int(added_work)}s")
            except Exception as e:
                print(f"[WARN] Offline update error: {e}")
        return

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        today = date.today()
        now = datetime.now()
        now_time = now.time()
        
        # 1. Resolve PK from Custom ID
        print(f"[ATTENDANCE] Looking up employee with custom ID: {employee_id}")
        cur.execute("SELECT id FROM employees WHERE employee_id = %s", (str(employee_id),))
        emp_row = cur.fetchone()
        
        if not emp_row:
            print(f"[ERROR] Employee {name} (ID: {employee_id}) not found in DB!")
            conn.close()
            return
            
        emp_pk = emp_row['id']
        print(f"[ATTENDANCE] Found employee PK: {emp_pk}")
        
        # 2. Check for existing record using PK
        cur.execute("SELECT * FROM attendance WHERE employee_id = %s AND date = %s", (emp_pk, today))
        existing = cur.fetchone()
        
        if not existing:
            # First Entry
            status = 'Present'
            # Simple string comparison for time (HH:MM:SS) works for 24h format
            if str(now_time) > OFFICE_START_TIME:
                status = 'Late'
            
            cur.execute("""
                INSERT INTO attendance (employee_id, date, first_in, last_seen, total_work_seconds, status)
                VALUES (%s, %s, %s, %s, 0, %s)
            """, (emp_pk, today, now_time, now_time, status))
            conn.commit()
            print(f"[OK] First Entry: {name} ({status}) at {now_time_str}")
            
        else:
            # Update Existing
            last_seen_time = existing['last_seen'] # timedelta or time object
            
            # Convert to datetime for diff
            # Note: last_seen from DB might be timedelta if using mysql-connector with TIME column
            if isinstance(last_seen_time, (datetime, date)):
                last_dt = datetime.combine(today, last_seen_time.time())
            elif isinstance(last_seen_time, (str)):
                 last_dt = datetime.combine(today, datetime.strptime(last_seen_time, "%H:%M:%S").time())
            else:
                # Handle timedelta (common in mysql connector for TIME fields)
                seconds = last_seen_time.total_seconds()
                last_dt = datetime.combine(today, datetime.min.time()) + last_seen_time
            
            diff_seconds = (now - last_dt).total_seconds()
            
            # Threshold: 5 minutes (300 seconds)
            # If seen within 5 mins, assume they were working continuously.
            # If > 5 mins, assume they were on break/away, so don't add that gap to work time.
            added_work = 0
            if diff_seconds < 300:
                added_work = diff_seconds
            
            cur.execute("""
                UPDATE attendance 
                SET last_seen = %s, 
                    total_work_seconds = total_work_seconds + %s
                WHERE id = %s
            """, (now_time, added_work, existing['id']))
            conn.commit()
            print(f"[UPDATE] Updated: {name} - Last seen: {now_time_str}, Work added: {int(added_work)}s")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        import traceback
        traceback.print_exc()

def start_camera_thread(cam_config):
    cam_id = cam_config['id']
    source = cam_config['source']
    name = cam_config['name']
    
    print(f"[INFO] Starting Camera {cam_id}: {name} ({source})")
    
    def load_known():
        if not os.path.exists(KNOWN_PATH): return []
        try:
            with open(KNOWN_PATH, 'rb') as f: return pickle.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load known faces: {e}")
            return []

    # Initialize OpenCV DNN Models (Deep Learning)
    DETECTOR_PATH = os.path.join(BASE_DIR, 'models', 'face_detection_yunet_2023mar.onnx')
    RECOGNIZER_PATH = os.path.join(BASE_DIR, 'models', 'face_recognition_sface_2021dec.onnx')
    
    if not os.path.exists(DETECTOR_PATH) or not os.path.exists(RECOGNIZER_PATH):
        print(f"[ERROR] Models not found! Please download YuNet and SFace models to app/models/")
        return

    detector = cv2.FaceDetectorYN.create(DETECTOR_PATH, "", (320, 320), 0.6, 0.3, 5000)
    recognizer = cv2.FaceRecognizerSF.create(RECOGNIZER_PATH, "")

    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"[WARN] Camera {cam_id} not found. Retrying in background...")
    
    known = load_known()
    last_known_mtime = os.path.getmtime(KNOWN_PATH) if os.path.exists(KNOWN_PATH) else 0

    # Hysteresis State
    consecutive_matches = 0
    last_recognized_name = None
    
    # Optimization State
    frame_count = 0
    PROCESS_EVERY_N_FRAMES = 3
    last_processed_faces = None # Stores (faces, names) for display

    while True:
        # --- DYNAMIC CONFIG CHECK ---
        # Check if global config changed for this camera ID
        current_config = next((c for c in CAMERAS if c['id'] == cam_id), None)
        if current_config:
            new_source = current_config['source']
            if new_source != source:
                print(f"[INFO] Camera {cam_id} source changed: {source} -> {new_source}")
                source = new_source
                cap.release()
                cap = cv2.VideoCapture(source)
                if isinstance(source, str) and source.startswith('http'):
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Reconnect if needed
        if not cap.isOpened():
            cap.open(source)
            if not cap.isOpened():
                time.sleep(5)
                continue
            else:
                print(f"[OK] Camera {cam_id} connected.")
                if isinstance(source, str) and source.startswith('http'):
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Hot-Reload Known Faces
        if os.path.exists(KNOWN_PATH):
            mtime = os.path.getmtime(KNOWN_PATH)
            if mtime > last_known_mtime:
                print("[INFO] Reloading known faces...")
                known = load_known()
                last_known_mtime = mtime

        ret, frame = cap.read()
        if not ret:
            time.sleep(0.5)
            continue
        
        # Resize for Display/Processing (Standardize)
        # If frame is huge (e.g. 1080p), resize to 640x480 for speed
        h, w, _ = frame.shape
        if w > 800:
            frame = cv2.resize(frame, (800, 600))
            h, w, _ = frame.shape

        frame_count += 1
        
        # --- FRAME SKIPPING LOGIC ---
        if frame_count % PROCESS_EVERY_N_FRAMES != 0 and last_processed_faces is not None:
            # Skip processing, just draw last results
            faces, recognized_names = last_processed_faces
        else:
            # Process this frame
            detector.setInputSize((w, h))
            faces = detector.detect(frame)
            recognized_names = []
            
            if faces[1] is not None:
                for face in faces[1]:
                    # Face Coords
                    coords = face[:-1].astype(np.int32)
                    x, y, w_box, h_box = coords[0], coords[1], coords[2], coords[3]
                    
                    # Align & Recognize (SFace)
                    face_align = recognizer.alignCrop(frame, face)
                    face_feature = recognizer.feature(face_align)
                    
                    # Compare with Known Faces
                    min_score = 1.0 # Cosine Distance
                    best_name = "Unknown"
                    best_id = None
                    
                    if len(known) > 0:
                        for person in known:
                            score = recognizer.match(face_feature, person['feature'], cv2.FaceRecognizerSF_FR_COSINE)
                            if score < min_score:
                                min_score = score
                                temp_name = person['name']
                                temp_id = person.get('id')
                                
                                # Fallback: Extract ID from name (Format: ID_Name)
                                if not temp_id and '_' in temp_name:
                                    try:
                                        parts = temp_name.split('_')
                                        temp_id = parts[0]
                                        # Optional: You might want to strip the ID from the display name
                                        # temp_name = parts[1] 
                                    except:
                                        pass

                                best_name = temp_name
                                best_id = temp_id
                    
                    # Threshold logic
                    # SFace threshold: 0.363 is strict. 0.7 is lenient/standard for unconstrained env.
                    is_match = False
                    if min_score < 0.7:
                        # Potential Match
                        if best_name == last_recognized_name:
                            consecutive_matches = min(consecutive_matches + 1, 20)
                        else:
                            consecutive_matches = 0
                            last_recognized_name = best_name
                        
                        if consecutive_matches > 2: # Require 3 consecutive frames
                            is_match = True
                    else:
                        consecutive_matches = max(0, consecutive_matches - 1)
                        if consecutive_matches == 0:
                            last_recognized_name = None

                    # Final Name Decision
                    display_name = best_name if is_match else "Unknown"
                    recognized_names.append((display_name, min_score, best_id, coords))
                    
                    # Mark Attendance
                    if is_match and best_id:
                        mark_attendance(best_id, best_name)
            
            # Update Cache
            last_processed_faces = (faces, recognized_names)

        # --- DRAWING ---
        # Draw results (either fresh or cached)
        if last_processed_faces:
            _, current_names = last_processed_faces
            for name, score, _, coords in current_names:
                x, y, w_box, h_box = coords[0], coords[1], coords[2], coords[3]
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                
                cv2.rectangle(frame, (x, y), (x+w_box, y+h_box), color, 2)
                
                label = f"{name} ({score:.2f})"
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Update global frame
        with camera_locks[cam_id]:
            camera_frames[cam_id] = frame.copy()


        # Update Global Frame
        with camera_locks[cam_id]:
            camera_frames[cam_id] = frame.copy()

if __name__ == '__main__':
    # Start threads for each camera
    for cam in CAMERAS:
        t = threading.Thread(target=start_camera_thread, args=(cam,))
        t.daemon = True
        t.start()
        
    print("Checking Database Connection...")
    check_db_connection()
    print("Server starting on http://localhost:5001 ...")
    app.run(debug=True, port=5001, use_reloader=False)