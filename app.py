from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Use a strong secret key


# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------
def get_db():
    conn = sqlite3.connect('salon.db')
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------
# INITIALIZE DATABASE (Create tables if not exist)
# ---------------------------------------------------
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create user table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT
        )
    """)

    # Create booking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tbl_booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fullname TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            service TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            notes TEXT,
            payment_method TEXT NOT NULL,
            transaction_id TEXT,
            FOREIGN KEY (user_id) REFERENCES tbl_user(id)
        )
    """)

    conn.commit()
    conn.close()


# Initialize database tables at startup
init_db()


# ---------------------------------------------------
# HOME
# ---------------------------------------------------
@app.route('/')
def index():
    user_logged_in = 'user_id' in session
    return render_template('index.html', user_logged_in=user_logged_in, fullname=session.get('fullname'))


# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO tbl_user (fullname, email, password, phone) VALUES (?, ?, ?, ?)",
                (fullname, email, password, phone)
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "danger")
        finally:
            conn.close()

    return render_template('register.html')


# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------
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
            flash(f"Welcome back, {user['fullname']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")

    return render_template('login.html')


# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))
    return render_template('dashboard.html', fullname=session['fullname'])


# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


# ---------------------------------------------------
# BOOK APPOINTMENT
# ---------------------------------------------------
@app.route('/book', methods=['POST'])
def submit_booking():
    if 'user_id' not in session:
        flash("Please log in to book an appointment.", "warning")
        return redirect(url_for('login'))

    # Get form data
    fullname = request.form['fullName']
    email = request.form['email']
    phone = request.form['phone']
    service = request.form['service']
    date = request.form['date']
    time = request.form['time']
    notes = request.form['notes']

    # Save booking temporarily in session
    session['booking'] = {
        'fullname': fullname,
        'email': email,
        'phone': phone,
        'service': service,
        'date': date,
        'time': time,
        'notes': notes
    }

    return redirect(url_for('payment'))


# ---------------------------------------------------
# PAYMENT
# ---------------------------------------------------
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'booking' not in session:
        flash("Please book an appointment first.", "warning")
        return redirect(url_for('index'))

    booking = session['booking']

    if request.method == 'POST':
        payment_method = request.form['payment_method']
        transaction_id = request.form.get('transaction_id', '')

        conn = get_db()
        conn.execute("""
            INSERT INTO tbl_booking 
            (user_id, fullname, email, phone, service, date, time, notes, payment_method, transaction_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session['user_id'], booking['fullname'], booking['email'], booking['phone'],
            booking['service'], booking['date'], booking['time'], booking['notes'],
            payment_method, transaction_id
        ))
        conn.commit()
        conn.close()

        session.pop('booking')  # clear temporary booking info
        flash("Payment successful! Your appointment is confirmed.", "success")
        return redirect(url_for('index'))

    return render_template('payment.html', booking=booking)


# ---------------------------------------------------
# RUN APP
# ---------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
