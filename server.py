import sqlite3
import time
from flask import Flask, request, redirect, render_template_string, jsonify

DB = "tasks.db"
app = Flask(__name__)

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    with db() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            worker TEXT,
            command TEXT,
            loop INTEGER,
            delay INTEGER
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS running (
            id TEXT PRIMARY KEY,
            worker TEXT,
            command TEXT,
            loop INTEGER,
            delay INTEGER
        )""")

init_db()

HTML = """
<!doctype html>
<title>LAN Task Server</title>

<h2>Add Task</h2>
<form method="post" action="/add">
ID:<br><input name="id" required><br>
Command:<br><input name="command" size="80" required><br>
Worker:<br>
<select name="worker"><option>A</option><option>B</option><option>C</option></select><br>
Loop <input type="checkbox" name="loop"><br>
Delay <input name="delay" value="0"><br>
<button>Add</button>
</form>

<hr>

<h2>Queued</h2>
{% for w in ["A","B","C"] %}
<h3>{{w}}</h3>
<ul>
{% for t in tasks if t["worker"]==w %}
<li>{{t["id"]}} – {{t["command"]}}</li>
{% endfor %}
</ul>
{% endfor %}

<h2>Running</h2>
<ul>
{% for r in running %}
<li>{{r["id"]}} ({{r["worker"]}})</li>
{% endfor %}
</ul>
"""

@app.route("/")
def index():
    with db() as c:
        tasks = [dict(zip(
            ["id","worker","command","loop","delay"], row
        )) for row in c.execute("SELECT * FROM tasks")]
        running = [dict(zip(
            ["id","worker","command","loop","delay"], row
        )) for row in c.execute("SELECT * FROM running")]

    return render_template_string(HTML, tasks=tasks, running=running)

@app.route("/add", methods=["POST"])
def add():
    with db() as c:
        c.execute(
            "INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?)",
            (
                request.form["id"],
                request.form["worker"],
                request.form["command"],
                1 if "loop" in request.form else 0,
                int(request.form["delay"] or 0)
            )
        )
    return redirect("/")

@app.route("/task/<worker>")
def get_task(worker):
    with db() as c:
        row = c.execute(
            "SELECT * FROM tasks WHERE worker=? LIMIT 1",
            (worker,)
        ).fetchone()

        if not row:
            return jsonify({})

        c.execute("DELETE FROM tasks WHERE id=?", (row[0],))
        c.execute("INSERT INTO running VALUES (?,?,?,?,?)", row)

    return jsonify({
        "id": row[0],
        "worker": row[1],
        "command": row[2],
        "loop": bool(row[3]),
        "delay": row[4]
    })

@app.route("/done", methods=["POST"])
def done():
    tid = request.json["id"]

    with db() as c:
        row = c.execute(
            "SELECT * FROM running WHERE id=?", (tid,)
        ).fetchone()

        c.execute("DELETE FROM running WHERE id=?", (tid,))

        if row and row[3]:  # loop
            time.sleep(row[4])
            c.execute("INSERT INTO tasks VALUES (?,?,?,?,?)", row)

    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
