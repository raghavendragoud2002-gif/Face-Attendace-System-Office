"""
Script to migrate JSON data to MySQL database
Run this to import your offline data into MySQL for demo purposes
"""
import sys
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import mysql.connector
from datetime import datetime

# Database configuration - UPDATE THIS WITH YOUR MYSQL PASSWORD
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Raghu@3033',  # UPDATE THIS!
    'database': 'face_attendance'
}

def migrate_data():
    print("Starting data migration to MySQL...")
    
    # Connect to MySQL
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ Connected to MySQL")
    except Exception as e:
        print(f"✗ Failed to connect to MySQL: {e}")
        print("\nPlease update the password in this script and ensure MySQL is running!")
        return
    
    # Load JSON data
    try:
        with open('data/employees.json', 'r') as f:
            employees = json.load(f)
        print(f"✓ Loaded {len(employees)} employees from JSON")
    except Exception as e:
        print(f"✗ Failed to load employees.json: {e}")
        employees = []
    
    try:
        with open('data/attendance.json', 'r') as f:
            attendance = json.load(f)
        print(f"✓ Loaded {len(attendance)} attendance records from JSON")
    except Exception as e:
        print(f"✗ Failed to load attendance.json: {e}")
        attendance = []
    
    # Clear existing data
    print("\nClearing existing data...")
    cursor.execute("DELETE FROM attendance")
    cursor.execute("DELETE FROM employees")
    conn.commit()
    print("✓ Cleared existing data")
    
    # Migrate employees
    print("\nMigrating employees...")
    employee_id_map = {}  # Map JSON id to MySQL id
    
    for emp in employees:
        try:
            cursor.execute("""
                INSERT INTO employees (name, employee_id, department, designation, email, image_path, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                emp['name'],
                emp['employee_id'],
                emp.get('department', ''),
                emp.get('designation', ''),
                emp.get('email', ''),
                emp.get('image_path', ''),
                emp.get('created_at', datetime.now())
            ))
            
            # Store the mapping of JSON id to MySQL id
            employee_id_map[emp['id']] = cursor.lastrowid
            print(f"  ✓ Migrated: {emp['name']} (ID: {emp['employee_id']})")
            
        except Exception as e:
            print(f"  ✗ Failed to migrate {emp.get('name', 'Unknown')}: {e}")
    
    conn.commit()
    print(f"✓ Migrated {len(employee_id_map)} employees")
    
    # Migrate attendance
    print("\nMigrating attendance records...")
    migrated_count = 0
    
    for att in attendance:
        try:
            # Get the MySQL employee_id from our mapping
            mysql_emp_id = employee_id_map.get(att['employee_id'])
            
            if not mysql_emp_id:
                print(f"  ⚠ Skipping attendance for unknown employee ID: {att['employee_id']}")
                continue
            
            cursor.execute("""
                INSERT INTO attendance (employee_id, date, first_in, last_seen, total_work_seconds, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                mysql_emp_id,
                att['date'],
                att['first_in'],
                att['last_seen'],
                att.get('total_work_seconds', 0),
                att.get('status', 'Present')
            ))
            migrated_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to migrate attendance record: {e}")
    
    conn.commit()
    print(f"✓ Migrated {migrated_count} attendance records")
    
    # Show summary
    print("\n" + "="*50)
    print("MIGRATION COMPLETE!")
    print("="*50)
    
    cursor.execute("SELECT COUNT(*) FROM employees")
    emp_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM attendance")
    att_count = cursor.fetchone()[0]
    
    print(f"Total Employees in MySQL: {emp_count}")
    print(f"Total Attendance Records in MySQL: {att_count}")
    print("\nYou can now view this data in MySQL Workbench!")
    print("\nQueries to run in Workbench:")
    print("  SELECT * FROM employees;")
    print("  SELECT * FROM attendance;")
    print("  SELECT e.name, e.employee_id, a.date, a.first_in, a.last_seen, a.status")
    print("  FROM attendance a JOIN employees e ON a.employee_id = e.id;")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    migrate_data()
