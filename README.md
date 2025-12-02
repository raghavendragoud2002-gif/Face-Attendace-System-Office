# Face Attendance System - Cloud Harbor Technologies

A modern, AI-powered face recognition attendance system with multi-camera support, real-time monitoring, and comprehensive reporting.

![Dashboard](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9-blue)
![React](https://img.shields.io/badge/React-18-61dafb)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)

## 🌟 Features

### Core Functionality
- **Face Recognition**: Real-time face detection and recognition using MediaPipe and ORB
- **Multi-Camera Support**: Simultaneous monitoring from multiple cameras (Webcam + IP Camera)
- **Attendance Tracking**: Automatic attendance marking with first-in, last-seen, work hours, and break hours
- **Smart Status Detection**: Automatically marks employees as Present or Late based on entry time

### User Interface
- **Modern Dashboard**: Clean, intuitive interface with real-time statistics
- **Live Surveillance**: Grid view and focus mode for multiple camera feeds
- **Advanced Filtering**: Filter attendance by date (Today/Month) and status (Present/Late/Absent)
- **Employee Management**: Full CRUD operations for employee records
- **Export Functionality**: Download attendance reports as CSV

### Technical Features
- **Offline Mode**: Works without database connection using JSON file storage
- **MySQL Integration**: Production-ready database support
- **Hot-Reload**: Automatic detection of new employee enrollments
- **Responsive Design**: Works on desktop and tablet devices

## 📋 Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher
- MySQL 8.0 or higher
- Webcam (built-in or external)
- IP Webcam app (for wireless camera support)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/raghavendragoud2002-gif/Face-Attendace-System-Office.git
cd Face-Attendace-System-Office
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
python -m venv venv
```

#### Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install flask flask-cors opencv-python mediapipe mysql-connector-python requests
```

### 3. Database Setup

#### Create Database
```bash
mysql -u root -p < schema.sql
```

#### Update Database Credentials
Edit `app/server.py` and update the `DB_CONFIG`:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_PASSWORD',
    'database': 'face_attendance'
}
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run build
cd ..
```

## 🎯 Usage

### Starting the Server

```bash
venv\Scripts\python app/server.py
```

The server will start on `http://localhost:5001`

### Default Login Credentials

- **Username:** `admin`
- **Password:** `admin123`

### Setting Up IP Camera

1. Install "IP Webcam" app on your Android phone
2. Start the server in the app
3. Note the IP address (e.g., `http://192.168.1.5:8080`)
4. Update `app/server.py`:
```python
CAMERAS = [
    {'id': 0, 'source': 0, 'name': 'Main Entrance (Webcam)'},
    {'id': 1, 'source': 'http://YOUR_IP:8080/video', 'name': 'Office Area (Wireless)'}
]
```

## 📊 Features Guide

### Employee Enrollment

1. Navigate to **Employees** page
2. Click **Add Employee**
3. Fill in employee details
4. Capture face image using webcam
5. Click **Save**

### Viewing Attendance

1. Navigate to **Attendance** page
2. Use filters to view:
   - **Date**: Today or This Month
   - **Status**: All, Present, Late, or Absent
3. Click **Export CSV** to download reports

### Live Monitoring

1. Navigate to **Live Feed** page
2. View all cameras in grid view
3. Click on any camera to maximize it
4. Face recognition runs automatically on all cameras

## 🗂️ Project Structure

```
Face-Attendace-System-Office/
├── app/
│   ├── server.py              # Flask backend server
│   ├── known_faces.pkl        # Encoded face data
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── pages/             # React pages
│   │   ├── components/        # React components
│   │   └── ...
│   ├── dist/                  # Production build
│   └── package.json
├── data/
│   ├── images/                # Employee face images
│   ├── employees.json         # Offline employee data
│   └── attendance.json        # Offline attendance data
├── schema.sql                 # Database schema
├── migrate_to_mysql.py        # Data migration script
├── venv/                      # Python virtual environment
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Office Start Time
Edit `app/server.py`:
```python
OFFICE_START_TIME = "09:00:00"  # Change to your office start time
```

### Attendance Throttle
```python
ATTENDANCE_THROTTLE_SECONDS = 60 * 5  # 5 minutes between updates
```

## 📝 API Endpoints

### Authentication
- `POST /api/login` - Admin login

### Employees
- `GET /api/employees` - Get all employees
- `POST /api/employees` - Add new employee
- `PUT /api/employees/<id>` - Update employee
- `DELETE /api/employees/<id>` - Delete employee

### Attendance
- `GET /api/attendance/daily?filter=today&status=All` - Get attendance records
- `GET /api/stats` - Get dashboard statistics

### Camera
- `GET /api/cameras` - Get camera list
- `GET /video_feed/<camera_id>` - Get camera stream

## 🐛 Troubleshooting

### Camera Not Working
- Check camera permissions
- Ensure no other application is using the camera
- For IP camera, verify the IP address and network connection

### Database Connection Failed
- Verify MySQL is running
- Check database credentials in `app/server.py`
- Ensure `face_attendance` database exists

### Attendance Not Recording
- Verify employee is enrolled with face image
- Check if face is clearly visible to camera
- Review server logs for errors

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👥 Credits

Developed by **Cloud Harbor Technologies**

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Note:** This system is designed for office attendance management. Ensure compliance with local privacy laws when deploying face recognition systems.
