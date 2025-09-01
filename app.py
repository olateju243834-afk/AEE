import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify,session
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from models import db, Contact, Payment
import re

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
ALLOWED_LEVELS = {100, 200, 300, 400, 500}
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}



# --------------------------------------------------------
# Configure logging
# --------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)

# --------------------------------------------------------
# Initialize app
# --------------------------------------------------------
app = Flask(__name__)
if not os.environ.get("SESSION_SECRET"):
    raise RuntimeError("SESSION_SECRET environment variable must be set")
app.secret_key = os.environ["SESSION_SECRET"]


# --------------------------------------------------------
# Database configuration (PostgreSQL instead of SQLite)
# --------------------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "postgresql+psycopg://aeedb_user:pbZRHWCMGvkRMMtzYyIMEBqVJdprYPrp@dpg-d2m57uv5r7bs73ebqv40-a/aeedb"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
#app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"



# --------------------------------------------------------
# Mail configuration
# --------------------------------------------------------
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# --------------------------------------------------------
# File upload configuration
# --------------------------------------------------------
app.config['UPLOAD_FOLDER'] = 'uploads/receipts'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# --------------------------------------------------------
# Allowed file types for upload
# --------------------------------------------------------
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --------------------------------------------------------
# Initialize extensions
# --------------------------------------------------------
db.init_app(app)
mail = Mail(app)

# --------------------------------------------------------
# Create upload directory
# --------------------------------------------------------
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --------------------------------------------------------
# Routes
# --------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def stats():
    stats = (
        db.session.query(
            db.func.to_char(Payment.created_at, 'YYYY-MM'),
            db.func.count(Payment.id).label('count'),
            db.func.sum(Payment.total_amount).label('total')
        )
        .group_by('month')
        .order_by('month')
        .all()
    )

    data = {
        "labels": [row.month for row in stats],
        "counts": [row.count for row in stats],
        "totals": [float(row.total or 0) for row in stats],
    }

    return jsonify(data)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.environ.get('ADMIN_PASSWORD'):
            session['is_admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid password', 'error')
    return render_template('admin_login.html')


@app.route('/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    payments = Payment.query.all()
    return render_template('admin_dashboard.html', payments=payments)


    payments = Payment.query.all()
    return render_template('admin_dashboard.html', payments=payments)


@app.route('/uploads/receipts/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



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
def academic_program ():
    return render_template('academic_program.html')


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
        
        # Save payment to database
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


# --------------------------------------------------------
# Initialize database
# --------------------------------------------------------
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
