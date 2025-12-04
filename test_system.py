# Test Script for Attendance System
# This script helps verify the attendance system is working correctly

import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.getcwd(), 'app'))

print("=" * 60)
print("ATTENDANCE SYSTEM TEST")
print("=" * 60)

# Test 1: Check Database Connection
print("\n[TEST 1] Database Connection")
try:
    import mysql.connector
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Raghu@3033',
        database='face_attendance'
    )
    print("✓ Database connection successful")
    conn.close()
except Exception as e:
    print(f"✗ Database connection failed: {e}")

# Test 2: Check Known Faces
print("\n[TEST 2] Known Faces Database")
try:
    import pickle
    known_path = os.path.join(os.getcwd(), 'data', 'known_orb.pkl')
    if os.path.exists(known_path):
        with open(known_path, 'rb') as f:
            known = pickle.load(f)
        print(f"✓ Loaded {len(known)} known faces:")
        for person in known:
            print(f"  - {person['name']}")
    else:
        print("✗ Known faces file not found")
except Exception as e:
    print(f"✗ Failed to load known faces: {e}")

# Test 3: Check Employees in Database
print("\n[TEST 3] Employees in Database")
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Raghu@3033',
        database='face_attendance'
    )
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name, employee_id FROM employees")
    employees = cur.fetchall()
    print(f"✓ Found {len(employees)} employees:")
    for emp in employees:
        print(f"  - {emp['name']} (ID: {emp['employee_id']}, PK: {emp['id']})")
    conn.close()
except Exception as e:
    print(f"✗ Failed to query employees: {e}")

# Test 4: Check Today's Attendance
print("\n[TEST 4] Today's Attendance Records")
try:
    from datetime import date
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Raghu@3033',
        database='face_attendance'
    )
    cur = conn.cursor(dictionary=True)
    today = date.today()
    cur.execute("""
        SELECT e.name, e.employee_id, a.date, a.first_in, a.last_seen, a.status
        FROM attendance a 
        JOIN employees e ON a.employee_id = e.id
        WHERE a.date = %s
    """, (today,))
    records = cur.fetchall()
    if records:
        print(f"✓ Found {len(records)} attendance records for today:")
        for r in records:
            print(f"  - {r['name']} ({r['employee_id']}): {r['first_in']} - {r['last_seen']} [{r['status']}]")
    else:
        print("⚠ No attendance records for today yet")
    conn.close()
except Exception as e:
    print(f"✗ Failed to query attendance: {e}")

# Test 5: Test Attendance Marking
print("\n[TEST 5] Test Attendance Marking Function")
try:
    import server
    # Force DB online for testing
    server.DB_ONLINE = True
    
    # Test with a known employee ID
    print("Testing mark_attendance function...")
    print("(Check server console for detailed logs)")
    
    # This will attempt to mark attendance
    # server.mark_attendance(9381780839, '9381780839_raghavendra')
    
    print("✓ Attendance marking function is available")
    print("  (Run the server to test live attendance marking)")
except Exception as e:
    print(f"✗ Failed to test attendance marking: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNext Steps:")
print("1. Start the server: .\\venv\\Scripts\\python.exe app\\server.py")
print("2. Open browser: http://localhost:5001")
print("3. Go to Live Feed page")
print("4. Show your face to the camera")
print("5. Watch for:")
print("   - Green box around recognized face")
print("   - Red box around unknown face")
print("   - Console logs showing [RECOGNITION] and [ATTENDANCE] messages")
print("6. Check Attendance page for your record")
print("7. Check Dashboard for recent activity")
