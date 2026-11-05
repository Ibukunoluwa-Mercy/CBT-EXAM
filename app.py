
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Secret key for session and flash messages
app.secret_key = "cbt-development-secret-key"


# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Create database and students table
def create_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Student registration page
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check empty fields
        if not fullname or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("register"))

        # Check password length
        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("register"))

        # Check passwords
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        # Hash password before saving
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
                """
                INSERT INTO students (fullname, email, password)
                VALUES (?, ?, ?)
                """,
                (fullname, email, hashed_password)
            )

            conn.commit()

            flash("Registration successful! You can now log in.")

            return redirect(url_for("home"))

        except sqlite3.IntegrityError:
            flash("This email address is already registered.")
            return redirect(url_for("register"))

        finally:
            conn.close()

    return render_template("register.html")


# Start application
if __name__ == "__main__":
    create_database()
    app.run(debug=True)
