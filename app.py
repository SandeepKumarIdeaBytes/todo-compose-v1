
import os
import time
from flask import Flask, request, redirect, render_template_string
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "user": os.getenv("DB_USER", "todo_user"),
    "password": os.getenv("DB_PASSWORD", "todo_password"),
    "database": os.getenv("DB_NAME", "todo_db"),
}

def get_connection():
    for attempt in range(30):
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error:
            if attempt == 29:
                raise
            time.sleep(2)

def initialize_database():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
    finally:
        conn.close()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>My To-Do App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #eef2f7;
            margin: 0;
            padding: 40px 16px;
        }
        .container {
            max-width: 600px;
            margin: auto;
            background: white;
            padding: 28px;
            border-radius: 12px;
            box-shadow: 0 4px 16px #0001;
        }
        h1 { text-align: center; color: #243b55; }
        form.add { display: flex; gap: 8px; }
        input[name=title] {
            flex: 1; min-width: 0; padding: 12px;
            border: 1px solid #ccd3df; border-radius: 6px;
        }
        button {
            padding: 10px 14px; border: 0;
            border-radius: 6px; cursor: pointer;
        }
        .add button { background: #2563eb; color: white; }
        .task {
            display: flex; align-items: center;
            justify-content: space-between; gap: 12px;
            padding: 14px 0; border-bottom: 1px solid #eee;
        }
        .task-title { overflow-wrap: anywhere; }
        .done { text-decoration: line-through; color: #888; }
        .actions { display: flex; gap: 6px; }
        .complete { background: #dcfce7; }
        .delete { background: #fee2e2; }
        .empty { text-align: center; color: #777; padding: 20px; }
    </style>
</head>
<body>
<div class="container">
    <h1>My To-Do List</h1>
    <form class="add" action="/add" method="POST">
        <input name="title" placeholder="Enter a new task..." required maxlength="255">
        <button type="submit">Add Task</button>
    </form>

    {% if tasks %}
        {% for task in tasks %}
        <div class="task">
            <span class="task-title {{ 'done' if task[2] else '' }}">
                {{ task[1] }}
            </span>
            <div class="actions">
                <form action="/toggle/{{ task[0] }}" method="POST">
                    <button class="complete" type="submit">
                        {{ 'Undo' if task[2] else 'Done' }}
                    </button>
                </form>
                <form action="/delete/{{ task[0] }}" method="POST">
                    <button class="delete" type="submit">Delete</button>
                </form>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <p class="empty">No tasks yet. Add your first task!</p>
    {% endif %}
</div>
</body>
</html>
"""

@app.route("/")
def index():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, completed FROM tasks ORDER BY id DESC"
        )
        tasks = cursor.fetchall()
        cursor.close()
        return render_template_string(HTML, tasks=tasks)
    finally:
        conn.close()

@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    if title:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (title) VALUES (%s)", (title,)
            )
            conn.commit()
            cursor.close()
        finally:
            conn.close()
    return redirect("/")

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE tasks SET completed = NOT completed
               WHERE id = %s""",
            (task_id,)
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()
    return redirect("/")

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
        cursor.close()
    finally:
        conn.close()
    return redirect("/")

if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000)
