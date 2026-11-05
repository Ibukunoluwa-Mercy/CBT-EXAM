import os
import sqlite3
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-key")
DATABASE = os.path.join(app.root_path, "database.db")
EXAM_DURATION = 15 * 60

QUESTIONS = [
    ("Computer Basics", "Which device is used to enter text into a computer?", "Keyboard", ["Monitor", "Printer", "Speaker"]),
    ("Computer Basics", "What does CPU stand for?", "Central Processing Unit", ["Computer Personal Unit", "Central Program Utility", "Control Processing User"]),
    ("Mathematics", "What is 12 multiplied by 8?", "96", ["86", "108", "120"]),
    ("Mathematics", "What is the square root of 81?", "9", ["7", "8", "10"]),
    ("English", "Choose the correctly spelled word.", "Necessary", ["Neccessary", "Necesary", "Necassary"]),
    ("General Knowledge", "Which planet is known as the Red Planet?", "Mars", ["Venus", "Jupiter", "Saturn"]),
    ("Science", "What gas do humans need to breathe?", "Oxygen", ["Nitrogen", "Carbon dioxide", "Hydrogen"]),
    ("ICT", "Which symbol begins an email address?", "@", ["#", "&", "%"]),
]


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                options TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id)
            );
        """)
        count = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if count == 0:
            connection.executemany(
                "INSERT INTO questions(subject, question, answer, options) VALUES (?, ?, ?, ?)",
                [(subject, question, answer, "|".join([answer] + options))
                 for subject, question, answer, options in QUESTIONS],
            )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirm_password", "")
        if not fullname or not email or len(password) < 8:
            flash("Enter your name, a valid email and a password of at least 8 characters.", "error")
            return render_template("register.html")
        if password != confirmation:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        try:
            with get_db() as connection:
                connection.execute(
                    "INSERT INTO students(fullname, email, password) VALUES (?, ?, ?)",
                    (fullname, email, generate_password_hash(password)),
                )
            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email address is already registered.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as connection:
            student = connection.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
        if student and check_password_hash(student["password"], password):
            session["student_id"] = student["id"]
            session["student_name"] = student["fullname"]
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as connection:
        attempts = connection.execute(
            "SELECT * FROM attempts WHERE student_id = ? ORDER BY completed_at DESC",
            (session["student_id"],),
        ).fetchall()
    return render_template("dashboard.html", attempts=attempts)


@app.route("/exam")
@login_required
def exam():
    with get_db() as connection:
        questions = connection.execute("SELECT * FROM questions ORDER BY id").fetchall()
    return render_template("exam.html", questions=questions, duration=EXAM_DURATION)


@app.route("/submit-exam", methods=["POST"])
@login_required
def submit_exam():
    with get_db() as connection:
        questions = connection.execute("SELECT * FROM questions ORDER BY id").fetchall()
        score = sum(request.form.get(str(question["id"])) == question["answer"] for question in questions)
        cursor = connection.execute(
            "INSERT INTO attempts(student_id, score, total) VALUES (?, ?, ?)",
            (session["student_id"], score, len(questions)),
        )
    return redirect(url_for("result", attempt_id=cursor.lastrowid))


@app.route("/result/<int:attempt_id>")
@login_required
def result(attempt_id):
    with get_db() as connection:
        attempt = connection.execute(
            "SELECT * FROM attempts WHERE id = ? AND student_id = ?",
            (attempt_id, session["student_id"]),
        ).fetchone()
    if attempt is None:
        flash("Result not found.", "error")
        return redirect(url_for("dashboard"))
    percentage = round((attempt["score"] / attempt["total"]) * 100)
    return render_template("result.html", attempt=attempt, percentage=percentage)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
