from flask import jsonify
import matplotlib
matplotlib.use("Agg")

from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import os

# 🔹 IMPORT CORECT DIN database.py
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = "secret123"


# ======================
# INITIALIZARE DB (CORECT PENTRU RENDER)
# ======================
@app.before_first_request
def initialize_database():
    init_db()


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
    conn = get_db_connection()

    if request.method == "POST":
        student_email = request.form["student_email"]
        subject = request.form["subject"]
        grade = int(request.form["grade"])
        semester = int(request.form["semester"])
        year = int(request.form["year"])

        conn.execute("""
            INSERT INTO grades (student_email, subject, grade, semester, year)
            VALUES (?, ?, ?, ?, ?)
        """, (student_email, subject, grade, semester, year))

        conn.commit()

    grades = conn.execute("""
        SELECT *
        FROM grades
        ORDER BY student_email, year, semester
    """).fetchall()

    conn.close()
    return render_template("admin.html", grades=grades)


# ======================
# DELETE GRADE
# ======================
@app.route("/delete-grade/<int:id>")
@login_required("admin")
def delete_grade(id):
    conn = get_db_connection()
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
    conn = get_db_connection()

    grades = conn.execute("""
        SELECT subject, grade, semester, year
        FROM grades
        WHERE student_email = ?
        ORDER BY year, semester
    """, (email,)).fetchall()

    conn.close()

    # ----------------------
    # MEDII PE ANI + SEMESTRE
    # ----------------------
    averages = {}
    all_grades = []

    for g in grades:
        year = g["year"]
        semester = g["semester"]
        averages.setdefault(year, {1: [], 2: []})
        averages[year][semester].append(g["grade"])
        all_grades.append(g["grade"])

    year_semester_averages = {}
    for year, sems in averages.items():
        year_semester_averages[year] = {}
        for sem, notes in sems.items():
            year_semester_averages[year][sem] = (
                round(sum(notes) / len(notes), 2) if notes else None
            )

    general_average = (
        round(sum(all_grades) / len(all_grades), 2) if all_grades else None
    )

    # ----------------------
    # DATE PENTRU GRAFIC
    # ----------------------
    chart_data = {
        "labels": [f"{g['subject']} (An {g['year']})" for g in grades],
        "values": [g["grade"] for g in grades]
    }

    return render_template(
        "dashboard.html",
        grades=grades,
        year_semester_averages=year_semester_averages,
        general_average=general_average,
        chart_data=chart_data
    )

# ======================
# API - REST
# ======================
@app.route("/api/grades", methods=["GET"])
def api_grades():
    conn = get_db_connection()

    grades = conn.execute("""
        SELECT student_email, subject, grade, semester, year
        FROM grades
        ORDER BY student_email, year, semester
    """).fetchall()

    conn.close()

    result = []
    for g in grades:
        result.append({
            "student_email": g["student_email"],
            "subject": g["subject"],
            "grade": g["grade"],
            "semester": g["semester"],
            "year": g["year"]
        })

    return jsonify(result)



# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
