from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Use a strong secret key

# Connect to SQLite DB
def get_db():
    conn = sqlite3.connect('salon.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home Page
@app.route('/')
def index():
    user_logged_in = 'user_id' in session
    return render_template('index.html', user_logged_in=user_logged_in, fullname=session.get('fullname'))

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']

        conn = get_db()
        try:
            conn.execute("INSERT INTO tbl_user (fullname, email, password, phone) VALUES (?, ?, ?, ?)",
                         (fullname, email, password, phone))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except:
            flash("Email already exists!", "danger")
        finally:
            conn.close()

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        user = conn.execute("SELECT * FROM tbl_user WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['fullname'] = user['fullname']
            flash("Welcome back, " + user['fullname'] + "!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))
    return render_template('dashboard.html', fullname=session['fullname'])

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
