import requests
import os

url = 'http://localhost:5001/api/employees'
files = {'file': open('dummy.jpg', 'rb')}
data = {
    'name': 'API Test User',
    'employee_id': 'API001',
    'department': 'Engineering',
    'designation': 'Developer',
    'email': 'api@test.com'
}

try:
    response = requests.post(url, data=data, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
