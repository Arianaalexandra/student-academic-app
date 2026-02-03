from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "secret123"

from database import init_db

init_db()

# ======================
# DATABASE
# ======================
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ======================
# AUTH DECORATOR
# ======================
def login_required(role):
    def decorator(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            if "user" not in session or session.get("role") != role:
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return inner
    return decorator


# ======================
# LOGIN
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email.endswith("@utm.ro"):
            return "Email universitar invalid"

        if email.startswith("admin") and password == "admin":
            session["user"] = email
            session["role"] = "admin"
            return redirect(url_for("admin"))

        session["user"] = email
        session["role"] = "student"
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ======================
# ADMIN
# ======================
@app.route("/admin", methods=["GET", "POST"])
@login_required("admin")
def admin():
    conn = get_db()

    if request.method == "POST":
        student_email = request.form["student_email"]
        subject = request.form["subject"]
        grade = int(request.form["grade"])
        semester = int(request.form["semester"])

        conn.execute(
            """
            INSERT INTO grades (student_email, email, subject, grade, semester)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_email, student_email, subject, grade, semester)
        )
        conn.commit()

    grades = conn.execute(
        """
        SELECT id, student_email, subject, grade, semester
        FROM grades
        ORDER BY student_email
        """
    ).fetchall()

    conn.close()
    return render_template("admin.html", grades=grades)


# ======================
# DELETE GRADE
# ======================
@app.route("/delete-grade/<int:id>")
@login_required("admin")
def delete_grade(id):
    conn = get_db()
    conn.execute("DELETE FROM grades WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


# ======================
# DASHBOARD STUDENT
# ======================
@app.route("/dashboard")
@login_required("student")
def dashboard():
    email = session["user"]
    conn = get_db()

    grades = conn.execute(
        """
        SELECT subject, grade, semester
        FROM grades
        WHERE student_email = ?
        """,
        (email,)
    ).fetchall()

    conn.close()

    semester_averages = {1: None, 2: None}
    general_average = None

    if grades:
        all_grades = [g["grade"] for g in grades]
        general_average = sum(all_grades) / len(all_grades)

        for sem in (1, 2):
            sem_grades = [g["grade"] for g in grades if g["semester"] == sem]
            if sem_grades:
                semester_averages[sem] = sum(sem_grades) / len(sem_grades)

    chart_data = {
        "labels": [g["subject"] for g in grades],
        "values": [g["grade"] for g in grades]
    }

    return render_template(
        "dashboard.html",
        grades=grades,
        semester_averages=semester_averages,
        general_average=general_average,
        chart_data=chart_data
    )


# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(debug=True)
