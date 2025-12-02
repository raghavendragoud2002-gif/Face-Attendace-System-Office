import sys
import os
import json
from datetime import date

# Add app directory to path
sys.path.append(os.path.join(os.getcwd(), 'app'))

# Mock the database config to ensure offline mode if needed, 
# but server.py defaults DB_ONLINE to False anyway.
import server

# Mock data/employees.json if it doesn't exist or is empty
employees_path = os.path.join(os.getcwd(), 'data', 'employees.json')
if not os.path.exists(employees_path):
    with open(employees_path, 'w') as f:
        json.dump([{'id': 1, 'name': 'Test User', 'employee_id': 'T001'}], f)

# Call mark_attendance
print("Marking attendance for Test User...")
server.mark_attendance(1, 'Test User')

# Check attendance.json
attendance_path = os.path.join(os.getcwd(), 'data', 'attendance.json')
if os.path.exists(attendance_path):
    with open(attendance_path, 'r') as f:
        data = json.load(f)
        print("Attendance Data:", json.dumps(data, indent=2))
        
        # Verify today's record
        today_str = str(date.today())
        record = next((r for r in data if r['date'] == today_str and r['employee_id'] == 1), None)
        if record:
            print("SUCCESS: Attendance record found!")
        else:
            print("FAILURE: No record found for today.")
else:
    print("FAILURE: attendance.json not found.")
