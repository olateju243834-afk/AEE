from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Contact {self.name} - {self.subject}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    matric_number = db.Column(db.String(20), nullable=False, index=True)
    level = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    payment_items = db.Column(db.Text, nullable=False)  # JSON string of selected items
    total_amount = db.Column(db.Float, nullable=False)
    transaction_ref = db.Column(db.String(100))
    payment_date = db.Column(db.Date)
    receipt_filename = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.matric_number} - ₦{self.total_amount}>'
