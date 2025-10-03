import urllib.request
import urllib.error

try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/simple-test/')
    print(f"Status Code: {response.getcode()}")
    print(f"Response: {response.read().decode('utf-8')}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(f"Headers: {dict(e.headers)}")
    try:
        print(f"Body: {e.read().decode('utf-8')}")
    except:
        print("Could not read error body")
except Exception as e:
    print(f"Error: {e}")