import os
import re
import json
import logging
import traceback
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

from flask import (
    Flask, render_template, request, flash, redirect,
    url_for, jsonify, send_file, session
)
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import psycopg
from psycopg.rows import dict_row

# =========================================================
# --- CONFIGURATION ---
# =========================================================
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# =========================================================
# --- SECRET KEYS AND ENVIRONMENT VARIABLES ---
# =========================================================
session_secret = os.environ.get("SESSION_SECRET")
if not session_secret:
    raise RuntimeError("SESSION_SECRET environment variable must be set")
app.secret_key = session_secret

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL environment variable must be set")

# =========================================================
# --- SESSION AND SECURITY CONFIG ---
# =========================================================
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# =========================================================
# --- MAIL CONFIG ---
# =========================================================
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
mail = Mail(app)

# =========================================================
# --- UPLOAD CONFIG ---
# =========================================================
app.config['UPLOAD_FOLDER'] = 'uploads/receipts'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# =========================================================
# --- DATABASE CONNECTION HELPERS ---
# =========================================================
def get_db_connection():
    """Get a psycopg connection to the PostgreSQL database."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable must be set")
    
    # Normalize URL for psycopg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    elif url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    
    return psycopg.connect(url, row_factory=dict_row, autocommit=False)

# =========================================================
# --- TABLE CREATION FUNCTIONS ---
# =========================================================
def create_tables():
    """Create all necessary database tables using pure psycopg."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Students table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    matric_number VARCHAR(20) UNIQUE NOT NULL,
                    level INTEGER NOT NULL,
                    department VARCHAR(100),
                    email VARCHAR(100),
                    phone VARCHAR(20),
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Admins table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    session_name VARCHAR(20) UNIQUE NOT NULL,
                    is_current BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Courses table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    course_code VARCHAR(20) UNIQUE NOT NULL,
                    course_title VARCHAR(200) NOT NULL,
                    course_unit INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    semester INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Results table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                    course_code VARCHAR(20) NOT NULL,
                    course_title VARCHAR(200) NOT NULL,
                    course_unit INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    grade VARCHAR(2) NOT NULL,
                    grade_point NUMERIC(3, 2) NOT NULL,
                    semester INTEGER NOT NULL,
                    session_id INTEGER REFERENCES sessions(id),
                    uploaded_by INTEGER REFERENCES admins(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Contacts table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    subject VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Payments table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    matric_number VARCHAR(20) NOT NULL,
                    level INTEGER NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    phone_number VARCHAR(20) NOT NULL,
                    payment_items TEXT NOT NULL,
                    total_amount NUMERIC(10, 2) NOT NULL,
                    transaction_ref VARCHAR(100),
                    payment_date DATE,
                    receipt_filename VARCHAR(200),
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_students_matric ON students(matric_number)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_matric ON payments(matric_number)")
            
            conn.commit()
            app.logger.info("✅ All tables created successfully")
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error creating tables: {e}")
        raise
    finally:
        conn.close()

def seed_database():
    """Seed the database with default data."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Create default admin (username='admin', password='aeeAdmin')
            cur.execute("SELECT id FROM admins WHERE username = %s", ('admin',))
            if not cur.fetchone():
                admin_hash = generate_password_hash('aeeAdmin')
                cur.execute("""
                    INSERT INTO admins (name, username, password_hash, role, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                """, ('System Administrator', 'admin', admin_hash, 'super_admin', True))
                app.logger.info("✅ Default admin created (username=admin, password=aeeAdmin)")
            
            # Create default session
            cur.execute("SELECT id FROM sessions WHERE session_name = %s", ('2024/2025',))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO sessions (session_name, is_current)
                    VALUES (%s, %s)
                """, ('2024/2025', True))
                app.logger.info("✅ Default session 2024/2025 created")
            
            # Create sample courses
            cur.execute("SELECT COUNT(*) as count FROM courses")
            result = cur.fetchone()
            if result['count'] == 0:
                sample_courses = [
                    ("AGE 101", "Introduction to Agricultural Engineering", 2, 100, 1),
                    ("AGE 102", "Engineering Drawing and Design", 3, 100, 1),
                    ("AGE 103", "Mathematics for Engineers I", 3, 100, 1),
                    ("AGE 104", "Physics for Engineers", 3, 100, 1),
                    ("AGE 105", "Chemistry for Engineers", 3, 100, 1),
                    ("AGE 111", "Workshop Technology", 2, 100, 2),
                    ("AGE 112", "Mathematics for Engineers II", 3, 100, 2),
                    ("AGE 113", "Engineering Mechanics", 3, 100, 2),
                    ("AGE 201", "Fluid Mechanics", 3, 200, 1),
                    ("AGE 202", "Strength of Materials", 3, 200, 1),
                    ("AGE 203", "Thermodynamics", 3, 200, 1),
                    ("AGE 301", "Farm Power and Machinery", 3, 300, 1),
                    ("AGE 302", "Soil and Water Engineering", 3, 300, 1),
                    ("AGE 401", "Agricultural Processing Engineering", 3, 400, 1),
                    ("AGE 501", "Project", 6, 500, 1),
                ]
                for code, title, unit, level, semester in sample_courses:
                    cur.execute("""
                        INSERT INTO courses (course_code, course_title, course_unit, level, semester)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (code, title, unit, level, semester))
                app.logger.info("✅ Sample courses inserted")
            
            conn.commit()
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error seeding database: {e}")
        raise
    finally:
        conn.close()

# =========================================================
# --- AUTHENTICATION HELPERS ---
# =========================================================
# Session keys for separate authentication
STUDENT_SESSION_KEY = 'student_user_id'
ADMIN_SESSION_KEY = 'admin_user_id'

def student_login_required(f):
    """Decorator to require student authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if STUDENT_SESSION_KEY not in session:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_login_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ADMIN_SESSION_KEY not in session:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_student():
    """Get the currently logged-in student."""
    student_id = session.get(STUDENT_SESSION_KEY)
    if not student_id:
        return None
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
            student = cur.fetchone()
            conn.close()
            return student
    except Exception as e:
        app.logger.error(f"Error getting current student: {e}")
        return None

def get_current_admin():
    """Get the currently logged-in admin."""
    admin_id = session.get(ADMIN_SESSION_KEY)
    if not admin_id:
        return None
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM admins WHERE id = %s", (admin_id,))
            admin = cur.fetchone()
            conn.close()
            return admin
    except Exception as e:
        app.logger.error(f"Error getting current admin: {e}")
        return None

# =========================================================
# --- VALIDATION HELPERS ---
# =========================================================
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
ALLOWED_LEVELS = {100, 200, 300, 400, 500}

def validate_matric_number(matric_number):
    """Validate matric number format."""
    return bool(re.fullmatch(r'\d{6}', str(matric_number).strip() if matric_number else ""))

def get_student_level_for_session(matric_number, session_name):
    """Calculate student level based on matric number and session."""
    try:
        mn = re.sub(r'\D', '', str(matric_number).strip())
        now_year = datetime.utcnow().year
        entry_year = None
        
        if len(mn) >= 4:
            first4 = int(mn[:4])
            if 2000 <= first4 <= now_year:
                entry_year = first4
        
        if entry_year is None and len(mn) >= 2:
            first2 = int(mn[:2])
            candidate = 2000 + first2
            if 2000 <= candidate <= now_year:
                entry_year = candidate
        
        session_start_year = int(str(session_name).split('/')[0])
        if entry_year is None:
            entry_year = session_start_year
        
        years_since_entry = session_start_year - entry_year
        return max(100, min(100 + years_since_entry * 100, 500))
    except Exception:
        return 200

def calculate_grade_points(score, level):
    """Calculate grade points based on score and level."""
    if level == 100:
        return 5.0 if score >= 70 else 4.0 if score >= 60 else 3.0 if score >= 50 else 2.0 if score >= 45 else 1.0 if score >= 40 else 0.0
    return 4.0 if score >= 70 else 3.0 if score >= 60 else 2.0 if score >= 50 else 1.0 if score >= 45 else 0.0

def get_letter_grade(score):
    """Get letter grade based on score."""
    return 'A' if score >= 70 else 'B' if score >= 60 else 'C' if score >= 50 else 'D' if score >= 45 else 'E' if score >= 40 else 'F'

def check_payment_status(matric_number):
    """Check if student has an approved payment."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT status FROM payments 
                WHERE matric_number = %s AND status = 'approved'
                LIMIT 1
            """, (matric_number,))
            result = cur.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        app.logger.error(f"Error checking payment status: {e}")
        return False

# =========================================================
# --- PUBLIC ROUTES ---
# =========================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/students')
def students():
    return render_template('students.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/staff')
def staff():
    return render_template('staff.html')

@app.route('/payment')
def payment():
    return render_template('admin/payment.html')

@app.route('/academic_program')
def academic_program():
    return render_template('academic_program.html')

# =========================================================
# --- CONTACT FORM ROUTE ---
# =========================================================
@app.route('/contact', methods=['POST'])
def contact():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not all([name, email, subject, message]):
            flash('All fields are required.', 'error')
            return redirect(url_for('index') + '#contact')
        
        # Save to database
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO contacts (name, email, subject, message)
                VALUES (%s, %s, %s, %s)
            """, (name, email, subject, message))
            conn.commit()
        conn.close()
        
        flash('Your message has been sent successfully!', 'success')
    except Exception as e:
        app.logger.error(f"Error processing contact form: {str(e)}")
        flash('Sorry, there was an error sending your message. Please try again later.', 'error')
    
    return redirect(url_for('index') + '#contact')

# =========================================================
# --- PAYMENT SUBMISSION ROUTES ---
# =========================================================
@app.route('/submit-payment', methods=['POST'])
def submit_payment():
    """Public payment submission route (for backwards compatibility)."""
    return handle_payment_submission()

# =========================================================
# --- STUDENT PAYMENT ROUTES ---
# =========================================================
@app.route('/student/payment')
@student_login_required
def student_payment_form():
    """Display payment form for logged-in students."""
    student = get_current_student()
    if not student:
        return redirect(url_for('student_login'))
    
    return render_template('admin/payment.html', student=student)

@app.route('/student/submit-payment', methods=['POST'])
@student_login_required
def student_submit_payment():
    """Student payment submission route."""
    return handle_payment_submission()

def handle_payment_submission():
    """Handle payment submission from both public and student forms."""
    try:
        # Get form data
        full_name = request.form.get('fullName')
        matric_number = request.form.get('matricNumber')
        level = int(request.form.get('level') or '0')
        email = request.form.get('email')
        phone_number = request.form.get('phoneNumber')
        payment_items = request.form.get('paymentItems')
        total_amount = float(request.form.get('totalAmount') or '0')
        transaction_ref = request.form.get('transactionRef')
        payment_date_str = request.form.get('paymentDate')
        
        # Validate required fields
        if not all([full_name, matric_number, level, email, phone_number, payment_items, total_amount]):
            return jsonify({'success': False, 'error': 'All required fields must be filled'})

        # Validate Full Name
        if not full_name.replace(" ", "").isalpha():
            return jsonify({'success': False, 'error': 'Invalid full name'})

        # Validate Matric Number
        if not re.match(r"^[A-Za-z0-9\-]+$", matric_number):
            return jsonify({'success': False, 'error': 'Invalid matric number format'})

        # Validate Level
        if level not in ALLOWED_LEVELS:
            return jsonify({'success': False, 'error': 'Invalid academic level'})

        # Validate Email
        if not EMAIL_REGEX.match(email):
            return jsonify({'success': False, 'error': 'Invalid email format'})

        # Handle payment date
        payment_date = None
        if payment_date_str:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        
        # Handle file upload
        receipt_filename = None
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'success': False, 'error': 'Invalid file type. Only PNG, JPG, JPEG, and PDF are allowed.'})
                filename = secure_filename(f"{matric_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                receipt_filename = filename
        
        # Check if matric number already exists
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM payments WHERE matric_number = %s", (matric_number,))
            if cur.fetchone():
                conn.close()
                return jsonify({'success': False, 'error': 'Payment already exists for this matric number'})
            
            # Insert payment
            cur.execute("""
                INSERT INTO payments (full_name, matric_number, level, email, phone_number, 
                                    payment_items, total_amount, transaction_ref, payment_date, receipt_filename)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (full_name, matric_number, level, email, phone_number, payment_items, 
                  total_amount, transaction_ref, payment_date, receipt_filename))
            
            payment_id = cur.fetchone()['id']
            conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Payment information submitted successfully!',
            'payment_id': payment_id
        })
        
    except Exception as e:
        app.logger.error(f"Error processing payment: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

# =========================================================
# --- STUDENT AUTHENTICATION ROUTES ---
# =========================================================
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    """Student login route - separate from admin."""
    if STUDENT_SESSION_KEY in session:
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        matric_number = request.form.get('matric_number', '').strip()
        password = request.form.get('password', '')
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM students WHERE matric_number = %s", (matric_number,))
                student = cur.fetchone()
                
                if student and check_password_hash(student['password_hash'], password):
                    if not student.get('is_active', True):
                        flash('Your account is inactive. Contact the department.', 'error')
                        conn.close()
                        return render_template('login.html')
                    
                    # Set student session
                    session[STUDENT_SESSION_KEY] = student['id']
                    session.permanent = True
                    flash(f'Welcome, {student["name"]}!', 'success')
                    conn.close()
                    
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('student_dashboard'))
                else:
                    flash('Invalid matric number or password', 'error')
            conn.close()
        except Exception as e:
            flash('Error during login. Please try again.', 'error')
            app.logger.error(f"Student login error: {e}")
    
    return render_template('login.html')

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    """Student registration route."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        matric_number = request.form.get('matric_number', '').strip()
        try:
            level = int(request.form.get('level', '100'))
        except ValueError:
            level = 100
        department = request.form.get('department', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([name, matric_number, password, confirm_password]):
            flash('Please fill in all required fields', 'error')
            return render_template('register.html')
        
        if not validate_matric_number(matric_number):
            flash('Invalid matric number format. Use 6 digits.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
        if level not in ALLOWED_LEVELS:
            flash('Invalid level', 'error')
            return render_template('register.html')
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Check if matric number exists
                cur.execute("SELECT id FROM students WHERE matric_number = %s", (matric_number,))
                if cur.fetchone():
                    flash('This matric number is already registered', 'error')
                    conn.close()
                    return render_template('register.html')
                
                # Insert new student
                password_hash = generate_password_hash(password)
                cur.execute("""
                    INSERT INTO students (name, matric_number, level, department, email, phone, password_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, matric_number, level, department, email, phone, password_hash))
                conn.commit()
            conn.close()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('student_login'))
        except Exception as e:
            flash('Error during registration. Please try again.', 'error')
            app.logger.error(f"Student registration error: {e}")
    
    return render_template('register.html')

@app.route('/student/logout')
def student_logout():
    """Student logout route."""
    session.pop(STUDENT_SESSION_KEY, None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('student_login'))

# =========================================================
# --- STUDENT DASHBOARD AND ROUTES ---
# =========================================================
@app.route('/student/dashboard')
@student_login_required
def student_dashboard():
    """Student dashboard showing their results."""
    student = get_current_student()
    if not student:
        return redirect(url_for('student_login'))
    
    has_payment = check_payment_status(student['matric_number'])
    
    if not has_payment:
        flash('You must complete payment before accessing results.', 'warning')
        return render_template('student_dashboard.html',
                             student=student,
                             has_payment=False,
                             sessions=[],
                             current_session=None,
                             grouped_results={},
                             gpa_data={})
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get all sessions
            cur.execute("SELECT * FROM sessions ORDER BY session_name DESC")
            all_sessions = cur.fetchall()
            
            # Get current session
            cur.execute("SELECT * FROM sessions WHERE is_current = TRUE LIMIT 1")
            current_session = cur.fetchone()
            
            # Get results for this student
            cur.execute("""
                SELECT r.*, s.session_name 
                FROM results r
                LEFT JOIN sessions s ON r.session_id = s.id
                WHERE r.student_id = %s
                ORDER BY s.session_name DESC, r.semester, r.course_code
            """, (student['id'],))
            results = cur.fetchall()
        conn.close()
        
        # Group results by session and semester
        grouped_results = {}
        for result in results:
            session_name = result.get('session_name', 'Unknown')
            semester = result['semester']
            key = f"{session_name}_S{semester}"
            if key not in grouped_results:
                grouped_results[key] = []
            grouped_results[key].append(result)
        
        # Calculate GPA for each group
        gpa_data = {}
        for key, res_list in grouped_results.items():
            total_points = sum(float(r['grade_point']) * r['course_unit'] for r in res_list)
            total_units = sum(r['course_unit'] for r in res_list)
            gpa = round(total_points / total_units, 2) if total_units > 0 else 0.0
            gpa_data[key] = {'gpa': gpa, 'units': total_units}
        
        return render_template('student_dashboard.html',
                             student=student,
                             has_payment=True,
                             sessions=all_sessions,
                             current_session=current_session,
                             grouped_results=grouped_results,
                             gpa_data=gpa_data)
    except Exception as e:
        app.logger.error(f"Error loading student dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('student_login'))

# =========================================================
# --- ADMIN AUTHENTICATION ROUTES ---
# =========================================================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login route - separate from student."""
    if ADMIN_SESSION_KEY in session:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
                admin = cur.fetchone()
                
                if admin and check_password_hash(admin['password_hash'], password):
                    if not admin.get('is_active', True):
                        flash('Your account is inactive.', 'error')
                        conn.close()
                        return render_template('admin_login.html')
                    
                    # Set admin session
                    session[ADMIN_SESSION_KEY] = admin['id']
                    session.permanent = True
                    flash(f'Welcome, {admin["name"]}!', 'success')
                    conn.close()
                    
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Invalid username or password', 'error')
            conn.close()
        except Exception as e:
            flash('Error during login. Please try again.', 'error')
            app.logger.error(f"Admin login error: {e}")
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout route."""
    session.pop(ADMIN_SESSION_KEY, None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))

# =========================================================
# --- ADMIN DASHBOARD AND ROUTES ---
# =========================================================
@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    """Admin dashboard with statistics."""
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get statistics
            cur.execute("SELECT COUNT(*) as count FROM students")
            total_students = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM contacts")
            total_contacts = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM payments")
            total_payments = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM results")
            total_results = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM payments WHERE status = 'pending'")
            pending_payments = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM payments WHERE status = 'approved'")
            approved_payments = cur.fetchone()['count']
            
            # Recent submissions
            cur.execute("SELECT * FROM contacts ORDER BY created_at DESC LIMIT 5")
            recent_contacts = cur.fetchall()
            
            cur.execute("SELECT * FROM payments ORDER BY created_at DESC LIMIT 5")
            recent_payments = cur.fetchall()
        conn.close()
        
        return render_template('admin/admin_dashboard.html',
                             admin=admin,
                             total_students=total_students,
                             total_contacts=total_contacts,
                             total_payments=total_payments,
                             total_results=total_results,
                             pending_payments=pending_payments,
                             approved_payments=approved_payments,
                             recent_contacts=recent_contacts,
                             recent_payments=recent_payments)
    except Exception as e:
        app.logger.error(f"Error loading admin dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('admin_login'))

# =========================================================
# --- ADMIN CONTACT MANAGEMENT ROUTES ---
# =========================================================
@app.route('/admin/contacts')
@admin_login_required
def admin_contacts():
    """View all contacts."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM contacts")
            total = cur.fetchone()['count']
            
            cur.execute("""
                SELECT * FROM contacts 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            contacts = cur.fetchall()
        conn.close()
        
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('admin/admin_contacts.html',
                             contacts=contacts,
                             page=page,
                             total_pages=total_pages,
                             has_prev=page > 1,
                             has_next=page < total_pages)
    except Exception as e:
        app.logger.error(f"Error loading contacts: {e}")
        flash('Error loading contacts', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/contacts/<int:contact_id>')
@admin_login_required
def admin_view_contact(contact_id):
    """View contact details."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM contacts WHERE id = %s", (contact_id,))
            contact = cur.fetchone()
        conn.close()
        
        if not contact:
            flash('Contact not found', 'error')
            return redirect(url_for('admin_contacts'))
        
        return render_template('admin/admin_contact_detail.html', contact=contact)
    except Exception as e:
        app.logger.error(f"Error viewing contact: {e}")
        flash('Error viewing contact', 'error')
        return redirect(url_for('admin_contacts'))

@app.route('/admin/contacts/<int:contact_id>/delete', methods=['POST'])
@admin_login_required
def admin_delete_contact(contact_id):
    """Delete a contact."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
            conn.commit()
        conn.close()
        
        flash('Contact deleted successfully!', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting contact: {e}")
        flash('Error deleting contact', 'error')
    
    return redirect(url_for('admin_contacts'))

# =========================================================
# --- ADMIN PAYMENT MANAGEMENT ROUTES ---
# =========================================================
@app.route('/admin/payments')
@admin_login_required
def admin_payments():
    """View all payments."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    per_page = 20
    offset = (page - 1) * per_page
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if status_filter:
                cur.execute("SELECT COUNT(*) as count FROM payments WHERE status = %s", (status_filter,))
                total = cur.fetchone()['count']
                
                cur.execute("""
                    SELECT * FROM payments 
                    WHERE status = %s
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (status_filter, per_page, offset))
            else:
                cur.execute("SELECT COUNT(*) as count FROM payments")
                total = cur.fetchone()['count']
                
                cur.execute("""
                    SELECT * FROM payments 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
            
            payments = cur.fetchall()
        conn.close()
        
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('admin/admin_payments.html',
                             payments=payments,
                             page=page,
                             total_pages=total_pages,
                             has_prev=page > 1,
                             has_next=page < total_pages,
                             status_filter=status_filter)
    except Exception as e:
        app.logger.error(f"Error loading payments: {e}")
        flash('Error loading payments', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/payments/<int:payment_id>')
@admin_login_required
def admin_view_payment(payment_id):
    """View payment details."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
            payment = cur.fetchone()
        conn.close()
        
        if not payment:
            flash('Payment not found', 'error')
            return redirect(url_for('admin_payments'))
        
        try:
            payment_items = json.loads(payment['payment_items']) if payment['payment_items'] else []
        except:
            payment_items = []
        
        return render_template('admin/admin_payment_detail.html',
                             payment=payment,
                             payment_items=payment_items)
    except Exception as e:
        app.logger.error(f"Error viewing payment: {e}")
        flash('Error viewing payment', 'error')
        return redirect(url_for('admin_payments'))

@app.route('/admin/payments/<int:payment_id>/update_status', methods=['POST'])
@admin_login_required
def admin_update_payment_status(payment_id):
    """Update payment status."""
    new_status = request.form.get('status')
    
    if new_status not in ['pending', 'approved', 'rejected']:
        flash('Invalid status!', 'error')
        return redirect(url_for('admin_view_payment', payment_id=payment_id))
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE payments 
                SET status = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (new_status, payment_id))
            conn.commit()
        conn.close()
        
        flash(f'Payment status updated to {new_status}!', 'success')
    except Exception as e:
        app.logger.error(f"Error updating payment status: {e}")
        flash('Error updating payment status', 'error')
    
    return redirect(url_for('admin_view_payment', payment_id=payment_id))

@app.route('/admin/payments/<int:payment_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def admin_edit_payment(payment_id):
    """Edit payment details."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
            payment = cur.fetchone()
        
        if not payment:
            conn.close()
            flash('Payment not found', 'error')
            return redirect(url_for('admin_payments'))
        
        if request.method == 'POST':
            full_name = request.form.get('full_name')
            matric_number = request.form.get('matric_number')
            level = int(request.form.get('level', 0))
            email = request.form.get('email')
            phone_number = request.form.get('phone_number')
            total_amount = float(request.form.get('total_amount', 0))
            transaction_ref = request.form.get('transaction_ref')
            
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE payments 
                    SET full_name = %s, matric_number = %s, level = %s, 
                        email = %s, phone_number = %s, total_amount = %s, 
                        transaction_ref = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (full_name, matric_number, level, email, phone_number,
                      total_amount, transaction_ref, payment_id))
                conn.commit()
            conn.close()
            
            flash('Payment updated successfully!', 'success')
            return redirect(url_for('admin_view_payment', payment_id=payment_id))
        
        conn.close()
        return render_template('admin/admin_edit_payment.html', payment=payment)
    except Exception as e:
        app.logger.error(f"Error editing payment: {e}")
        flash('Error editing payment', 'error')
        return redirect(url_for('admin_payments'))

@app.route('/admin/payments/<int:payment_id>/delete', methods=['POST'])
@admin_login_required
def admin_delete_payment(payment_id):
    """Delete a payment."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get payment to find receipt file
            cur.execute("SELECT receipt_filename FROM payments WHERE id = %s", (payment_id,))
            payment = cur.fetchone()
            
            if payment and payment['receipt_filename']:
                receipt_path = os.path.join('uploads/receipts', payment['receipt_filename'])
                if os.path.exists(receipt_path):
                    os.remove(receipt_path)
            
            cur.execute("DELETE FROM payments WHERE id = %s", (payment_id,))
            conn.commit()
        conn.close()
        
        flash('Payment deleted successfully!', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting payment: {e}")
        flash('Error deleting payment', 'error')
    
    return redirect(url_for('admin_payments'))

@app.route('/admin/receipts/<filename>')
@admin_login_required
def admin_view_receipt(filename):
    """View receipt file."""
    receipt_path = os.path.join('uploads/receipts', filename)
    if os.path.exists(receipt_path):
        return send_file(receipt_path)
    else:
        flash('Receipt file not found!', 'error')
        return redirect(url_for('admin_payments'))

# =========================================================
# --- ADMIN EXPORT ROUTES ---
# =========================================================
@app.route('/admin/export/contacts')
@admin_login_required
def admin_export_contacts():
    """Export contacts to CSV."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM contacts ORDER BY created_at DESC")
            contacts = cur.fetchall()
        conn.close()
        
        # Create CSV content
        csv_content = "ID,Name,Email,Subject,Message,Created At\n"
        for contact in contacts:
            message_escaped = str(contact['message']).replace('"', '""')
            csv_content += f'"{contact["id"]}","{contact["name"]}","{contact["email"]}","{contact["subject"]}","{message_escaped}","{contact["created_at"]}"\n'
        
        # Save to file
        filename = f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        app.logger.error(f"Error exporting contacts: {e}")
        flash('Error exporting contacts', 'error')
        return redirect(url_for('admin_contacts'))

@app.route('/admin/export/payments')
@admin_login_required
def admin_export_payments():
    """Export payments to CSV."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM payments ORDER BY created_at DESC")
            payments = cur.fetchall()
        conn.close()
        
        # Create CSV content
        csv_content = "ID,Full Name,Matric Number,Level,Email,Phone,Total Amount,Status,Transaction Ref,Created At\n"
        for payment in payments:
            csv_content += f'"{payment["id"]}","{payment["full_name"]}","{payment["matric_number"]}","{payment["level"]}","{payment["email"]}","{payment["phone_number"]}","{payment["total_amount"]}","{payment["status"]}","{payment.get("transaction_ref", "")}","{payment["created_at"]}"\n'
        
        # Save to file
        filename = f"payments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        app.logger.error(f"Error exporting payments: {e}")
        flash('Error exporting payments', 'error')
        return redirect(url_for('admin_payments'))

# =========================================================
# --- ADMIN STUDENTS ROUTES ---
# =========================================================
@app.route('/admin/students')
@admin_login_required
def admin_students():
    """View all students with approve/reject options."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM students")
            total = cur.fetchone()['count']
            
            cur.execute("""
                SELECT * FROM students 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            students = cur.fetchall()
        conn.close()
        
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('admin/admin_students.html',
                             students=students,
                             page=page,
                             total_pages=total_pages,
                             has_prev=page > 1,
                             has_next=page < total_pages)
    except Exception as e:
        app.logger.error(f"Error loading students: {e}")
        flash('Error loading students', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/students/<int:student_id>/toggle-status', methods=['POST'])
@admin_login_required
def admin_toggle_student_status(student_id):
    """Approve or reject (activate/deactivate) a student account."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT is_active FROM students WHERE id = %s", (student_id,))
            student = cur.fetchone()
            
            if student:
                new_status = not student['is_active']
                cur.execute("""
                    UPDATE students 
                    SET is_active = %s 
                    WHERE id = %s
                """, (new_status, student_id))
                conn.commit()
                
                status_text = 'approved' if new_status else 'rejected'
                flash(f'Student account {status_text} successfully!', 'success')
        conn.close()
    except Exception as e:
        app.logger.error(f"Error toggling student status: {e}")
        flash('Error updating student status', 'error')
    
    return redirect(url_for('admin_students'))

# =========================================================
# --- ADMIN RESULTS ROUTES ---
# =========================================================
@app.route('/admin/results/upload', methods=['GET', 'POST'])
@admin_login_required
def admin_upload_results():
    """Upload results for students."""
    admin = get_current_admin()
    
    if request.method == 'POST':
        try:
            student_matric = request.form.get('matric_number')
            course_code = request.form.get('course_code')
            course_title = request.form.get('course_title')
            course_unit = int(request.form.get('course_unit', 0))
            score = int(request.form.get('score', 0))
            semester = int(request.form.get('semester', 1))
            session_id = request.form.get('session_id')
            
            if not all([student_matric, course_code, course_title, course_unit, semester, session_id]):
                flash('All fields are required', 'error')
                return redirect(url_for('admin_upload_results'))
            
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Get student by matric number
                cur.execute("SELECT id, level FROM students WHERE matric_number = %s", (student_matric,))
                student = cur.fetchone()
                
                if not student:
                    flash('Student not found', 'error')
                    conn.close()
                    return redirect(url_for('admin_upload_results'))
                
                student_id = student['id']
                level = student['level']
                
                # Calculate grade and grade points
                grade = get_letter_grade(score)
                grade_point = calculate_grade_points(score, level)
                
                # Insert result
                cur.execute("""
                    INSERT INTO results (student_id, course_code, course_title, course_unit, 
                                       score, grade, grade_point, semester, session_id, uploaded_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (student_id, course_code, course_title, course_unit, 
                      score, grade, grade_point, semester, session_id, admin['id']))
                conn.commit()
            conn.close()
            
            flash('Result uploaded successfully!', 'success')
            return redirect(url_for('admin_upload_results'))
        except Exception as e:
            app.logger.error(f"Error uploading result: {e}")
            flash('Error uploading result', 'error')
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sessions ORDER BY session_name DESC")
            sessions = cur.fetchall()
        conn.close()
        
        return render_template('admin/admin_upload_results.html', sessions=sessions)
    except Exception as e:
        app.logger.error(f"Error loading upload form: {e}")
        flash('Error loading form', 'error')
        return redirect(url_for('admin_dashboard'))

# =========================================================
# --- API ROUTES ---
# =========================================================
@app.route('/api/courses/search')
@admin_login_required
def api_search_courses():
    """Search courses by query for autocomplete."""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT course_code, course_title, course_unit, level, semester
                FROM courses
                WHERE LOWER(course_code) LIKE LOWER(%s) 
                   OR LOWER(course_title) LIKE LOWER(%s)
                ORDER BY course_code
                LIMIT 20
            """, (f'%{query}%', f'%{query}%'))
            courses = cur.fetchall()
        conn.close()
        
        return jsonify([{
            'course_code': c['course_code'],
            'course_title': c['course_title'],
            'course_unit': c['course_unit'],
            'level': c['level'],
            'semester': c['semester']
        } for c in courses])
    except Exception as e:
        app.logger.error(f"Error searching courses: {e}")
        return jsonify([])

# =========================================================
# --- ADMIN STATISTICS ROUTE ---
# =========================================================
@app.route('/admin/stats')
@admin_login_required
def admin_stats():
    """View statistics."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Payment statistics by level
            cur.execute("""
                SELECT level, COUNT(*) as count, SUM(total_amount) as total
                FROM payments
                GROUP BY level
                ORDER BY level
            """)
            level_stats = cur.fetchall()
            
            # Payment statistics by status
            cur.execute("""
                SELECT status, COUNT(*) as count, SUM(total_amount) as total
                FROM payments
                GROUP BY status
                ORDER BY status
            """)
            status_stats = cur.fetchall()
            
            # Monthly payment trends
            cur.execute("""
                SELECT TO_CHAR(created_at, 'YYYY-MM') as month, 
                       COUNT(*) as count, 
                       SUM(total_amount) as total
                FROM payments
                GROUP BY month
                ORDER BY month
            """)
            monthly_stats = cur.fetchall()
        conn.close()
        
        return render_template('admin_stats.html',
                             level_stats=level_stats,
                             status_stats=status_stats,
                             monthly_stats=monthly_stats)
    except Exception as e:
        app.logger.error(f"Error loading statistics: {e}")
        flash('Error loading statistics', 'error')
        return redirect(url_for('admin_dashboard'))

# =========================================================
# --- MAIN EXECUTION BLOCK ---
# =========================================================
if __name__ == '__main__':
    # Initialize database on startup
    try:
        create_tables()
        seed_database()
        app.logger.info("✅ Database initialized successfully")
    except Exception as e:
        app.logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
