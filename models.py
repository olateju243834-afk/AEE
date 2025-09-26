from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------- DB -------------------
db = SQLAlchemy()

# ------------------- Main Website Models -------------------
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Contact {self.name} - {self.subject}>"

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
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Payment {self.matric_number} - ₦{self.total_amount}>"

# ------------------- Result Portal Models -------------------
class Student(db.Model):
    __tablename__ = "students"  # force table name to match queries
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    matric_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    level = db.Column(db.Integer, nullable=False)  # 100,200,300...
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship("Result", backref="student", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(20), nullable=False
    )  # exam_officer, hod, super_admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(20), unique=True, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship("Result", backref="session", lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_title = db.Column(db.String(200), nullable=False)
    course_unit = db.Column(db.Integer, nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 100,200,...
    semester = db.Column(db.Integer, nullable=False)  # 1 or 2
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    course_code = db.Column(db.String(20), nullable=False)
    course_title = db.Column(db.String(200), nullable=False)
    course_unit = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(2), nullable=False)
    grade_point = db.Column(db.Numeric(3, 2), nullable=False)
    semester = db.Column(db.Integer, nullable=False)  # 1 or 2
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"))
    uploaded_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------- Seeder Function -------------------
def seed_defaults(app):
    """Create tables and insert default records if missing."""
    with app.app_context():
        db.create_all()

        # Default Admin
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

        # Default Session
        if not Session.query.filter_by(session_name="2024/2025").first():
            session = Session(session_name="2024/2025", is_current=True)
            db.session.add(session)
            db.session.commit()
            print("✅ Default session 2024/2025 created")

        # Sample Courses
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
