import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Raghu@3033',
    database='face_attendance'
)

cur = conn.cursor()
cur.execute('SELECT name, employee_id FROM employees')
print('Enrolled Employees:')
for row in cur.fetchall():
    print(f'  - {row[0]} (ID: {row[1]})')

conn.close()
