import mysql.connector
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': "6303017992Sam_",
    'database': 'face_attendance'
}

def init_db():
    print("🔄 Initializing Database...")
    try:
        # Connect to MySQL Server (without DB first to ensure it exists)
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        # Read schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            
        # Execute statements
        # Split by ';' to handle multiple statements
        statements = schema_sql.split(';')
        for stmt in statements:
            if stmt.strip():
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"⚠️ Warning executing statement: {e}")
                    
        conn.commit()
        print("✅ Database Schema Applied Successfully!")
        conn.close()
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
