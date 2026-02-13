from flask import Flask, request, redirect, render_template_string
from collections import deque
import time

app = Flask(__name__)

queues = {
    "A": deque(),
    "B": deque(),
    "C": deque()
}

running = {}

HTML = """
<!doctype html>
<title>LAN Task Server</title>
<h2>📤 Add Task</h2>

<form method="post" action="/add">
  Task ID:<br>
  <input name="id" required><br><br>

  Command:<br>
  <input name="command" size="80" required><br><br>

  Worker:<br>
  <select name="worker">
    <option>A</option>
    <option>B</option>
    <option>C</option>
  </select><br><br>

  Loop:
  <input type="checkbox" name="loop"><br><br>

  Delay (seconds):
  <input name="delay" value="0"><br><br>

  <button type="submit">Add Task</button>
</form>

<hr>

<h2>📋 Queues</h2>
{% for w, q in queues.items() %}
<h3>Worker {{w}}</h3>
<ul>
  {% for t in q %}
    <li>{{t["id"]}} → {{t["command"]}}</li>
  {% endfor %}
</ul>
{% endfor %}

<hr>

<h2>⚙️ Running</h2>
<ul>
{% for t in running.values() %}
  <li>{{t["id"]}} ({{t["worker"]}})</li>
{% endfor %}
</ul>
"""

@app.route("/")
def index():
    return render_template_string(HTML, queues=queues, running=running)

@app.route("/add", methods=["POST"])
def add():
    task = {
        "id": request.form["id"],
        "command": request.form["command"],
        "worker": request.form["worker"],
        "loop": "loop" in request.form,
        "delay": int(request.form["delay"] or 0)
    }
    queues[task["worker"]].append(task)
    return redirect("/")

@app.route("/task/<worker>")
def get_task(worker):
    if not queues[worker]:
        return {}
    task = queues[worker].popleft()
    running[task["id"]] = task
    return task

@app.route("/done", methods=["POST"])
def done():
    data = request.json
    task = running.pop(data["id"], None)

    if task and task.get("loop"):
        time.sleep(task["delay"])
        queues[task["worker"]].append(task)

    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
