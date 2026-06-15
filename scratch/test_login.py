import urllib.request
import json

url = 'http://localhost:8000/api/v1/auth/login'
data = json.dumps({'username': 'comando', 'password': 'comando123'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print('Error:', str(e))
    if hasattr(e, 'read'):
        print(e.read().decode())
