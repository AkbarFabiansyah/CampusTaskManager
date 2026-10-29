from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DATABASE = os.path.join("database", "campus.db")

# Membuat folder database jika belum ada
os.makedirs("database", exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            deadline TEXT NOT NULL,
            priority TEXT NOT NULL,
            duration REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'To Do'
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def dashboard():
    conn = get_db_connection()

    tasks = conn.execute("""
        SELECT * FROM tasks
        ORDER BY
            CASE priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
            END,
            deadline ASC
    """).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    completed = conn.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE status = 'Completed'
    """).fetchone()[0]

    in_progress = conn.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE status = 'In Progress'
    """).fetchone()[0]

    pending = conn.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE status = 'To Do'
    """).fetchone()[0]

    conn.close()

    progress = round((completed / total) * 100) if total else 0

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total=total,
        completed=completed,
        in_progress=in_progress,
        pending=pending,
        progress=progress
    )


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    deadline = request.form.get("deadline", "")
    priority = request.form.get("priority", "")
    duration = request.form.get("duration", "")

    if not title or not subject or not deadline:
        return "Judul, mata kuliah, dan deadline wajib diisi.", 400

    if priority not in ["Low", "Medium", "High"]:
        return "Prioritas tidak valid.", 400

    try:
        duration = float(duration)

        if not 0 < duration <= 24 * 30:
            raise ValueError

    except (ValueError, TypeError):
        return "Durasi harus lebih dari 0 dan maksimal 720 jam.", 400

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO tasks
        (title, subject, deadline, priority, duration, status)
        VALUES (?, ?, ?, ?, ?, 'To Do')
    """, (title, subject, deadline, priority, duration))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/update/<int:task_id>", methods=["POST"])
def update_task(task_id):
    status = request.form.get("status", "")

    if status not in ["To Do", "In Progress", "Completed"]:
        return "Status tidak valid.", 400

    conn = get_db_connection()

    conn.execute("""
        UPDATE tasks
        SET status = ?
        WHERE id = ?
    """, (status, task_id))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)