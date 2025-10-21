
import os
import functools
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Contact, Payment
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin credentials (in production, use environment variables)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('admin', 'admin123'))

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_contacts = Contact.query.count()
    total_payments = Payment.query.count()
    pending_payments = Payment.query.filter_by(status='pending').count()
    approved_payments = Payment.query.filter_by(status='approved').count()
    
    # Recent submissions
    recent_contacts = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('admin/admin_dashboard.html', 
                         total_contacts=total_contacts,
                         total_payments=total_payments,
                         pending_payments=pending_payments,
                         approved_payments=approved_payments,
                         recent_contacts=recent_contacts,
                         recent_payments=recent_payments)

@admin_bp.route('/contacts')
@login_required
def contacts():
    page = request.args.get('page', 1, type=int)
    contacts = Contact.query.order_by(Contact.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/admin_contacts.html', contacts=contacts)

@admin_bp.route('/contacts/<int:contact_id>')
@login_required
def view_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return render_template('admin/admin_contact_detail.html', contact=contact)

@admin_bp.route('/contacts/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('admin.contacts'))

@admin_bp.route('/payments')
@login_required
def payments():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Payment.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/admin_payments.html', payments=payments, status_filter=status_filter)

@admin_bp.route('/payments/<int:payment_id>')
@login_required
def view_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    try:
        payment_items = json.loads(payment.payment_items) if payment.payment_items else []
    except:
        payment_items = []
    return render_template('admin/admin_payment_detail.html', payment=payment, payment_items=payment_items)

@admin_bp.route('/payments/<int:payment_id>/update_status', methods=['POST'])
@login_required
def update_payment_status(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'approved', 'rejected']:
        payment.status = new_status
        payment.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Payment status updated to {new_status}!', 'success')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('admin.view_payment', payment_id=payment_id))

@admin_bp.route('/payments/<int:payment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_payment(payment_id):
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
        return redirect(url_for('admin.view_payment', payment_id=payment_id))
    
    return render_template('admin/admin_edit_payment.html', payment=payment)

@admin_bp.route('/payments/<int:payment_id>/delete', methods=['POST'])
@login_required
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # Delete associated receipt file if exists
    if payment.receipt_filename:
        receipt_path = os.path.join('uploads/receipts', payment.receipt_filename)
        if os.path.exists(receipt_path):
            os.remove(receipt_path)
    
    db.session.delete(payment)
    db.session.commit()
    flash('Payment deleted successfully!', 'success')
    return redirect(url_for('admin.payments'))

@admin_bp.route('/receipts/<filename>')
@login_required
def view_receipt(filename):
    receipt_path = os.path.join('uploads/receipts', filename)
    if os.path.exists(receipt_path):
        return send_file(receipt_path)
    else:
        flash('Receipt file not found!', 'error')
        return redirect(url_for('admin.payments'))

@admin_bp.route('/export/contacts')
@login_required
def export_contacts():
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

@admin_bp.route('/export/payments')
@login_required
def export_payments():
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

@admin_bp.route('/stats')
@login_required
def stats():
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

    # Detect which database we're using
    engine_name = db.engine.name  # 'postgresql', 'sqlite', etc.

    # Monthly payment trends
    if engine_name == 'sqlite':
        month_expr = db.func.strftime('%Y-%m', Payment.created_at)
    else:
        month_expr = db.func.to_char(Payment.created_at, 'YYYY-MM')

    monthly_stats = db.session.query(
        month_expr.label('month'),
        db.func.count(Payment.id).label('count'),
        db.func.sum(Payment.total_amount).label('total')
    ).group_by('month').order_by('month').all()

    return render_template(
        'admin_stats.html',
        level_stats=level_stats,
        status_stats=status_stats,
        monthly_stats=monthly_stats
    )

