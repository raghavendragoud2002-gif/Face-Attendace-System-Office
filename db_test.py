import mysql.connector

config = {
    'host': 'localhost',
    'user': 'root',
    'password': "6303017992Sam_",
    'database': 'face_attendance'
}

print("Attempting to connect to MySQL...")
try:
    conn = mysql.connector.connect(**config)
    print("✅ SUCCESS! Connection established.")
    conn.close()
except mysql.connector.Error as err:
    print(f"❌ FAILED: {err}")
    print("Please verify your password and ensure MySQL is running.")
