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

# local helpers (enroll_orb.py)
from enroll_orb import build_known, IMAGES_DIR, KNOWN_PATH

# ---------- CONFIG ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': "Raghu@3033",
    'database': 'face_attendance'
}
# Camera Configuration
CAMERAS = [
    {'id': 0, 'source': 0, 'name': 'Main Entrance (Webcam)'},
    {'id': 1, 'source': 'http://10.122.3.222:8080/video', 'name': 'Office Area (Wireless)'}
]
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
        f = request.files.get('file')
        
        if not f or not name or not emp_id:
            return jsonify({'error': 'Missing required fields'}), 400
            
        safe_name = name.strip().replace(' ', '_')
        ext = os.path.splitext(f.filename)[1] or '.jpg'
        filename = f"{emp_id}_{safe_name}{ext}"
        save_path = os.path.join(DATA_DIR, 'images', filename)
        f.save(save_path)
        
        try:
            if DB_ONLINE:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO employees (name, employee_id, department, designation, email, image_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, emp_id, dept, desig, email, save_path))
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
                    'image_path': save_path,
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

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
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
                    time.sleep(0.1)
                    continue
                
                (flag, encodedImage) = cv2.imencode(".jpg", frame)
                if not flag:
                    continue
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                bytearray(encodedImage) + b'\r\n')
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
        with open(KNOWN_PATH, 'rb') as f: return pickle.load(f)

    mp_face = mp.solutions.face_detection
    orb = cv2.ORB_create(1000)
    # CRITICAL FIX: crossCheck must be False for knnMatch
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    cap = cv2.VideoCapture(source)
    
    # Retry logic for IP cameras
    if not cap.isOpened():
        print(f"[WARN] Camera {cam_id} not found. Retrying in background...")
    
    known = load_known()
    last_known_mtime = os.path.getmtime(KNOWN_PATH) if os.path.exists(KNOWN_PATH) else 0
    last_seen = {} 
    last_recognized = {} # For per-person hysteresis

    with mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6) as detector:
        while True:
            # Reconnect if needed
            if not cap.isOpened():
                cap.open(source)
                if not cap.isOpened():
                    time.sleep(5)
                    continue
                else:
                    print(f"[OK] Camera {cam_id} connected.")

            # Hot-Reload Known Faces
            if os.path.exists(KNOWN_PATH):
                mtime = os.path.getmtime(KNOWN_PATH)
                if mtime > last_known_mtime:
                    known = load_known()
                    last_known_mtime = mtime

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.5)
                continue
            
            # --- Face Recognition Logic ---
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)
            
            if results.detections:
                for detection in results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                                 int(bboxC.width * iw), int(bboxC.height * ih)
                    
                    # Ensure valid coordinates
                    x, y = max(0, x), max(0, y)
                    w, h = min(w, iw - x), min(h, ih - y)
                    
                    # Recognize FIRST, then draw box with appropriate color
                    face_roi = frame[y:y+h, x:x+w]
                    if face_roi.size == 0: 
                        continue
                    
                    label = "Unknown"
                    color = (0, 0, 255)  # Red for unknown
                    recognized = False
                    
                    try:
                        kp, des = orb.detectAndCompute(face_roi, None)
                        if des is not None and len(known) > 0:
                            best_name = "Unknown"
                            best_score = 0
                            second_best_score = 0
                            best_person = None
                            
                            for person in known:
                                try:
                                    # Handle both 'desc' (new) and 'des' (old) keys for compatibility
                                    person_des = person.get('desc')
                                    if person_des is None:
                                        person_des = person.get('des')
                                        
                                    if person_des is None:
                                        print(f"[WARN] No descriptors found for {person.get('name')}")
                                        continue

                                    matches = bf.knnMatch(des, person_des, k=2)
                                    good = []
                                    for pair in matches:
                                        if len(pair) == 2:
                                            m, n = pair
                                            if m.distance < 0.75 * n.distance:
                                                good.append(m)
                                    
                                    # Debug: Show score for each person
                                    print(f"[DEBUG] Comparing with {person['name']}: {len(good)} good matches")
                                    
                                    # Find best match
                                    if len(good) > best_score:
                                        # If we already had a best score, that becomes the runner-up
                                        second_best_score = best_score
                                        best_score = len(good)
                                        best_name = person['name']
                                        best_person = person
                                    elif len(good) > second_best_score:
                                        second_best_score = len(good)
                                        
                                except Exception as e:
                                    print(f"[WARN] Matching error for {person.get('name', 'unknown')}: {e}")
                                    continue
                    
                            # Threshold for recognition
                            # Lowered to 2 because 3 was too strict for this camera/lighting
                            # Consecutive match check lowered to 2 frames
                            
                            is_match = False
                            if best_score >= 2:
                                if best_score > second_best_score:
                                    # Potential match found
                                    # Check if it's the same person as last frame
                                    if best_name == last_recognized_name:
                                        consecutive_matches += 1
                                    else:
                                        consecutive_matches = 1
                                        last_recognized_name = best_name
                                    
                                    print(f"[DEBUG] Potential: {best_name} ({best_score}), Consecutive: {consecutive_matches}")
                                    
                                    # REQUIRE 2 CONSECUTIVE FRAMES to confirm match
                                    if consecutive_matches >= 2:
                                        is_match = True
                                else:
                                    # Ambiguous
                                    consecutive_matches = 0
                                    last_recognized_name = None
                                    print(f"[DEBUG] Ambiguous: {best_score} vs {second_best_score}")
                            else:
                                # No good match
                                consecutive_matches = 0
                                last_recognized_name = None
                                print(f"[DEBUG] No match: Best score {best_score} < 3")
                                    
                            if is_match:
                                label = best_name
                                color = (0, 255, 0)  # Green for recognized
                                recognized = True
                                
                                # Mark Attendance
                                try:
                                    # Extract employee ID from filename (format: ID_Name or ID_Name_Name)
                                    parts = best_name.split('_')
                                    if len(parts) >= 1:
                                        emp_id_str = parts[0]
                                        # Verify it's a valid number
                                        if emp_id_str.isdigit():
                                            emp_id = int(emp_id_str)
                                            
                                            # Check throttle to avoid spamming
                                            current_time = time.time()
                                            last_time = last_seen.get(emp_id, 0)
                                            
                                            if current_time - last_time > ATTENDANCE_THROTTLE_SECONDS:
                                                print(f"[RECOGNITION] Recognized: {best_name} (ID: {emp_id}) - Score: {best_score}")
                                                mark_attendance(emp_id, best_name)
                                                last_seen[emp_id] = current_time
                                            # else: silently skip (within throttle period)
                                        else:
                                            print(f"[WARN] Invalid employee ID format in filename: {best_name}")
                                    else:
                                        print(f"[WARN] Cannot extract employee ID from filename: {best_name}")
                                except Exception as e:
                                    print(f"[ERROR] Attendance marking failed for {best_name}: {e}")
                                    import traceback
                                    traceback.print_exc()
                            else:
                                label = "Unknown"
                                color = (0, 0, 255)  # Red for unknown
                    
                    except Exception as e:
                        print(f"[ERROR] Recognition error: {e}")
                        pass
                    
                    # Draw box AFTER recognition with correct color
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    
                    # Draw label with background for better visibility
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (x, y - label_size[1] - 10), (x + label_size[0], y), color, -1)
                    cv2.putText(frame, label, (x, y - 5), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

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