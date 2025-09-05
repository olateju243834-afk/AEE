
import os
import logging
import json
import functools
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session, send_file
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Contact, Payment
import calendar
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
app.secret_key = 'some_super_secret_key_12345'
#if not os.environ.get("SESSION_SECRET"):
#    raise RuntimeError("SESSION_SECRET environment variable must be set")
#app.secret_key = os.environ["SESSION_SECRET"]

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
# Admin credentials and decorator
# --------------------------------------------------------
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------------
# Template filters
# --------------------------------------------------------
@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convert newlines to HTML br tags"""
    if text:
        return text.replace('\n', '<br>\n')
    return text

# --------------------------------------------------------
# Create upload directory
# --------------------------------------------------------
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --------------------------------------------------------
# Public Routes
# --------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/news1')
def news1():
    return render_template('news1.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

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
# Admin Routes
# --------------------------------------------------------
@app.route('/admin')
@app.route('/admin-access')
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        session['admin_logged_in'] = True
        session['admin_username'] = username
        flash('Login successful!', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid credentials!', 'error')
        return redirect(url_for('admin_login'))

@app.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/dashboard')
@admin_required
def admin_dashboard():
    # Get statistics
    total_contacts = Contact.query.count()
    total_payments = Payment.query.count()
    pending_payments = Payment.query.filter_by(status='pending').count()
    approved_payments = Payment.query.filter_by(status='approved').count()
    
    # Recent submissions
    recent_contacts = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html', 
                         total_contacts=total_contacts,
                         total_payments=total_payments,
                         pending_payments=pending_payments,
                         approved_payments=approved_payments,
                         recent_contacts=recent_contacts,
                         recent_payments=recent_payments)

@app.route('/contacts')
@admin_required
def admin_contacts():
    page = request.args.get('page', 1, type=int)
    contacts = Contact.query.order_by(Contact.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin_contacts.html', contacts=contacts)

@app.route('/contacts/<int:contact_id>')
@admin_required
def admin_view_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return render_template('admin_contact_detail.html', contact=contact)

@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
@admin_required
def admin_delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('admin_contacts'))

@app.route('/payments')
@admin_required
def admin_payments():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Payment.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin_payments.html', payments=payments, status_filter=status_filter)

@app.route('/payments/<int:payment_id>')
@admin_required
def admin_view_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    try:
        payment_items = json.loads(payment.payment_items) if payment.payment_items else []
    except:
        payment_items = []
    return render_template('admin_payment_detail.html', payment=payment, payment_items=payment_items)

@app.route('/payments/<int:payment_id>/update_status', methods=['POST'])
@admin_required
def admin_update_payment_status(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'approved', 'rejected']:
        payment.status = new_status
        payment.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Payment status updated to {new_status}!', 'success')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('admin_view_payment', payment_id=payment_id))

@app.route('/payments/<int:payment_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    if request.method == 'POST':
        payment.full_name = request.form.get('full_name')
        payment.matric_number = request.form.get('matric_number')
        payment.level = int(request.form.get('level', 0))
        payment.email = request.form.get('email')
        payment.phone_number = request.form.get('phone_number')
        payment.total_amount = float(request.form.get('total_amount', 0))
        payment.transaction_ref = request.form.get('transaction_ref')
        payment.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Payment updated successfully!', 'success')
        return redirect(url_for('admin_view_payment', payment_id=payment_id))
    
    return render_template('admin_edit_payment.html', payment=payment)

@app.route('/payments/<int:payment_id>/delete', methods=['POST'])
@admin_required
def admin_delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # Delete associated receipt file if exists
    if payment.receipt_filename:
        receipt_path = os.path.join('uploads/receipts', payment.receipt_filename)
        if os.path.exists(receipt_path):
            os.remove(receipt_path)
    
    db.session.delete(payment)
    db.session.commit()
    flash('Payment deleted successfully!', 'success')
    return redirect(url_for('admin_payments'))

@app.route('/receipts/<filename>')
@admin_required
def admin_view_receipt(filename):
    receipt_path = os.path.join('uploads/receipts', filename)
    if os.path.exists(receipt_path):
        return send_file(receipt_path)
    else:
        flash('Receipt file not found!', 'error')
        return redirect(url_for('admin_payments'))

@app.route('/export/contacts')
@admin_required
def admin_export_contacts():
    contacts = Contact.query.all()
    
    # Create CSV content
    csv_content = "ID,Name,Email,Subject,Message,Created At\n"
    for contact in contacts:
        csv_content += f'"{contact.id}","{contact.name}","{contact.email}","{contact.subject}","{contact.message.replace(chr(34), chr(34)+chr(34))}","{contact.created_at}"\n'
    
    # Save to file
    filename = f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/export/payments')
@admin_required
def admin_export_payments():
    payments = Payment.query.all()
    
    # Create CSV content
    csv_content = "ID,Full Name,Matric Number,Level,Email,Phone,Total Amount,Status,Transaction Ref,Created At\n"
    for payment in payments:
        csv_content += f'"{payment.id}","{payment.full_name}","{payment.matric_number}","{payment.level}","{payment.email}","{payment.phone_number}","{payment.total_amount}","{payment.status}","{payment.transaction_ref or ""}","{payment.created_at}"\n'
    
    # Save to file
    filename = f"payments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/admin/stats')
@admin_required
def admin_stats():
    # Payment statistics by level
    level_stats = db.session.query(
        Payment.level,
        db.func.count(Payment.id),
        db.func.sum(Payment.total_amount)
    ).group_by(Payment.level).all()

    # Payment statistics by status
    status_stats = db.session.query(
        Payment.status,
        db.func.count(Payment.id),
        db.func.sum(Payment.total_amount)
    ).group_by(Payment.status).all()

    # Monthly payment trends (SQLite-safe)
month_expr = db.func.to_char(Payment.created_at, 'YYYY-MM').label('month')
monthly_stats_raw = db.session.query(
    month_expr,
    db.func.count(Payment.id).label('count'),
    db.func.sum(Payment.total_amount).label('total')
).group_by(month_expr).order_by(month_expr).all()


    # Format months for display
import calendar
monthly_stats = []
for row in monthly_stats_raw:
        if row[0]:
            year, month = map(int, row[0].split('-'))
            label = f"{calendar.month_name[month]} {year}"  # e.g., August 2025
        else:
            label = "Unknown"
        monthly_stats.append((label, row[1], row[2]))

    return render_template(
        'admin_stats.html',
        level_stats=level_stats,
        status_stats=status_stats,
        monthly_stats=monthly_stats
    )



# --------------------------------------------------------
# Initialize database
# --------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
