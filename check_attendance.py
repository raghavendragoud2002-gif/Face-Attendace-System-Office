import mysql.connector
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
print(f'Attendance Records for Today ({today}):')
if records:
    for r in records:
        print(f"  - {r['name']} ({r['employee_id']}): {r['first_in']} - {r['last_seen']} [{r['status']}]")
else:
    print('  No attendance records for today yet.')

conn.close()
