import os
import re
import json
import logging
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

from flask import (
    Flask, render_template, request, flash, redirect,
    url_for, jsonify, send_file, session
)
from flask_mail import Mail, Message
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import psycopg
from psycopg.rows import dict_row

# Local models for main site (make sure this file exists and contains your models)
from models import db, Admin, Students, Session, Course, Result, Contact, Payment


# =========================================================
# --- CONFIGURATION ---
# =========================================================
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Secret Key
session_secret = os.environ.get("SESSION_SECRET")
if not session_secret:
    raise RuntimeError("SESSION_SECRET environment variable must be set")
app.secret_key = session_secret

app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# =========================================================
# --- DATABASE CONFIG (SQLAlchemy) ---
# =========================================================
db_url = os.environ.get("DATABASE_URL") or \
    "postgresql://agricdb_user:cr7loxFwGCvhjXV0PEI4MfrtOn4crF5y@dpg-d3b3ul3ipnbc73fie560-a/agricdb"

# Normalize known prefixes for SQLAlchemy + psycopg v3
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 300, "pool_pre_ping": True}
db.init_app(app)

# =========================================================
# --- psycopg CONNECTION ---
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable must be set")

    # Normalize known prefixes for raw psycopg usage
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    elif db_url.startswith("postgresql+psycopg://"):
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)

    # psycopg v3 can accept full URL directly
    return psycopg.connect(db_url, row_factory=dict_row, autocommit=False)
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
# --- LOGIN MANAGER ---
# =========================================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# =========================================================
# --- UTILITIES / RESULT PORTAL HELPERS ---
# =========================================================
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
ALLOWED_LEVELS = {100, 200, 300, 400, 500}

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if getattr(current_user, 'role', None) not in roles:
                flash('Access denied. Insufficient privileges.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_matric_number(matric_number):
    return bool(re.fullmatch(r'\d{6}', str(matric_number).strip() if matric_number else ""))

def get_student_level_for_session(matric_number, session_name):
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
    if level == 100:
        return 5.0 if score >= 70 else 4.0 if score >= 60 else 3.0 if score >= 50 else 2.0 if score >= 45 else 1.0 if score >= 40 else 0.0
    return 4.0 if score >= 70 else 3.0 if score >= 60 else 2.0 if score >= 50 else 1.0 if score >= 45 else 0.0

def get_letter_grade(score):
    return 'A' if score >= 70 else 'B' if score >= 60 else 'C' if score >= 50 else 'D' if score >= 45 else 'E' if score >= 40 else 'F'

# =========================================================
# --- USER CLASS ---
# =========================================================
class User(UserMixin):
    def __init__(self, id, username, level, name, department, role, is_active=True, matric_number=None):
        self.id = id
        self.username = username
        self.level = level
        self.name = name
        self.department = department
        self.role = role
        self.matric_number = matric_number
        self._is_active = is_active if role == 'student' else True

    def get_id(self):
        return f"{self.role}:{self.id}"

    @property
    def is_active(self):
        return bool(self._is_active)

    @property
    def is_authenticated(self):
        return True

@login_manager.user_loader
def load_user(user_key):
    try:
        role, user_id = user_key.split(":", 1)
    except ValueError:
        return None

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if role == 'student':
                    cur.execute("SELECT * FROM students WHERE id = %s", (user_id,))
                    student = cur.fetchone()
                    if student:
                        return User(
                            id=student['id'],
                            username=student.get('matric_number'),
                            level=student.get('level', 100),
                            name=student.get('name', 'Unknown'),
                            department=student.get('department'),
                            role='student',
                            is_active=student.get('is_active', True),
                            matric_number=student.get('matric_number')
                        )
                elif role in ['admin', 'super_admin', 'hod', 'exam_officer']:
                    cur.execute("SELECT * FROM admins WHERE id = %s", (user_id,))
                    admin = cur.fetchone()
                    if admin:
                        return User(
                            id=admin['id'],
                            username=admin.get('username'),
                            level=None,
                            name=admin.get('name', 'Admin'),
                            department=None,
                            role=admin.get('role', 'exam_officer'),
                            is_active=admin.get('is_active', True)
                        )
    except Exception as e:
        app.logger.error("load_user error: %s", e)
    return None

# =========================================================
# --- MAIN WEBSITE ROUTES ---
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
    return render_template('payment.html')

@app.route('/academic_program')
def academic_program():
    return render_template('academic_program.html')

# --- Contact, payment, result portal, login, register routes ---
# The rest of your routes remain unchanged in logic
# Only psycopg2 calls replaced with psycopg, using `with get_db_connection() as conn:`
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
        contact_submission = Contact(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(contact_submission)
        db.session.commit()
        
        # Create and send email
        msg = Message(
            subject=f"[AGRIC DEPT] {subject}",
            recipients=[os.environ.get('CONTACT_EMAIL', 'agric.dept@ui.edu.ng')],
            body=f"""
            New message from department website:
            
            Name: {name}
            Email: {email}
            Subject: {subject}
            
            Message:
            {message}
            
            Submission ID: {contact_submission.id}
            Submitted: {contact_submission.created_at}
            """
        )
        
        mail.send(msg)
        flash('Thank you for your message! We will get back to you soon.', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error processing contact form: {str(e)}")
        flash('Sorry, there was an error sending your message. Please try again later.', 'error')
    
    return redirect(url_for('index') + '#contact')

@app.route('/submit-payment', methods=['POST'])
def submit_payment():
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
        existing_payment = Payment.query.filter_by(matric_number=matric_number).first()
        if existing_payment:
            return jsonify({'success': False, 'error': 'Payment already exists for this matric number'})
        
        # Save payment to database (SQLAlchemy)
        payment = Payment(
            full_name=full_name,
            matric_number=matric_number,
            level=level,
            email=email,
            phone_number=phone_number,
            payment_items=payment_items,
            total_amount=total_amount,
            transaction_ref=transaction_ref,
            payment_date=payment_date,
            receipt_filename=receipt_filename
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Send confirmation email
        try:
            items_list = json.loads(payment_items or '[]')
            items_text = '\n'.join([f"- {item['name']}: ₦{item['amount']:,}" for item in items_list])
            
            msg = Message(
                subject="Payment Submission Confirmation - Agricultural Engineering Dept",
                recipients=[email] if email else [],
                body=f"""
                Dear {full_name},
                
                Your payment submission has been received successfully.
                
                Payment Details:
                Matric Number: {matric_number}
                Level: {level}L
                Total Amount: ₦{total_amount:,}
                Reference: {transaction_ref or 'N/A'}
                Submission ID: {payment.id}
                
                Items Paid For:
                {items_text}
                
                Your payment is currently under review. You will be notified once it's approved.
                
                Best regards,
                Agricultural and Environmental Engineering Department
                University of Ibadan
                """
            )
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Error sending confirmation email: {str(e)}")
        
        return jsonify({
            'success': True, 
            'message': 'Payment information submitted successfully!',
            'payment_id': payment.id
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error processing payment: {str(e)}")
        return jsonify({'success': False, 'error': 'Error processing payment. Please try again.'})

# =========================================================
# --- RESULT PORTAL ROUTES (preserve all provided handlers) ---
# =========================================================
@app.before_request
def check_student_active():
    # Skip login, register, index, static
    if request.endpoint in ['login', 'register', 'index1', 'static']:
        return

    # Skip admin routes entirely for any admin-like role
    if current_user.is_authenticated and getattr(current_user, 'role', None) in ['admin', 'super_admin', 'hod', 'exam_officer']:
        return

    # Check student account active status
    if current_user.is_authenticated and getattr(current_user, 'role', None) == 'student':
        if not current_user.is_active:
            logout_user()
            flash('Your account has been deactivated. Please contact the department.', 'error')
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(
            'student_dashboard' if current_user.role == 'student' else 'admin_dashboard1'
        ))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor(row_factory=dict_row)

            # Student login
            cur.execute("SELECT * FROM students WHERE matric_number = %s", (identifier,))
            student = cur.fetchone()
            if student and check_password_hash(student.get('password_hash', ''), password):
                if not student.get('is_active', True):
                    flash('Your account is inactive. Contact department.', 'error')
                    return render_template('login.html')

                user = User(
                    id=student['id'],
                    username=student['matric_number'],
                    level=student.get('level'),
                    name=student.get('name'),
                    department=student.get('department', None),
                    role="student",
                    is_active=student.get('is_active', True),
                    matric_number=student['matric_number']
                )

                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('student_dashboard'))

            # Admin login
            cur.execute("SELECT * FROM admins WHERE username = %s", (identifier,))
            admin = cur.fetchone()
            if admin and check_password_hash(admin.get('password_hash', ''), password):
                user = User(
                    id=admin['id'],
                    username=admin.get('username'),
                    level=None,
                    name=admin.get('name'),
                    department=None,
                    role=admin.get('role', 'exam_officer'),
                    is_active=admin.get('is_active', True)
                )

                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin_dashboard1'))

            flash('Invalid login credentials', 'error')
        except Exception as e:
            flash('Error during login. Check server logs.', 'error')
            app.logger.error("Login error: %s", e)
        finally:
            if conn:
                conn.close()

    return render_template('login.html')

from psycopg import sql
from psycopg.rows import dict_row

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        matric_number = request.form.get('matric_number', '').strip()
        try:
            level = int(request.form.get('level', '100'))
        except ValueError:
            level = 100
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        if not validate_matric_number(matric_number):
            flash('Invalid matric number format. Provide a 6-digit matric number.', 'error')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO students (name, matric_number, level, email, phone, password_hash, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, matric_number, level, email, phone, password_hash, False))
                conn.commit()
            flash('Registration successful! Pending approval.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            if conn:
                conn.rollback()
            flash('Registration failed. Matric number may already exist.', 'error')
            print("Register error:", e)
        finally:
            if conn:
                conn.close()
    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/student/dashboard')
@roles_required('student')
def student_dashboard():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT r.*, s.session_name FROM results r
                JOIN sessions s ON r.session_id = s.id
                WHERE r.student_id = %s
                ORDER BY s.session_name DESC, r.semester DESC
            """, (current_user.id,))
            results = cur.fetchall()

        total_points, total_units = 0, 0
        results_list = []
        for result in results:
            result_dict = dict(result)
            student_level = get_student_level_for_session(current_user.matric_number, result['session_name'])
            gp = calculate_grade_points(result['score'], student_level)
            result_dict['correct_grade_point'] = gp
            result_dict['level_at_time'] = student_level
            total_points += gp * result['course_unit']
            total_units += result['course_unit']
            results_list.append(result_dict)

        cgpa = round(total_points / total_units, 2) if total_units > 0 else 0.00
        return render_template('student_dashboard.html',
                               results=results_list,
                               cgpa=cgpa,
                               student_name=current_user.name,
                               matric_number=current_user.username,
                               level=current_user.level)
    except Exception as e:
        flash('Error loading dashboard', 'error')
        print("Student dashboard error:", e)
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()


@app.route('/admin/dashboard')
@roles_required('super_admin', 'hod', 'exam_officer', 'admin')
def admin_dashboard():
    if current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM students")
            total_students = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM students WHERE is_active = true")
            active_students = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM students WHERE is_active = false")
            pending_students = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM results")
            total_results = cur.fetchone()['cnt']
        return render_template('admin_dashboard.html',
                               total_students=total_students,
                               active_students=active_students,
                               pending_students=pending_students,
                               total_results=total_results)
    except Exception as e:
        flash('Error loading admin dashboard', 'error')
        print("Admin dashboard error:", e)
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()


@app.route('/admin/add-admin', methods=['POST'])
@login_required
def add_admin():
    if current_user.role not in ['super_admin', 'hod']:
        flash("You don't have permission to add admins.", "error")
        return redirect(url_for('admin_dashboard'))

    name = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip()
    role = request.form.get('role', 'exam_officer').strip()
    password = request.form.get('password', '')

    if not name or not username or not role or not password:
        flash("All fields are required.", "error")
        return redirect(url_for('admin_dashboard'))

    password_hash = generate_password_hash(password)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO admins (name, username, role, password_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (name, username, role, password_hash))
            conn.commit()
        flash("New admin created successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash("Error creating admin. Username may already exist.", "error")
        print("Add Admin Error:", e)
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route("/api/students")
@login_required
def get_students():
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, matric_number, name, level, email, phone, is_active, created_at
                FROM students
                ORDER BY created_at DESC
            """)
            students = cur.fetchall()
            return jsonify(students)
    finally:
        conn.close()


@app.route('/api/admins')
@login_required
def api_admins():
    if current_user.role not in ['hod', 'super_admin']:
        return jsonify([])
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT id, name, username, role, created_at FROM admins")
            rows = cur.fetchall()
        admins = [
            {"id": r["id"], "name": r["name"], "username": r["username"], "role": r["role"], "created_at": r["created_at"].isoformat()}
            for r in rows
        ]
        return jsonify(admins)
    finally:
        conn.close()


@app.route("/admin/toggle-student-status", methods=["POST"])
@login_required
def toggle_student_status():
    data = request.get_json()
    student_id = data.get("id")
    new_status = data.get("is_active")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE students
                SET is_active = %s
                WHERE id = %s
            """, (new_status, student_id))
            conn.commit()
        return jsonify({"success": True, "message": "Student status updated"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/sessions", methods=["GET"])
@login_required
@roles_required("super_admin", "hod", "exam_officer")
def get_sessions():
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT id, session_name, is_current FROM sessions ORDER BY id DESC")
            sessions = cur.fetchall()
            return jsonify(sessions)
    finally:
        conn.close()


@app.route("/admin/add-result", methods=["POST"])
@login_required
@roles_required("super_admin", "hod", "exam_officer")
def add_result():
    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()

    try:
        student_id = int(data.get("student_id"))
        course_code = data.get("course_code", "").strip()
        course_title = data.get("course_title", "").strip()
        course_unit = int(data.get("course_unit", 0))
        score = float(data.get("score", 0))
        semester = data.get("semester", "").strip()
        session_id = int(data.get("session_id"))
    except Exception as e:
        return jsonify({"error": f"Invalid input data: {str(e)}"}), 400

    if score >= 70:
        grade, grade_point = "A", 5.0
    elif score >= 60:
        grade, grade_point = "B", 4.0
    elif score >= 50:
        grade, grade_point = "C", 3.0
    elif score >= 45:
        grade, grade_point = "D", 2.0
    elif score >= 40:
        grade, grade_point = "E", 1.0
    else:
        grade, grade_point = "F", 0.0

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO results (
                    student_id, course_code, course_title, course_unit, score,
                    grade, grade_point, semester, session_id, uploaded_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                student_id, course_code, course_title, course_unit, score,
                grade, grade_point, semester, session_id, current_user.id
            ))
            conn.commit()
        return jsonify({"message": "Result added successfully"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/admin/analytics')
@login_required
@roles_required('super_admin', 'hod', 'exam_officer')
def admin_analytics():
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT level, COUNT(*) AS total FROM students GROUP BY level ORDER BY level")
            students_per_level = cursor.fetchall()

            cursor.execute("""
                WITH student_avg AS (
                    SELECT student_id, AVG(score) AS avg_score
                    FROM results
                    GROUP BY student_id
                )
                SELECT 
                    CASE 
                        WHEN avg_score >= 70 THEN 'First Class/Distinction'
                        WHEN avg_score >= 60 THEN 'Second Class Upper'
                        WHEN avg_score >= 50 THEN 'Second Class Lower'
                        WHEN avg_score >= 45 THEN 'Third Class'
                        ELSE 'Pass/Fail'
                    END AS class,
                    COUNT(*) AS total
                FROM student_avg
                GROUP BY class
                ORDER BY class
            """)
            performance_distribution = cursor.fetchall()
        return jsonify({
            "students_per_level": students_per_level,
            "performance_distribution": performance_distribution
        })
    finally:
        conn.close()







# =========================================================
# --- DEFAULT ADMIN + SEEDERS ---
# =========================================================
def create_default_super_admin():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM admins")
                row = cur.fetchone()
                if row['cnt'] == 0:
                    default_username = os.environ.get('DEFAULT_ADMIN_USER', 'admin')
                    default_password = os.environ.get('DEFAULT_ADMIN_PASS', 'admin123')
                    password_hash = generate_password_hash(default_password)
                    cur.execute("""
                        INSERT INTO admins (username, name, role, password_hash)
                        VALUES (%s, %s, %s, %s)
                    """, (default_username, "Super Admin", "super_admin", password_hash))
                    conn.commit()
                    print(f"✅ Default super admin created: username='{default_username}', password='{default_password}'")
    except Exception as e:
        print("⚠️ Error creating default super admin (table may not exist yet):", e)

def seed_default_session_and_courses():
    sample_courses = [
        ('AGE 101', 'Introduction to Agricultural Engineering', 2, 100, 1),
        ('AGE 102', 'Engineering Drawing and Design', 3, 100, 1),
        ('AGE 103', 'Mathematics for Engineers I', 3, 100, 1),
        ('AGE 104', 'Physics for Engineers', 3, 100, 1),
        ('AGE 105', 'Chemistry for Engineers', 3, 100, 1),
        ('AGE 111', 'Workshop Technology', 2, 100, 2),
        ('AGE 112', 'Mathematics for Engineers II', 3, 100, 2),
        ('AGE 113', 'Engineering Mechanics', 3, 100, 2),
        ('AGE 201', 'Fluid Mechanics', 3, 200, 1),
        ('AGE 202', 'Strength of Materials', 3, 200, 1),
        ('AGE 203', 'Thermodynamics', 3, 200, 1),
        ('AGE 301', 'Farm Power and Machinery', 3, 300, 1),
        ('AGE 302', 'Soil and Water Engineering', 3, 300, 1),
        ('AGE 401', 'Agricultural Processing Engineering', 3, 400, 1),
        ('AGE 501', 'Project', 6, 500, 1)
    ]
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM sessions")
                if cur.fetchone()['cnt'] == 0:
                    cur.execute("INSERT INTO sessions (session_name, is_current) VALUES (%s, %s)", ('2024/2025', True))
                    conn.commit()
                    print("✅ Default session 2024/2025 created")

                cur.execute("SELECT COUNT(*) AS cnt FROM courses")
                if cur.fetchone()['cnt'] == 0:
                    for course in sample_courses:
                        cur.execute("""
                            INSERT INTO courses (course_code, course_title, course_unit, level, semester)
                            VALUES (%s, %s, %s, %s, %s)
                        """, course)
                    conn.commit()
                    print("✅ Sample courses inserted")
    except Exception as e:
        print("⚠️ Error seeding sessions/courses:", e)

# =========================================================
# --- STARTUP ---
# =========================================================
with app.app_context():
    db.create_all()
create_default_super_admin()
seed_default_session_and_courses()

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)

# ------------------- Robust DB Initialization & Seeding -------------------
def init_db(app):
    """
    Ensures all tables exist and default records are seeded.
    Should be called once at app startup.
    """
    with app.app_context():
        # 1️⃣ Create all tables if they don't exist
        try:
            db.create_all()
            print("✅ All tables ensured.")
        except Exception as e:
            print("❌ Error creating tables:", e)
            raise

        # 2️⃣ Seed default admin
        if not Admin.query.filter_by(username="admin").first():
            admin = Admin(
                name="System Administrator",
                username="admin",
                role="super_admin",
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created (username=admin, password=admin123)")

        # 3️⃣ Seed default session
        if not Session.query.filter_by(session_name="2024/2025").first():
            session = Session(session_name="2024/2025", is_current=True)
            db.session.add(session)
            db.session.commit()
            print("✅ Default session 2024/2025 created")

        # 4️⃣ Seed sample courses (if table empty)
        if Course.query.count() == 0:
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
                db.session.add(
                    Course(
                        course_code=code,
                        course_title=title,
                        course_unit=unit,
                        level=level,
                        semester=semester,
                    )
                )
            db.session.commit()
            print("✅ Sample courses inserted")

        print("✅ DB initialization & seeding completed.")


# ------------------- Usage -------------------
# Place this at the bottom of your main app.py or entry script
if __name__ == "__main__":
    init_db(app)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
