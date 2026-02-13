import requests
import time
import subprocess
import sys

SERVER = "http://192.168.1.10:5000"
WORKER = sys.argv[1]

while True:
    task = requests.get(f"{SERVER}/task/{WORKER}").json()

    if not task:
        time.sleep(2)
        continue

    try:
        subprocess.run(task["command"], shell=True, check=True)
    except Exception as e:
        print(e)

    requests.post(f"{SERVER}/done", json={"id": task["id"]})
